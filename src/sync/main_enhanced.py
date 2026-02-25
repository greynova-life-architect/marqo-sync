"""Enhanced main entry point for the codebase sync service with multiple indexers."""
import os
import sys
import time
import logging
import marqo
import asyncio
from typing import Dict, List

from .indexer_config import EnhancedSyncConfig
from .indexer_factory import IndexerFactory
from .abstract_indexer import AbstractIndexer
from .watcher import FileWatcher
from .health_server import HealthServer
from .api_server import set_service_state, ServiceState
import platform
from .marqo_handlers import check_marqo_compatibility, ensure_index_exists
from .env_config import env_config

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging with proper encoding and fallback
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/sync_service.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    # Fallback to basic logging if there are issues
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

class EnhancedSyncService:
    """Enhanced sync service that manages multiple indexers."""
    
    def __init__(self):
        self.config = None
        self.marqo_client = None
        self.indexers: Dict[str, AbstractIndexer] = {}
        self.watchers: Dict[str, FileWatcher] = {}
        health_port = env_config.get_health_check_port()
        self.health_server = HealthServer(port=health_port)
        self.service_state = ServiceState()
        
    async def initialize(self):
        """Initialize the service, load configuration and create indexers."""
        try:
            # Load and validate configuration
            try:
                self.config = EnhancedSyncConfig.from_env()
                self.config.validate()
                
                # Log configuration for debugging
                logger.info(f"Enhanced configuration loaded:")
                logger.info(f"  Marqo URL: {self.config.marqo_url}")
                logger.info(f"  Number of indexers: {len(self.config.indexers)}")
                
                for idx, indexer_config in enumerate(self.config.indexers):
                    logger.info(f"  Indexer {idx+1}: {indexer_config.indexer_type} - {indexer_config.index_name}")
                    logger.info(f"    Source directory: {indexer_config.source_dir}")
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                sys.exit(1)
            
            # Create Marqo client
            try:
                self.marqo_client = marqo.Client(url=self.config.marqo_url)
            except Exception as e:
                logger.error(f"Failed to create Marqo client: {e}")
                sys.exit(1)
            
            # Check Marqo compatibility
            try:
                check_marqo_compatibility(self.marqo_client)
            except Exception as e:
                logger.warning(f"Compatibility check failed: {e}")
            
            await self._create_indexers()
            await self.health_server.start()
            self.health_server.update_status('ready')
            
            self.service_state.marqo_client = self.marqo_client
            self.service_state.config = self.config
            self.service_state.indexers = self.indexers
            self.service_state.watchers = self.watchers
            self.service_state.status = 'ready'
            set_service_state(self.service_state)
        except Exception as e:
            logger.error(f"Failed to initialize enhanced sync service: {e}")
            sys.exit(1)
    
    async def _create_indexers(self):
        """Create indexers for each configured indexer type."""
        for indexer_config in self.config.indexers:
            try:
                # Skip disabled indexers
                if not indexer_config.enabled:
                    logger.info(f"Skipping disabled indexer: {indexer_config.index_name}")
                    continue
                
                # Ensure index exists with proper settings
                try:
                    ensure_index_exists(self.marqo_client, self.config.to_legacy_config(indexer_config.index_name))
                except Exception as e:
                    logger.error(f"Failed to ensure index exists for {indexer_config.index_name}: {e}")
                    continue
                
                # Create indexer using factory
                indexer = IndexerFactory.create_indexer(
                    indexer_config.indexer_type,
                    self.marqo_client,
                    self.config.to_legacy_config(indexer_config.index_name)
                )
                
                self.indexers[indexer_config.index_name] = indexer
                logger.info(f"Created indexer for {indexer_config.index_name}")
                
            except Exception as e:
                logger.error(f"Failed to create indexer for {indexer_config.index_name}: {e}")
    
    async def run(self):
        """Run the sync service with all configured indexers."""
        if not self.indexers:
            logger.error("No valid indexers configured, exiting")
            sys.exit(1)
        
        # Perform initial indexing for all indexers
        for index_name, indexer in self.indexers.items():
            try:
                # Find the corresponding config
                config = next(cfg for cfg in self.config.indexers if cfg.index_name == index_name)
                
                logger.info(f"Starting initial indexing for {index_name}")
                
                # Handle unified indexers with multiple projects/types
                if hasattr(config, 'settings') and 'projects' in config.settings:
                    # Handle codebase/codex indexers with multiple projects
                    # Each project gets its own index
                    for project_name, project_path in config.settings['projects']:
                        # Create project-specific index name
                        project_index_name = f"{config.index_name}-{project_name}".lower().replace(' ', '-').replace('_', '-')
                        logger.info(f"Indexing project {project_name} at {project_path} into index {project_index_name}")
                        
                        # Create a new config with project-specific index name
                        from .config import SyncConfig
                        project_config = SyncConfig(
                            index_name=project_index_name,
                            marqo_url=self.config.marqo_url,
                            max_file_size_bytes=self.config.max_file_size_bytes,
                            store_large_files_metadata_only=self.config.store_large_files_metadata_only
                        )
                        
                        # Create indexer instance for this project
                        from .indexer_factory import IndexerFactory
                        project_indexer = IndexerFactory.create_indexer(
                            config.indexer_type,
                            self.marqo_client,
                            project_config
                        )
                        
                        # Set project context
                        if hasattr(project_indexer, 'set_project_context'):
                            project_indexer.set_project_context(project_name, project_path, project_index_name)
                        
                        # Ensure index exists
                        from .marqo_handlers import ensure_index_exists
                        ensure_index_exists(self.marqo_client, project_config)
                        
                        # Store indexer for this project
                        self.indexers[project_index_name] = project_indexer
                        
                        # Start watcher for this project
                        from .watcher import FileWatcher
                        watcher = FileWatcher(project_indexer, project_path)
                        watcher.start()
                        self.watchers[project_index_name] = watcher
                        
                        await project_indexer.index_directory(project_path)
                        
                elif hasattr(config, 'settings') and 'conversation_types' in config.settings:
                    # Handle conversation indexers with multiple types
                    # Each conversation type gets its own index
                    for conv_type, conv_path in config.settings['conversation_types']:
                        # Create conversation-specific index name
                        conv_index_name = f"{config.index_name}-{conv_type}".lower().replace(' ', '-').replace('_', '-')
                        logger.info(f"Indexing conversation type {conv_type} at {conv_path} into index {conv_index_name}")
                        
                        # Create a new config with conversation-specific index name
                        from .config import SyncConfig
                        conv_config = SyncConfig(
                            index_name=conv_index_name,
                            marqo_url=self.config.marqo_url,
                            max_file_size_bytes=self.config.max_file_size_bytes,
                            store_large_files_metadata_only=self.config.store_large_files_metadata_only
                        )
                        
                        # Create indexer instance for this conversation type
                        from .indexer_factory import IndexerFactory
                        conv_indexer = IndexerFactory.create_indexer(
                            config.indexer_type,
                            self.marqo_client,
                            conv_config
                        )
                        
                        # Set conversation context
                        if hasattr(conv_indexer, 'set_conversation_context'):
                            conv_indexer.set_conversation_context(conv_type, conv_path, conv_index_name)
                        
                        # Ensure index exists
                        from .marqo_handlers import ensure_index_exists
                        ensure_index_exists(self.marqo_client, conv_config)
                        
                        # Store indexer for this conversation type
                        self.indexers[conv_index_name] = conv_indexer
                        
                        # Start watcher for this conversation type
                        from .watcher import FileWatcher
                        watcher = FileWatcher(conv_indexer, conv_path)
                        watcher.start()
                        self.watchers[conv_index_name] = watcher
                        
                        await conv_indexer.index_directory(conv_path)
                else:
                    # Handle legacy single-directory indexers
                    await indexer.index_directory(config.source_dir)
                    
            except Exception as e:
                logger.error(f"Error during initial indexing for {index_name}: {e}")
        
        # Setup and start file watchers for each indexer
        for index_name, indexer in self.indexers.items():
            try:
                # Find the corresponding config
                config = next(cfg for cfg in self.config.indexers if cfg.index_name == index_name)
                
                # Handle unified indexers with multiple projects/types
                if hasattr(config, 'settings') and 'projects' in config.settings:
                    # Create watchers for each project
                    for project_name, project_path in config.settings['projects']:
                        logger.info(f"Starting file watcher for project {project_name} at {project_path}")
                        watcher = FileWatcher(indexer, root_dir=project_path)
                        
                        if platform.system() == 'Windows':
                            logger.info(f"Starting file watcher on Windows for {index_name} project {project_name}")
                        
                        watcher.start()
                        self.watchers[f"{index_name}_{project_name}"] = watcher
                        
                elif hasattr(config, 'settings') and 'conversation_types' in config.settings:
                    # Create watchers for each conversation type
                    for conv_type, conv_path in config.settings['conversation_types']:
                        logger.info(f"Starting file watcher for conversation type {conv_type} at {conv_path}")
                        watcher = FileWatcher(indexer, root_dir=conv_path)
                        
                        if platform.system() == 'Windows':
                            logger.info(f"Starting file watcher on Windows for {index_name} type {conv_type}")
                        
                        watcher.start()
                        self.watchers[f"{index_name}_{conv_type}"] = watcher
                else:
                    # Handle legacy single-directory indexers
                    watcher = FileWatcher(indexer, root_dir=config.source_dir)
                    
                    if platform.system() == 'Windows':
                        logger.info(f"Starting file watcher on Windows for {index_name}")
                    
                    watcher.start()
                    self.watchers[index_name] = watcher
                    logger.info(f"Started file watcher for {index_name} watching {config.source_dir}")
                    
            except Exception as e:
                logger.error(f"Failed to start file watcher for {index_name}: {e}")
                # On Windows, suggest using PollingObserver
                if platform.system() == 'Windows':
                    logger.info("On Windows, consider setting WATCHDOG_USE_POLLING=1 environment variable")
        
        self.service_state.status = 'running'
        self.service_state.indexers = self.indexers
        self.service_state.watchers = self.watchers
        set_service_state(self.service_state)
        
        self.health_server.update_status('running', 
                                       indexers={name: {'type': type(idx).__name__} for name, idx in self.indexers.items()},
                                       watchers={name: {'root_dir': watcher.root_dir} for name, watcher in self.watchers.items()})
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal, stopping watchers")
            self.health_server.update_status('stopping')
            for index_name, watcher in self.watchers.items():
                try:
                    watcher.stop()
                    logger.info(f"Stopped watcher for {index_name}")
                except Exception as e:
                    logger.error(f"Error stopping watcher for {index_name}: {e}")
            await self.health_server.stop()

async def run_enhanced_service():
    """Run the enhanced sync service."""
    service = EnhancedSyncService()
    await service.initialize()
    await service.run()

def main():
    """Main entry point for the enhanced sync service."""
    asyncio.run(run_enhanced_service())

if __name__ == "__main__":
    main()
