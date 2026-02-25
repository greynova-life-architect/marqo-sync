"""Chat history indexing functionality for the sync service with specialized logic."""
import os
import logging
from typing import Dict, Any, Optional, List
import marqo

from .universal_indexer import UniversalIndexer
from .config import SyncConfig

logger = logging.getLogger(__name__)

class ChatHistoryIndexer:
    """Specialized indexer for chat history and conversation content."""
    
    def __init__(self, marqo_client: marqo.Client, config: SyncConfig):
        self.current_conversation_type = None
        self.current_conversation_path = None
        self.conversation_types = getattr(config, 'conversation_types', ['all', 'chatgpt', 'claude', 'gemini'])
        self.max_conversation_length = getattr(config, 'max_conversation_length', 10000)
        self.include_timestamps = getattr(config, 'include_timestamps', True)
        
        def metadata_enhancer(metadata: Dict[str, Any], file_path: str) -> Dict[str, Any]:
            if self.current_conversation_type:
                metadata['conversation_type'] = self.current_conversation_type
                metadata['index_type'] = 'conversations'
            return metadata
        
        self.universal_indexer = UniversalIndexer(marqo_client, config, metadata_enhancer=metadata_enhancer)
        self.marqo_client = marqo_client
        self.config = config
        self.file_hashes = self.universal_indexer.file_hashes
        self.hash_file = self.universal_indexer.hash_file
    
    def set_conversation_context(self, conversation_type: str, conversation_path: str, index_name: str = None) -> None:
        self.current_conversation_type = conversation_type
        self.current_conversation_path = conversation_path
        if index_name:
            self.config.index_name = index_name
            self.universal_indexer.config.index_name = index_name
        logger.info(f"Set conversation context: {conversation_type} -> {conversation_path} (index: {self.config.index_name})")
    
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
