"""Adapter for backward compatibility with legacy configuration."""
import logging
from typing import Dict, Any, Optional

from .config import SyncConfig
from .indexer_config import EnhancedSyncConfig, IndexerTypeConfig, CodebaseConfig, ConversationConfig

logger = logging.getLogger(__name__)

class ConfigAdapter:
    """Adapter for converting between legacy and enhanced configurations."""
    
    @staticmethod
    def legacy_to_enhanced(legacy_config: SyncConfig) -> EnhancedSyncConfig:
        """Convert legacy SyncConfig to EnhancedSyncConfig.
        
        Args:
            legacy_config: Legacy configuration
            
        Returns:
            Enhanced configuration with equivalent settings
        """
        # Create settings dict from legacy config
        settings = {
            "skip_extensions": legacy_config.skip_extensions,
            "skip_directories": legacy_config.skip_directories
        }
        
        # Create indexer config
        indexer_config = CodebaseConfig(
            indexer_type="code",
            index_name=legacy_config.index_name,
            source_dir=legacy_config.source_dir,
            settings=settings
        )
        
        # Create enhanced config
        enhanced_config = EnhancedSyncConfig(
            marqo_url=legacy_config.marqo_url,
            indexers=[indexer_config],
            max_file_size_bytes=legacy_config.max_file_size_bytes,
            store_large_files_metadata_only=legacy_config.store_large_files_metadata_only
        )
        
        return enhanced_config
    
    @staticmethod
    def enhanced_to_legacy(enhanced_config: EnhancedSyncConfig, index_name: Optional[str] = None) -> SyncConfig:
        """Convert EnhancedSyncConfig to legacy SyncConfig.
        
        Args:
            enhanced_config: Enhanced configuration
            index_name: Name of the index to use, or None for first available
            
        Returns:
            Legacy configuration with equivalent settings
            
        Raises:
            ValueError: If no suitable indexer found
        """
        if index_name:
            # Find indexer with matching name
            for indexer in enhanced_config.indexers:
                if indexer.index_name == index_name:
                    return enhanced_config.to_legacy_config(index_name)
            
            raise ValueError(f"No indexer found with name: {index_name}")
        
        # Use first available indexer
        if not enhanced_config.indexers:
            raise ValueError("No indexers configured")
            
        first_indexer = enhanced_config.indexers[0]
        return enhanced_config.to_legacy_config(first_indexer.index_name)
    
    @staticmethod
    def get_config_for_indexer_type(enhanced_config: EnhancedSyncConfig, indexer_type: str) -> Dict[str, SyncConfig]:
        """Get legacy configs for all indexers of a specific type.
        
        Args:
            enhanced_config: Enhanced configuration
            indexer_type: Type of indexer to get configs for
            
        Returns:
            Dictionary mapping index names to legacy configs
        """
        result = {}
        
        for indexer in enhanced_config.indexers:
            if indexer.indexer_type == indexer_type:
                try:
                    legacy_config = enhanced_config.to_legacy_config(indexer.index_name)
                    result[indexer.index_name] = legacy_config
                except Exception as e:
                    logger.error(f"Error converting config for {indexer.index_name}: {e}")
        
        return result
