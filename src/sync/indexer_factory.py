"""Factory for creating indexers based on configuration."""
import logging
from typing import Dict, Type
import marqo

from .abstract_indexer import AbstractIndexer
from .universal_indexer import UniversalIndexer
from .codex_indexer import CodexIndexer
from .codebase_indexer import CodebaseIndexer
from .chathistory_indexer import ChatHistoryIndexer
from .config import SyncConfig

logger = logging.getLogger(__name__)

class IndexerFactory:
    """Factory for creating indexers based on configuration."""
    
    # Registry of available indexer types
    _indexer_registry: Dict[str, Type[AbstractIndexer]] = {
        "code": CodebaseIndexer,      # Specialized codebase indexer
        "codex": CodexIndexer,        # Specialized codex indexer
        "chathistory": ChatHistoryIndexer,  # Chat history indexer
        "conversation": ChatHistoryIndexer, # Alias for chat history
        "universal": UniversalIndexer, # General-purpose fallback
    }
    
    @classmethod
    def register_indexer(cls, indexer_type: str, indexer_class: Type[AbstractIndexer]) -> None:
        """Register a new indexer type.
        
        Args:
            indexer_type: Type identifier for the indexer
            indexer_class: Class implementing the AbstractIndexer interface
        """
        cls._indexer_registry[indexer_type] = indexer_class
        logger.info(f"Registered indexer type: {indexer_type}")
    
    @classmethod
    def create_indexer(cls, 
                      indexer_type: str, 
                      marqo_client: marqo.Client, 
                      config: SyncConfig) -> AbstractIndexer:
        """Create an indexer of the specified type.
        
        Args:
            indexer_type: Type of indexer to create
            marqo_client: Marqo client instance
            config: Configuration for the indexer
            
        Returns:
            An instance of the requested indexer type
            
        Raises:
            ValueError: If the requested indexer type is not registered
        """
        if indexer_type not in cls._indexer_registry:
            available_types = ", ".join(cls._indexer_registry.keys())
            raise ValueError(
                f"Unknown indexer type: {indexer_type}. "
                f"Available types: {available_types}"
            )
        
        indexer_class = cls._indexer_registry[indexer_type]
        logger.info(f"Creating indexer of type: {indexer_type}")
        return indexer_class(marqo_client, config)
    
    @classmethod
    def get_available_indexer_types(cls) -> list[str]:
        """Get a list of all registered indexer types.
        
        Returns:
            List of registered indexer type identifiers
        """
        return list(cls._indexer_registry.keys())
