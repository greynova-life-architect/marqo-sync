"""Enhanced configuration management for multiple indexer types."""
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional, Any
import os
import json
import logging
from pathlib import Path
from .env_config import env_config

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class IndexerTypeConfig:
    """Configuration for a specific indexer type."""
    index_name: str
    source_dir: str
    indexer_type: str = "generic"
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """Validate type-specific configuration."""
        # For unified indexers, source_dir may be empty as it's set per project/type
        if self.source_dir and not os.path.exists(self.source_dir):
            raise ValueError(f"Source directory does not exist for {self.indexer_type}: {self.source_dir}")
            
        # Convert source_dir to absolute path if it's not empty
        if self.source_dir:
            self.source_dir = os.path.abspath(self.source_dir)

@dataclass
class CodebaseConfig(IndexerTypeConfig):
    """Configuration specific to codebase indexers."""
    index_name: str
    source_dir: str
    indexer_type: str = "code"
    
    def __post_init__(self):
        """Set default settings for codebase indexer."""
        if "skip_extensions" not in self.settings:
            self.settings["skip_extensions"] = {
                # Binary and compiled files
                '.exe', '.dll', '.pdb', '.bin', '.obj', 
                '.pyc', '.pyo', '.pyd', '.so', '.dylib',
                # Media files
                '.jpg', '.jpeg', '.png', '.gif', '.ico',
                '.mp3', '.mp4', '.wav', '.avi', '.mov',
                # Package and archive files
                '.zip', '.tar', '.gz', '.rar', '.7z',
                # Cache and IDE files
                '.cache', '.log', '.tmp', '.swp',
                # Other binary formats
                '.pdf', '.doc', '.docx', '.xls', '.xlsx'
            }
            
        if "skip_directories" not in self.settings:
            # Default skip directories that typically contain build artifacts or cache
            default_skip_dirs = {
                'compiled', 'bin', 'obj', 'build', 'dist',
                'node_modules', '__pycache__', '.git',
                '.idea', '.vscode', '.vs', 'venv',
                'Debug', 'Release', 'x64', 'x86'
            }
            self.settings["skip_directories"] = default_skip_dirs

@dataclass
class CodexConfig(IndexerTypeConfig):
    """Configuration specific to codex (folder structure) indexers."""
    index_name: str
    source_dir: str
    indexer_type: str = "codex"
    
    def __post_init__(self):
        """Set default settings for codex indexer."""
        if "skip_directories" not in self.settings:
            # Default skip directories that typically contain build artifacts or cache
            default_skip_dirs = {
                'compiled', 'bin', 'obj', 'build', 'dist',
                'node_modules', '__pycache__', '.git',
                '.idea', '.vscode', '.vs', 'venv',
                'Debug', 'Release', 'x64', 'x86'
            }
            self.settings["skip_directories"] = default_skip_dirs
            
        if "max_depth" not in self.settings:
            # Default maximum folder depth to index
            self.settings["max_depth"] = 10

@dataclass
class ConversationConfig(IndexerTypeConfig):
    """Configuration specific to conversation indexers."""
    index_name: str
    source_dir: str
    indexer_type: str = "conversation"
    conversation_type: str = "all"  # Can be "all", "chatgpt", "claude"
    
    def __post_init__(self):
        """Set default settings for conversation indexer."""
        if "file_patterns" not in self.settings:
            self.settings["file_patterns"] = ["*.json", "*.md", "*.txt"]

