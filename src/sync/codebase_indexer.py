"""Codebase indexing functionality for the sync service with specialized logic."""
import os
import logging
from typing import Dict, Any, Optional, List
import marqo

from .universal_indexer import UniversalIndexer
from .config import SyncConfig

logger = logging.getLogger(__name__)

class CodebaseIndexer:
    """Specialized indexer for source code repositories."""
    
    def __init__(self, marqo_client: marqo.Client, config: SyncConfig):
        self.current_project_id = None
        self.current_project_path = None
        
        def metadata_enhancer(metadata: Dict[str, Any], file_path: str) -> Dict[str, Any]:
            if self.current_project_id:
                metadata['project_id'] = self.current_project_id
                metadata['index_type'] = 'codebase'
            return metadata
        
        self.universal_indexer = UniversalIndexer(marqo_client, config, metadata_enhancer=metadata_enhancer)
        self.marqo_client = marqo_client
        self.config = config
        self.file_hashes = self.universal_indexer.file_hashes
        self.hash_file = self.universal_indexer.hash_file
    
    def set_project_context(self, project_id: str, project_path: str, index_name: str = None) -> None:
        self.current_project_id = project_id
        self.current_project_path = project_path
        if index_name:
            self.config.index_name = index_name
            self.universal_indexer.config.index_name = index_name
        logger.info(f"Set codebase project context: {project_id} -> {project_path} (index: {self.config.index_name})")
    
    async def index_file(self, file_path: str) -> None:
        await self.universal_indexer.index_file(file_path)
    
    async def index_directory(self, directory: str) -> None:
        """Recursively index all files in a directory - delegates to UniversalIndexer."""
        # Simply delegate to UniversalIndexer for testing
        await self.universal_indexer.index_directory(directory)
    
    # Delegate all other methods to UniversalIndexer
    def _load_hashes(self):
        return self.universal_indexer._load_hashes()
    
    def _save_hashes(self):
        return self.universal_indexer._save_hashes()
    
    def _get_file_hash(self, file_path: str):
        return self.universal_indexer._get_file_hash(file_path)
    
    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        return self.universal_indexer._get_file_metadata(file_path)
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        return self.universal_indexer._read_file_content(file_path)
    
    def _sanitize_content(self, content: str, file_path: str) -> Optional[str]:
        return self.universal_indexer._sanitize_content(content, file_path)
    
    def _validate_file_for_indexing(self, file_path: str) -> bool:
        return self.universal_indexer._validate_file_for_indexing(file_path)
    
    def _update_file_hash(self, file_path: str) -> None:
        return self.universal_indexer._update_file_hash(file_path)
    
    def _should_skip_file(self, file_path: str) -> bool:
        return self.universal_indexer._should_skip_file(file_path)

# Re-export functions from marqo_handlers for backward compatibility
from .marqo_handlers import ensure_index_exists, check_marqo_compatibility
