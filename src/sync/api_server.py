import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import marqo
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import json

from .indexer_config import EnhancedSyncConfig
from .config import SyncConfig
from .marqo_handlers import check_marqo_compatibility, ensure_specialized_index
from .profile_manager import ProfileManager, UserProfile, AgentProfile, OrganizationProfile, ProfileType
from .conversation_manager import ConversationManager, ConversationMetadata, ConversationMessage, ConversationStatus
from .memory_manager import MemoryManager, Memory, MemoryType
from .category_manager import CategoryManager, Category
from .document_model import DocumentMetadata, DocumentType, create_document
from .env_config import env_config

logger = logging.getLogger(__name__)

app = FastAPI(title="Marqo Sync API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PathValidationRequest(BaseModel):
    path: str

class PathValidationResponse(BaseModel):
    valid: bool
    exists: bool
    is_directory: bool
    readable: bool
    error: Optional[str] = None

class MarqoConnectionRequest(BaseModel):
    url: str

class ConfigUpdateRequest(BaseModel):
    marqo_url: Optional[str] = None
    codebases: Optional[List[Dict[str, str]]] = None
    codex: Optional[List[Dict[str, str]]] = None
    conversations: Optional[List[Dict[str, str]]] = None
    max_file_size_bytes: Optional[int] = None
    store_large_files_metadata_only: Optional[bool] = None
    health_check_port: Optional[int] = None

class ServiceState:
    def __init__(self):
        self.marqo_client: Optional[marqo.Client] = None
        self.config: Optional[EnhancedSyncConfig] = None
        self.indexers: Dict[str, Any] = {}
        self.watchers: Dict[str, Any] = {}
        self.status: str = "stopped"

service_state = ServiceState()

def get_marqo_client(url: str) -> marqo.Client:
    try:
        client = marqo.Client(url=url)
        check_marqo_compatibility(client)
        return client
    except Exception as e:
        logger.error(f"Failed to create Marqo client: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to connect to Marqo: {str(e)}")

@app.get("/api/status")
async def get_status():
    return {
        "status": service_state.status,
        "indexers": {
            name: {
                "type": type(idx).__name__,
                "index_name": idx.config.index_name if hasattr(idx, 'config') else None
            }
            for name, idx in service_state.indexers.items()
        },
        "watchers": {
            name: {
                "root_dir": watcher.root_dir if hasattr(watcher, 'root_dir') else None,
                "watching": watcher.watching if hasattr(watcher, 'watching') else False
            }
            for name, watcher in service_state.watchers.items()
        }
    }

@app.get("/api/config")
async def get_config():
    try:
        if service_state.config:
            config_dict = {
                "marqo_url": service_state.config.marqo_url,
                "max_file_size_bytes": service_state.config.max_file_size_bytes,
                "store_large_files_metadata_only": service_state.config.store_large_files_metadata_only,
                "indexers": []
            }
            
            for idx_config in service_state.config.indexers:
                idx_dict = {
                    "indexer_type": idx_config.indexer_type,
                    "index_name": idx_config.index_name,
                    "source_dir": idx_config.source_dir,
                    "enabled": idx_config.enabled,
                    "settings": idx_config.settings
                }
                config_dict["indexers"].append(idx_dict)
            
            return config_dict
        else:
            config = EnhancedSyncConfig.from_env()
            service_state.config = config
            return await get_config()
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def update_config(request: ConfigUpdateRequest):
    try:
        config = EnhancedSyncConfig.from_env()
        
        if request.marqo_url:
            config.marqo_url = request.marqo_url
        
        if request.max_file_size_bytes:
            config.max_file_size_bytes = request.max_file_size_bytes
        
        if request.store_large_files_metadata_only is not None:
            config.store_large_files_metadata_only = request.store_large_files_metadata_only
        
        if request.codebases:
            codebase_configs = [cfg for cfg in config.indexers if cfg.indexer_type == "code"]
            if codebase_configs:
                codebase_config = codebase_configs[0]
            else:
                from .indexer_config import CodebaseConfig
                codebase_config = CodebaseConfig(
                    indexer_type="code",
                    index_name="codebase",
                    source_dir="",
                    settings={}
                )
                config.indexers.append(codebase_config)
            projects = [(item["name"], item["path"]) for item in request.codebases]
            codebase_config.settings["projects"] = projects
        
        if request.codex:
            codex_configs = [cfg for cfg in config.indexers if cfg.indexer_type == "codex"]
            if codex_configs:
                codex_config = codex_configs[0]
            else:
                from .indexer_config import CodexConfig
                codex_config = CodexConfig(
                    indexer_type="codex",
                    index_name="codex",
                    source_dir="",
                    settings={}
                )
                config.indexers.append(codex_config)
            projects = [(item["name"], item["path"]) for item in request.codex]
            codex_config.settings["projects"] = projects
        
        if request.conversations:
            conv_configs = [cfg for cfg in config.indexers if cfg.indexer_type == "chathistory"]
            if conv_configs:
                conv_config = conv_configs[0]
            else:
                from .indexer_config import ConversationConfig
                conv_config = ConversationConfig(
                    indexer_type="chathistory",
                    index_name="conversations",
                    source_dir="",
                    conversation_type="all",
                    settings={}
                )
                config.indexers.append(conv_config)
            conv_types = [(item["type"], item["path"]) for item in request.conversations]
            conv_config.settings["conversation_types"] = conv_types
        
        config_file = env_config.get_sync_config_file() or env_config.get_default_config_file()
        save_config_to_file(config, config_file)
        
        service_state.config = config
        return {"success": True, "message": "Configuration updated"}
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def save_config_to_file(config: EnhancedSyncConfig, file_path: str):
    try:
        import yaml
        config_dict = {
            "marqo_url": config.marqo_url,
            "max_file_size_bytes": config.max_file_size_bytes,
            "store_large_files_metadata_only": config.store_large_files_metadata_only,
            "indexers": []
        }
        
        for idx_config in config.indexers:
            settings = {}
            for key, value in idx_config.settings.items():
                if isinstance(value, list):
                    settings[key] = [list(item) if isinstance(item, tuple) else item for item in value]
                else:
                    settings[key] = value
            
            idx_dict = {
                "indexer_type": idx_config.indexer_type,
                "index_name": idx_config.index_name,
                "source_dir": idx_config.source_dir,
                "enabled": idx_config.enabled,
                "settings": settings
            }
            config_dict["indexers"].append(idx_dict)
        
        with open(file_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
    except Exception as e:
        logger.error(f"Error saving config to file: {e}")
        raise

@app.get("/api/indexes")
async def get_indexes():
    try:
        if not service_state.marqo_client:
            config = EnhancedSyncConfig.from_env()
            service_state.marqo_client = get_marqo_client(config.marqo_url)
        
        client = service_state.marqo_client
        indexes = []
        index_names = []
        
        try:
            # Try multiple methods to get index list
            # Method 1: Try list_indexes() if available
            if hasattr(client, 'list_indexes'):
                try:
                    result = client.list_indexes()
                    if isinstance(result, dict):
                        index_names = result.get('results', [])
                    elif isinstance(result, list):
                        index_names = result
                    logger.info(f"Got {len(index_names)} indexes from list_indexes()")
                except Exception as e:
                    logger.warning(f"list_indexes() failed: {e}")
            
            # Method 2: Try get_stats() to extract index names
            if not index_names:
                try:
                    stats = client.get_stats()
                    if isinstance(stats, dict):
                        if 'indexes' in stats:
                            index_names = list(stats['indexes'].keys())
                        elif 'results' in stats:
                            index_names = stats['results']
                    logger.info(f"Got {len(index_names)} indexes from get_stats()")
                except Exception as e:
                    logger.warning(f"Could not get index list from stats: {e}")
            
            # Method 3: Try to get index names from index() method
            if not index_names:
                try:
                    # Try to get all indexes by attempting to access them
                    # This is a fallback method
                    all_stats = client.get_stats()
                    if isinstance(all_stats, dict) and 'indexes' in all_stats:
                        index_names = list(all_stats['indexes'].keys())
                except Exception as e:
                    logger.debug(f"Could not extract index names from stats: {e}")
            
            # Method 4: Try HTTP API directly
            if not index_names:
                try:
                    import requests
                    # Get marqo_url from config or service_state
                    marqo_url = None
                    if 'config' in locals() and hasattr(config, 'marqo_url'):
                        marqo_url = config.marqo_url
                    elif service_state.config and hasattr(service_state.config, 'marqo_url'):
                        marqo_url = service_state.config.marqo_url
                    elif hasattr(client, 'url'):
                        marqo_url = client.url
                    
                    if marqo_url:
                        # Remove trailing slash
                        marqo_url = marqo_url.rstrip('/')
                        response = requests.get(f"{marqo_url}/indexes", timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, dict):
                                index_names = data.get('results', [])
                            elif isinstance(data, list):
                                index_names = data
                            logger.info(f"Got {len(index_names)} indexes from HTTP API")
                except Exception as e:
                    logger.debug(f"HTTP API method failed: {e}")
            
            # Method 5: Fallback to known indexes
            if not index_names:
                logger.info("No indexes found via API methods, checking known indexes")
                known_indexes = ['codebase', 'codex', 'conversations', 'profiles', 'memories', 'categories', 'conversation_messages']
                for idx_name in known_indexes:
                    try:
                        client.get_index(idx_name)
                        index_names.append(idx_name)
                        logger.debug(f"Found known index: {idx_name}")
                    except Exception as e:
                        logger.debug(f"Known index {idx_name} does not exist: {e}")
                        pass
            
            logger.info(f"Processing {len(index_names)} indexes")
            
            # Process each index
            for index_name in index_names:
                try:
                    index_info = {}
                    stats = {}
                    
                    # Get index info
                    try:
                        index_info = client.get_index(index_name)
                        if not isinstance(index_info, dict):
                            index_info = {}
                    except Exception as e:
                        logger.debug(f"Could not get index info for {index_name}: {e}")
                    
                    # Get index stats
                    try:
                        index_obj = client.index(index_name)
                        if hasattr(index_obj, 'get_stats'):
                            stats = index_obj.get_stats()
                        elif hasattr(client, 'get_stats'):
                            all_stats = client.get_stats()
                            if isinstance(all_stats, dict) and 'indexes' in all_stats:
                                stats = all_stats['indexes'].get(index_name, {})
                    except Exception as e:
                        logger.debug(f"Could not get stats for {index_name}: {e}")
                    
                    # Extract document count
                    doc_count = 0
                    if isinstance(stats, dict):
                        doc_count = stats.get('numberOfDocuments', stats.get('number_of_documents', stats.get('document_count', 0)))
                    elif hasattr(stats, 'numberOfDocuments'):
                        doc_count = stats.numberOfDocuments
                    elif hasattr(stats, 'number_of_documents'):
                        doc_count = stats.number_of_documents
                    
                    # Extract size
                    size = 0
                    if isinstance(stats, dict):
                        size = stats.get('indexSize', stats.get('index_size', stats.get('size', 0)))
                    elif hasattr(stats, 'indexSize'):
                        size = stats.indexSize
                    elif hasattr(stats, 'index_size'):
                        size = stats.index_size
                    
                    indexes.append({
                        "name": index_name,
                        "type": _determine_index_type(index_name),
                        "document_count": doc_count,
                        "size": size,
                        "settings": index_info.get('settings', {}) if isinstance(index_info, dict) else {}
                    })
                    logger.debug(f"Added index: {index_name} with {doc_count} documents")
                except Exception as e:
                    logger.warning(f"Error getting info for index {index_name}: {e}")
                    indexes.append({
                        "name": index_name,
                        "type": _determine_index_type(index_name),
                        "document_count": 0,
                        "size": 0,
                        "error": str(e)
                    })
            
            logger.info(f"Returning {len(indexes)} indexes")
        except Exception as e:
            logger.error(f"Error listing indexes: {e}", exc_info=True)
            # Don't raise here, return empty list with error info
            return {"indexes": [], "error": str(e)}
        
        return {"indexes": indexes}
    except Exception as e:
        logger.error(f"Error getting indexes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def _determine_index_type(index_name: str) -> str:
    index_name_lower = index_name.lower()
    # Check for project-specific codebase indexes (e.g., "codebase-project1", "codebase-myapp")
    if index_name_lower.startswith("codebase-") or (index_name_lower.startswith("codebase") and "-" in index_name_lower):
        return "codebase"
    elif index_name == "codebase" or "codebase" in index_name_lower:
        return "codebase"
    # Check for project-specific codex indexes
    elif index_name_lower.startswith("codex-") or (index_name_lower.startswith("codex") and "-" in index_name_lower):
        return "codex"
    elif index_name == "codex" or "codex" in index_name_lower:
        return "codex"
    # Check for conversation-specific indexes (e.g., "conversations-chatgpt", "conversations-claude")
    elif index_name_lower.startswith("conversations-") or index_name_lower.startswith("conversation-"):
        return "conversations"
    elif index_name == "conversations" or (index_name == "conversation_messages"):
        return "conversations"
    elif index_name == "profiles" or "profile" in index_name_lower:
        return "profiles"
    elif index_name == "memories" or "memory" in index_name_lower:
        return "memories"
    elif index_name == "categories" or "category" in index_name_lower:
        return "categories"
    return "unknown"

def _extract_project_name(index_name: str) -> str:
    """Extract project/conversation name from index name."""
    if "-" in index_name:
        parts = index_name.split("-", 1)
        if len(parts) > 1:
            return parts[1]
    return index_name

@app.get("/api/indexers")
async def get_indexers():
    try:
        if not service_state.config:
            config = EnhancedSyncConfig.from_env()
            service_state.config = config
        
        indexers_list = []
        for indexer_config in service_state.config.indexers:
            indexers_list.append({
                "indexer_type": indexer_config.indexer_type,
                "index_name": indexer_config.index_name,
                "enabled": indexer_config.enabled,
                "settings": indexer_config.settings
            })
        
        return {"indexers": indexers_list}
    except Exception as e:
        logger.error(f"Error getting indexers: {e}")
        return {"indexers": []}

@app.get("/api/watchers")
async def get_watchers():
    watchers_list = []
    for name, watcher in service_state.watchers.items():
        watchers_list.append({
            "name": name,
            "root_dir": watcher.root_dir if hasattr(watcher, 'root_dir') else None,
            "watching": watcher.watching if hasattr(watcher, 'watching') else False
        })
    return {"watchers": watchers_list}

@app.post("/api/validate-path")
async def validate_path(request: PathValidationRequest):
    path = Path(request.path)
    
    response = {
        "valid": False,
        "exists": False,
        "is_directory": False,
        "readable": False,
        "error": None
    }
    
    try:
        if path.exists():
            response["exists"] = True
            if path.is_dir():
                response["is_directory"] = True
                if os.access(path, os.R_OK):
                    response["readable"] = True
                    response["valid"] = True
                else:
                    response["error"] = "Directory exists but is not readable"
            else:
                response["error"] = "Path exists but is not a directory"
        else:
            response["error"] = "Path does not exist"
    except Exception as e:
        response["error"] = str(e)
    
    return response

@app.post("/api/test-connection")
async def test_connection(request: MarqoConnectionRequest):
    try:
        client = get_marqo_client(request.url)
        
        index_count = 0
        try:
            if hasattr(client, 'list_indexes'):
                indexes = client.list_indexes()
                index_count = len(indexes.get('results', []))
            else:
                try:
                    stats = client.get_stats()
                    if isinstance(stats, dict) and 'indexes' in stats:
                        index_count = len(stats['indexes'])
                except:
                    pass
        except:
            pass
        
        return {
            "success": True,
            "message": "Connection successful",
            "index_count": index_count
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.get("/api/index-stats/{index_name}")
async def get_index_stats(index_name: str):
    try:
        if not service_state.marqo_client:
            config = EnhancedSyncConfig.from_env()
            service_state.marqo_client = get_marqo_client(config.marqo_url)
        
        client = service_state.marqo_client
        stats = {}
        
        try:
            if hasattr(client.index(index_name), 'get_stats'):
                stats = client.index(index_name).get_stats()
            else:
                search_result = client.index(index_name).search("", limit=1)
                stats = {
                    "numberOfDocuments": search_result.get('total', 0) if isinstance(search_result, dict) else 0
                }
        except Exception as e:
            logger.warning(f"Error getting stats for {index_name}: {e}")
            stats = {"error": str(e)}
        
        return {"index_name": index_name, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting index stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integration/search")
async def search_index(index_name: str, query: str, limit: int = 10):
    try:
        if not service_state.marqo_client:
            config = EnhancedSyncConfig.from_env()
            service_state.marqo_client = get_marqo_client(config.marqo_url)
        
        client = service_state.marqo_client
        results = client.index(index_name).search(query, limit=limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integration/index-info")
async def get_index_info_for_integration(index_name: str):
    try:
        if not service_state.marqo_client:
            config = EnhancedSyncConfig.from_env()
            service_state.marqo_client = get_marqo_client(config.marqo_url)
        
        client = service_state.marqo_client
        index_info = client.get_index(index_name)
        
        try:
            stats = client.index(index_name).get_stats() if hasattr(client.index(index_name), 'get_stats') else {}
        except:
            stats = {}
        
        return {
            "name": index_name,
            "type": _determine_index_type(index_name),
            "document_count": stats.get('numberOfDocuments', 0) if isinstance(stats, dict) else 0,
            "settings": index_info.get('settings', {}) if isinstance(index_info, dict) else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integration/health")
async def integration_health():
    return {
        "status": "healthy",
        "service": "marqo-sync",
        "version": "1.0.0"
    }

class ProfileRequest(BaseModel):
    profile_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    tenant_id: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class AgentProfileRequest(BaseModel):
    profile_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    capabilities: Optional[List[str]] = None
    model_config: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None

class ConversationRequest(BaseModel):
    conversation_id: Optional[str] = None
    thread_id: Optional[str] = None
    tenant_id: Optional[str] = None
    topic: Optional[str] = None
    category: Optional[str] = None
    participants: Optional[Dict[str, List[str]]] = None

class MessageRequest(BaseModel):
    conversation_id: str
    thread_id: str
    role: str
    content: str
    turn_number: int

class MemoryRequest(BaseModel):
    memory_id: Optional[str] = None
    memory_type: str
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    content: str
    importance_score: float = 0.5
    tags: Optional[List[str]] = None

class CategoryRequest(BaseModel):
    category_id: str
    name: str
    description: Optional[str] = None
    parent_category_id: Optional[str] = None
    tenant_id: Optional[str] = None

def get_profile_manager():
    if not service_state.marqo_client:
        config = EnhancedSyncConfig.from_env()
        service_state.marqo_client = get_marqo_client(config.marqo_url)
    ensure_specialized_index(service_state.marqo_client, "profiles")
    return ProfileManager(service_state.marqo_client)

def get_conversation_manager():
    if not service_state.marqo_client:
        config = EnhancedSyncConfig.from_env()
        service_state.marqo_client = get_marqo_client(config.marqo_url)
    ensure_specialized_index(service_state.marqo_client, "conversations")
    ensure_specialized_index(service_state.marqo_client, "conversation_messages")
    return ConversationManager(service_state.marqo_client)

def get_memory_manager():
    if not service_state.marqo_client:
        config = EnhancedSyncConfig.from_env()
        service_state.marqo_client = get_marqo_client(config.marqo_url)
    ensure_specialized_index(service_state.marqo_client, "memories")
    return MemoryManager(service_state.marqo_client)

def get_category_manager():
    if not service_state.marqo_client:
        config = EnhancedSyncConfig.from_env()
        service_state.marqo_client = get_marqo_client(config.marqo_url)
    ensure_specialized_index(service_state.marqo_client, "categories")
    return CategoryManager(service_state.marqo_client)

@app.post("/api/profiles")
async def create_profile(request: ProfileRequest):
    try:
        manager = get_profile_manager()
        profile = UserProfile(
            profile_id=request.profile_id,
            name=request.name,
            email=request.email,
            tenant_id=request.tenant_id,
            preferences=request.preferences or {}
        )
        success = manager.create_user_profile(profile)
        if success:
            return {"success": True, "profile_id": request.profile_id}
        raise HTTPException(status_code=500, detail="Failed to create profile")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    try:
        manager = get_profile_manager()
        profile = manager.get_profile(profile_id)
        if profile:
            return profile
        raise HTTPException(status_code=404, detail="Profile not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/profiles/{profile_id}")
async def update_profile(profile_id: str, updates: Dict[str, Any]):
    try:
        manager = get_profile_manager()
        success = manager.update_profile(profile_id, updates)
        if success:
            return {"success": True}
        raise HTTPException(status_code=500, detail="Failed to update profile")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles")
async def list_profiles(tenant_id: Optional[str] = None, profile_type: Optional[str] = None, query: str = ""):
    try:
        manager = get_profile_manager()
        profiles = manager.search_profiles(query, tenant_id, profile_type)
        return {"profiles": profiles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents")
async def create_agent(request: AgentProfileRequest):
    try:
        manager = get_profile_manager()
        profile = AgentProfile(
            profile_id=request.profile_id,
            name=request.name,
            description=request.description,
            tenant_id=request.tenant_id,
            capabilities=request.capabilities or [],
            model_config=request.model_config or {},
            memory_config=request.memory_config or {}
        )
        success = manager.create_agent_profile(profile)
        if success:
            return {"success": True, "profile_id": request.profile_id}
        raise HTTPException(status_code=500, detail="Failed to create agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations")
async def create_conversation(request: ConversationRequest):
    try:
        import uuid
        manager = get_conversation_manager()
        
        conv_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:12]}"
        
        metadata = ConversationMetadata(
            conversation_id=conv_id,
            thread_id=thread_id,
            tenant_id=request.tenant_id,
            topic=request.topic,
            category=request.category,
            participants=request.participants or {}
        )
        success = manager.create_conversation(metadata)
        if success:
            return {"success": True, "conversation_id": conv_id, "thread_id": thread_id}
        raise HTTPException(status_code=500, detail="Failed to create conversation")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    try:
        manager = get_conversation_manager()
        conversation = manager.get_conversation(conversation_id)
        if conversation:
            messages = manager.get_conversation_messages(conversation_id)
            conversation['messages'] = messages
            return conversation
        raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{conversation_id}/messages")
async def add_message(conversation_id: str, request: MessageRequest):
    try:
        import uuid
        manager = get_conversation_manager()
        
        message = ConversationMessage(
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            thread_id=request.thread_id,
            role=request.role,
            content=request.content,
            turn_number=request.turn_number
        )
        success = manager.add_message(message)
        if success:
            return {"success": True, "message_id": message.message_id}
        raise HTTPException(status_code=500, detail="Failed to add message")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations")
async def list_conversations(tenant_id: Optional[str] = None, status: Optional[str] = None, query: str = ""):
    try:
        manager = get_conversation_manager()
        conversations = manager.search_conversations(query, tenant_id, status)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{conversation_id}/archive")
async def archive_conversation(conversation_id: str):
    try:
        manager = get_conversation_manager()
        success = manager.archive_conversation(conversation_id)
        if success:
            return {"success": True}
        raise HTTPException(status_code=500, detail="Failed to archive conversation")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memories")
async def store_memory(request: MemoryRequest):
    try:
        import uuid
        manager = get_memory_manager()
        
        memory_id = request.memory_id or f"mem_{uuid.uuid4().hex[:12]}"
        memory = Memory(
            memory_id=memory_id,
            memory_type=MemoryType(request.memory_type),
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            user_id=request.user_id,
            content=request.content,
            importance_score=request.importance_score,
            tags=request.tags or []
        )
        success = manager.store_memory(memory)
        if success:
            return {"success": True, "memory_id": memory_id}
        raise HTTPException(status_code=500, detail="Failed to store memory")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories")
async def retrieve_memories(
    query: str,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    min_importance: float = 0.0,
    limit: int = 10
):
    try:
        manager = get_memory_manager()
        memories = manager.retrieve_memories(
            query, tenant_id, agent_id, user_id, memory_type, min_importance, limit
        )
        return {"memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories/{memory_id}")
async def get_memory(memory_id: str):
    try:
        manager = get_memory_manager()
        memory = manager.get_memory(memory_id)
        if memory:
            return memory
        raise HTTPException(status_code=404, detail="Memory not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/memories/{memory_id}")
async def update_memory(memory_id: str, updates: Dict[str, Any]):
    try:
        manager = get_memory_manager()
        success = manager.update_memory(memory_id, updates)
        if success:
            return {"success": True}
        raise HTTPException(status_code=500, detail="Failed to update memory")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: str):
    try:
        manager = get_memory_manager()
        success = manager.delete_memory(memory_id)
        if success:
            return {"success": True}
        raise HTTPException(status_code=500, detail="Failed to delete memory")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/categories")
async def create_category(request: CategoryRequest):
    try:
        manager = get_category_manager()
        category = Category(
            category_id=request.category_id,
            name=request.name,
            description=request.description,
            parent_category_id=request.parent_category_id,
            tenant_id=request.tenant_id
        )
        success = manager.create_category(category)
        if success:
            return {"success": True, "category_id": request.category_id}
        raise HTTPException(status_code=500, detail="Failed to create category")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
async def list_categories(tenant_id: Optional[str] = None, parent_id: Optional[str] = None):
    try:
        manager = get_category_manager()
        categories = manager.list_categories(tenant_id, parent_id)
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories/tree")
async def get_category_tree(tenant_id: Optional[str] = None):
    try:
        manager = get_category_manager()
        tree = manager.get_category_tree(tenant_id)
        return tree
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories/{category_id}")
async def get_category(category_id: str):
    try:
        manager = get_category_manager()
        category = manager.get_category(category_id)
        if category:
            return category
        raise HTTPException(status_code=404, detail="Category not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/categories/{category_id}")
async def update_category(category_id: str, updates: Dict[str, Any]):
    try:
        manager = get_category_manager()
        success = manager.update_category(category_id, updates)
        if success:
            return {"success": True}
        raise HTTPException(status_code=500, detail="Failed to update category")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/categories/{category_id}")
async def delete_category(category_id: str):
    try:
        manager = get_category_manager()
        success = manager.delete_category(category_id)
        if success:
            return {"success": True}
        raise HTTPException(status_code=500, detail="Failed to delete category")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def set_service_state(state: ServiceState):
    global service_state
    service_state = state