@dataclass
class EnhancedSyncConfig:
    """Enhanced configuration supporting multiple indexer types."""
    marqo_url: str
    indexers: List[IndexerTypeConfig] = field(default_factory=list)
    max_file_size_bytes: int = 1024 * 1024  # Default 1MB
    store_large_files_metadata_only: bool = True
    
    @classmethod
    def from_file(cls, config_path: str) -> 'EnhancedSyncConfig':
        config_path_obj = Path(config_path)
        if not config_path_obj.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path_obj, 'r') as f:
            if config_path_obj.suffix in ['.yaml', '.yml']:
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML is required for YAML configuration files")
                config_data = yaml.safe_load(f)
            elif config_path_obj.suffix == '.json':
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path_obj.suffix}")
        
        config = cls(
            marqo_url=config_data.get('marqo_url', env_config.get_marqo_url()),
            max_file_size_bytes=config_data.get('max_file_size_bytes', env_config.get_sync_max_file_size()),
            store_large_files_metadata_only=config_data.get('store_large_files_metadata_only', env_config.get_sync_store_large_files_meta())
        )
        
        for idx_config in config_data.get('indexers', []):
            idx_type = idx_config.get('indexer_type', 'code')
            index_name = idx_config.get('index_name')
            source_dir = idx_config.get('source_dir', '')
            settings = idx_config.get('settings', {})
            
            if idx_type == 'code':
                codebase_projects = settings.get('projects', [])
                if codebase_projects:
                    codebase_config = CodebaseConfig(
                        indexer_type='code',
                        index_name=index_name,
                        source_dir='',
                        settings={'projects': codebase_projects}
                    )
                    config.indexers.append(codebase_config)
            elif idx_type == 'codex':
                codex_projects = settings.get('projects', [])
                if codex_projects:
                    codex_config = CodexConfig(
                        indexer_type='codex',
                        index_name=index_name,
                        source_dir='',
                        settings={'projects': codex_projects}
                    )
                    config.indexers.append(codex_config)
            elif idx_type in ['chathistory', 'conversation']:
                conversation_types = settings.get('conversation_types', [])
                if conversation_types:
                    conv_config = ConversationConfig(
                        indexer_type='chathistory',
                        index_name=index_name,
                        source_dir='',
                        conversation_type='all',
                        settings={'conversation_types': conversation_types}
                    )
                    config.indexers.append(conv_config)
            else:
                indexer_config = IndexerTypeConfig(
                    indexer_type=idx_type,
                    index_name=index_name,
                    source_dir=source_dir,
                    settings=settings
                )
                config.indexers.append(indexer_config)
        
        return config
    
    @classmethod
    def from_env(cls) -> 'EnhancedSyncConfig':
        config_file = env_config.get_sync_config_file()
        if config_file:
            logger.info(f"Loading configuration from file: {config_file}")
            return cls.from_file(config_file)
        
        logger.info(f"Key environment variables:")
        logger.info(f"  MARQO_URL: {env_config.get_marqo_url()}")
        logger.info(f"  SYNC_CODEBASES: {env_config.get_sync_codebases() or 'NOT_SET'}")
        logger.info(f"  SYNC_CODEX: {env_config.get_sync_codex() or 'NOT_SET'}")
        logger.info(f"  SYNC_CONVERSATIONS: {env_config.get_sync_conversations() or 'NOT_SET'}")
        
        config = cls(
            marqo_url=env_config.get_marqo_url(),
            max_file_size_bytes=env_config.get_sync_max_file_size(),
            store_large_files_metadata_only=env_config.get_sync_store_large_files_meta()
        )
        
        config._add_codex_indexers()
        config._add_codebase_indexers()
        config._add_conversation_indexers()
        
        if not config.indexers:
            logger.warning("No indexers configured, adding legacy default indexer")
            config._add_legacy_default_indexer()
        
        return config
    
    def _add_codex_indexers(self) -> None:
        """Add unified codex indexer from environment variables."""
        codex_str = env_config.get_sync_codex()
        if not codex_str:
            return
            
        try:
            # Parse the name:path pairs
            # Format: "name1:path1,name2:path2"
            pairs = codex_str.split(',')
            codex_projects = []
            
            for pair in pairs:
                if ':' not in pair:
                    logger.warning(f"Invalid codex format (missing ':'): {pair}")
                    continue
                    
                name, path = pair.split(':', 1)
                name = name.strip()
                path = path.strip()
                
                if not name or not path:
                    logger.warning(f"Invalid codex pair (empty name or path): {pair}")
                    continue
                
                codex_projects.append((name, path))
                logger.info(f"Added codex project: {name} -> {path}")
            
            if codex_projects:
                # Create single unified codex config with all projects
                codex_config = CodexConfig(
                    indexer_type="codex",
                    index_name="codex",  # Unified index name
                    source_dir="",  # Will be set per project during indexing
                    settings={"projects": codex_projects}  # Store project info
                )
                
                self.indexers.append(codex_config)
                logger.info(f"Added unified codex indexer with {len(codex_projects)} projects")
                
        except Exception as e:
            logger.error(f"Error parsing SYNC_CODEX: {e}")
    
    def _add_codebase_indexers(self) -> None:
        """Add unified codebase indexer from environment variables."""
        codebases_str = env_config.get_sync_codebases()
        if not codebases_str:
            return
            
        try:
            # Parse the name:path pairs
            # Format: "name1:path1,name2:path2"
            pairs = codebases_str.split(',')
            codebase_projects = []
            
            for pair in pairs:
                if ':' not in pair:
                    logger.warning(f"Invalid codebase format (missing ':'): {pair}")
                    continue
                    
                name, path = pair.split(':', 1)
                name = name.strip()
                path = path.strip()
                
                if not name or not path:
                    logger.warning(f"Invalid codebase pair (empty name or path): {pair}")
                    continue
                
                codebase_projects.append((name, path))
                logger.info(f"Added codebase project: {name} -> {path}")
            
            if codebase_projects:
                # Create single unified codebase config with all projects
                codebase_config = CodebaseConfig(
                    indexer_type="code",
                    index_name="codebase",  # Unified index name
                    source_dir="",  # Will be set per project during indexing
                    settings={"projects": codebase_projects}  # Store project info
                )
                
                self.indexers.append(codebase_config)
                logger.info(f"Added unified codebase indexer with {len(codebase_projects)} projects")
                
        except Exception as e:
            logger.error(f"Error parsing SYNC_CODEBASES: {e}")
    
    def _add_conversation_indexers(self) -> None:
        """Add unified conversation indexer from environment variables."""
        conversations_str = env_config.get_sync_conversations()
        if not conversations_str:
            return
            
        try:
            # Parse the type:path pairs
            # Format: "chatgpt:path1,claude:path2"
            pairs = conversations_str.split(',')
            conversation_types = []
            
            for pair in pairs:
                if ':' not in pair:
                    logger.warning(f"Invalid conversation format (missing ':'): {pair}")
                    continue
                    
                conv_type, path = pair.split(':', 1)
                conv_type = conv_type.strip().lower()
                path = path.strip()
                
                if not conv_type or not path:
                    logger.warning(f"Invalid conversation pair (empty type or path): {pair}")
                    continue
                
                if conv_type not in ["chatgpt", "claude", "all"]:
                    logger.warning(f"Unknown conversation type: {conv_type}, using 'all'")
                    conv_type = "all"
                
                conversation_types.append((conv_type, path))
                logger.info(f"Added conversation type: {conv_type} -> {path}")
            
            if conversation_types:
                # Create single unified conversation config with all types
                conversation_config = ConversationConfig(
                    indexer_type="chathistory",
                    index_name="conversations",  # Unified index name
                    source_dir="",  # Will be set per type during indexing
                    conversation_type="all",  # Default type
                    settings={"conversation_types": conversation_types}  # Store type info
                )
                
                self.indexers.append(conversation_config)
                logger.info(f"Added unified conversation indexer with {len(conversation_types)} types")
                
        except Exception as e:
            logger.error(f"Error parsing SYNC_CONVERSATIONS: {e}")
    
    def _add_legacy_default_indexer(self) -> None:
        """Add legacy default indexer for backward compatibility."""
        source_dir = env_config.get_sync_source_dir()
        index_name = env_config.get_sync_index_name()
        
        default_skip_dirs = {
            'compiled', 'bin', 'obj', 'build', 'dist',
            'node_modules', '__pycache__', '.git',
            '.idea', '.vscode', '.vs', 'venv',
            'Debug', 'Release', 'x64', 'x86'
        }
        
        settings = {
            "skip_extensions": {
                '.exe', '.dll', '.pdb', '.bin', '.obj', 
                '.pyc', '.pyo', '.pyd', '.so', '.dylib',
                '.jpg', '.jpeg', '.png', '.gif', '.ico',
                '.mp3', '.mp4', '.wav', '.avi', '.mov',
                '.zip', '.tar', '.gz', '.rar', '.7z',
                '.cache', '.log', '.tmp', '.swp',
                '.pdf', '.doc', '.docx', '.xls', '.xlsx'
            },
            "skip_directories": env_config.get_sync_skip_dirs(default_skip_dirs)
        }
        
        # Create default indexer config
        default_config = IndexerTypeConfig(
            indexer_type="code",  # Default to code indexer
            index_name=index_name,
            source_dir=source_dir,
            settings=settings
        )
        
        self.indexers.append(default_config)
        logger.info(f"Added legacy default indexer: {index_name} -> {source_dir}")
    
    def validate(self) -> None:
        """Validate all configuration settings."""
        if not self.indexers:
            raise ValueError("No indexers configured")
            
        for indexer_config in self.indexers:
            try:
                indexer_config.validate()
                
                # Additional validation for unified indexers
                if not indexer_config.source_dir:  # Unified indexer
                    if 'projects' in indexer_config.settings:
                        # Validate codebase/codex project directories
                        for project_name, project_path in indexer_config.settings['projects']:
                            if not os.path.exists(project_path):
                                logger.warning(f"Project directory does not exist: {project_name} -> {project_path}")
                    elif 'conversation_types' in indexer_config.settings:
                        # Validate conversation type directories
                        for conv_type, conv_path in indexer_config.settings['conversation_types']:
                            if not os.path.exists(conv_path):
                                logger.warning(f"Conversation directory does not exist: {conv_type} -> {conv_path}")
                                
            except Exception as e:
                logger.error(f"Validation error for indexer {indexer_config.index_name}: {e}")
                # Don't raise, just log the error
    
    def get_indexer_configs(self, indexer_type: Optional[str] = None) -> List[IndexerTypeConfig]:
        """Get all indexer configurations of a specific type.
        
        Args:
            indexer_type: Type of indexers to get, or None for all
            
        Returns:
            List of indexer configurations
        """
        if indexer_type is None:
            return self.indexers
            
        return [cfg for cfg in self.indexers if cfg.indexer_type == indexer_type]
        
    def to_legacy_config(self, index_name: str):
        """Convert to legacy SyncConfig for backward compatibility.
        
        Args:
            index_name: Name of the index to convert
            
        Returns:
            Legacy SyncConfig instance
            
        Raises:
            ValueError: If index_name not found
        """
        # Import here to avoid circular imports
        from .config import SyncConfig
        # Return type is SyncConfig, but we use string annotation in method signature to avoid circular imports
        
        # Find the indexer config with matching index_name
        for indexer_config in self.indexers:
            if indexer_config.index_name == index_name:
                # Extract settings
                skip_extensions = indexer_config.settings.get("skip_extensions", set())
                skip_directories = indexer_config.settings.get("skip_directories", set())
                
                # Create legacy config
                return SyncConfig(
                    source_dir=indexer_config.source_dir,
                    marqo_url=self.marqo_url,
                    index_name=index_name,
                    skip_extensions=skip_extensions,
                    skip_directories=skip_directories,
                    max_file_size_bytes=self.max_file_size_bytes,
                    store_large_files_metadata_only=self.store_large_files_metadata_only
                )
                
        raise ValueError(f"No indexer found with index_name: {index_name}")