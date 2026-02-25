"""File watching functionality for the sync service."""
import os
import time
import logging
import asyncio
import platform
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from queue import Queue
import threading

from .env_config import env_config

# Import Windows-compatible observer as fallback
if platform.system() == 'Windows':
    try:
        from watchdog.observers.polling import PollingObserver
    except ImportError:
        PollingObserver = None
    
    FORCE_POLLING = env_config.get_watchdog_use_polling()
else:
    PollingObserver = None
    FORCE_POLLING = False

from .abstract_indexer import AbstractIndexer
from .marqo_handlers import delete_document

logger = logging.getLogger(__name__)

class FileChangeHandler(FileSystemEventHandler):
    """Handles file system events and triggers indexing."""
    
    def __init__(self, indexer: AbstractIndexer, task_queue: Optional[Queue] = None):
        super().__init__()
        self.indexer = indexer
        self.task_queue = task_queue
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        logger.info(f"File modified: {event.src_path}")
        if self.task_queue:
            self.task_queue.put(('modified', event.src_path))
        
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        logger.info(f"File created: {event.src_path}")
        if self.task_queue:
            self.task_queue.put(('created', event.src_path))
        
    def on_deleted(self, event):
        """Handle file deletion events."""
        if event.is_directory:
            return
        logger.info(f"File deleted: {event.src_path}")
        if self.task_queue:
            self.task_queue.put(('deleted', event.src_path))

class FileWatcher:
    """Watches for file changes and triggers re-indexing."""
    
    def __init__(self, indexer: AbstractIndexer, root_dir: Optional[str] = None):
        self.indexer = indexer
        self.root_dir = root_dir or indexer.config.source_dir
        self.event_loop = None
        self.event_loop_thread = None
        
        # Create observer with Windows compatibility
        if platform.system() == 'Windows' and FORCE_POLLING and PollingObserver is not None:
            # User explicitly requested polling observer
            self.observer = PollingObserver()
            logger.info("Using PollingObserver (forced by environment variable)")
        else:
            try:
                self.observer = Observer()
            except Exception as e:
                logger.warning(f"Failed to create observer: {e}")
                # Try alternative approach for Windows
                try:
                    if platform.system() == 'Windows' and PollingObserver is not None:
                        # Use polling observer as fallback for Windows
                        self.observer = PollingObserver()
                        logger.info("Using PollingObserver for Windows compatibility")
                    else:
                        raise e
                except Exception as e2:
                    logger.error(f"Failed to create any observer: {e2}")
                    raise e2
        
        self.task_queue = Queue()
        self.event_handler = FileChangeHandler(self.indexer, self.task_queue)
        self.watching = False
        self.processing_thread = None
        
    def start(self) -> None:
        """Start watching the configured directory."""
        logger.info(f"Starting file watcher for directory: {self.root_dir}")
        
        try:
            self.observer.schedule(self.event_handler, self.root_dir, recursive=True)
            self.observer.start()
            
            # Start the processing thread
            self.watching = True
            self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
            self.processing_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start file watcher with default observer: {e}")
            
            # Try to clean up if observer was partially started
            try:
                if hasattr(self.observer, '_running') and self.observer._running:
                    self.observer.stop()
            except:
                pass
            
            # Try fallback to polling observer on Windows
            try:
                if platform.system() == 'Windows' and PollingObserver is not None:
                    logger.info("Attempting to use PollingObserver as fallback...")
                    self.observer = PollingObserver()
                    self.observer.schedule(self.event_handler, self.root_dir, recursive=True)
                    self.observer.start()
                    
                    # Start the processing thread
                    self.watching = True
                    self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
                    self.processing_thread.start()
                    logger.info("Successfully started file watcher with PollingObserver")
                    return
            except Exception as e2:
                logger.error(f"Failed to start file watcher with PollingObserver: {e2}")
            
            # If all attempts fail, raise the original error
            raise e
        
    def _start_event_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.event_loop = loop
        loop.run_forever()
        
    def _process_events(self):
        self.event_loop_thread = threading.Thread(target=self._start_event_loop, daemon=True)
        self.event_loop_thread.start()
        
        while self.event_loop is None:
            time.sleep(0.1)
        
        while self.watching:
            try:
                event_type, file_path = self.task_queue.get(timeout=1.0)
                
                if event_type == 'deleted':
                    try:
                        if file_path in self.indexer.file_hashes:
                            del self.indexer.file_hashes[file_path]
                            self.indexer._save_hashes()
                            logger.info(f"Removed tracking for deleted file: {file_path}")
                        
                        try:
                            delete_document(
                                self.indexer.marqo_client,
                                self.indexer.config.index_name,
                                file_path
                            )
                        except Exception as e:
                            logger.error(f"Error removing documents from index for {file_path}: {e}")
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {e}")
                else:
                    logger.info(f"Processing {event_type} event for: {file_path}")
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.indexer.index_file(file_path),
                            self.event_loop
                        )
                    except Exception as e:
                        logger.error(f"Error processing file event for {file_path}: {e}")
            except Exception as e:
                if "timeout" not in str(e).lower():
                    logger.debug(f"Event processing: {e}")
                continue
        
    def stop(self) -> None:
        self.watching = False
        
        if self.event_loop:
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        if self.event_loop_thread:
            self.event_loop_thread.join(timeout=2.0)
            
        if self.observer:
            logger.info("Stopping file watcher...")
            self.observer.stop()
            self.observer.join() 