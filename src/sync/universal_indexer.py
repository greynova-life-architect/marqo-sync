"""Universal indexer that handles all file types for the sync service."""
import os
import logging
import asyncio
import traceback
from typing import Dict, Any, Optional, List
import marqo

from .abstract_indexer import AbstractIndexer
from .config import SyncConfig
from .text_splitter import semantic_split
from .marqo_handlers import (
    ensure_index_exists,
    check_marqo_compatibility,
    index_document_metadata,
    index_document_chunks,
    delete_document
)

logger = logging.getLogger(__name__)

class UniversalIndexer(AbstractIndexer):
    """Universal indexer that handles all file types with optimized logic."""
    
    def __init__(self, marqo_client: marqo.Client, config: SyncConfig, metadata_enhancer=None):
        super().__init__(marqo_client, config)
        self.metadata_enhancer = metadata_enhancer

    async def _process_file_chunks(self, content: str, file_path: str) -> List[str]:
        """Process content into chunks for indexing with enhanced token-based chunking."""
        try:
            logger.info(f"Splitting content into chunks for: {file_path}")
            # Use enhanced chunking with file path for content type detection
            chunks = await semantic_split(content, file_path=file_path, use_enhanced=True)
            if not chunks:
                logger.error(f"No chunks generated for file: {file_path}")
                return []
            logger.info(f"Generated {len(chunks)} chunks for: {file_path}")
            return chunks
        except Exception as e:
            logger.error(f"EXCEPTION during content splitting for {file_path}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Fallback: create a single chunk with truncated content
            fallback_chunk = content[:4000] if len(content) > 4000 else content
            logger.info(f"Using fallback chunk for: {file_path}")
            return [fallback_chunk]

    def _index_metadata_only(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """Index file with metadata only (for large files)."""
        success = index_document_metadata(
            self.marqo_client,
            self.config.index_name,
            file_path,
            metadata
        )
        
        if success:
            logger.info(f"Indexed file metadata: {file_path}")
        else:
            logger.error(f"Failed to index metadata for file: {file_path}")
        
        return success

    async def _index_content_chunks(self, file_path: str, chunks: List[str], metadata: Dict[str, Any]) -> bool:
        """Index file content as chunks."""
        success = await index_document_chunks(
            self.marqo_client,
            self.config.index_name,
            file_path,
            chunks,
            metadata
        )
        
        if success:
            logger.info(f"Indexed file: {file_path} (chunks={len(chunks)})")
        else:
            logger.error(f"Failed to index chunks for file: {file_path}")
        
        return success

    async def index_file(self, file_path: str) -> None:
        """Index a single file if it has changed."""
        try:
            logger.debug(f"Processing file: {file_path}")
            
            # Basic validation using base class method
            if not self._validate_file_for_indexing(file_path):
                logger.debug(f"File validation failed, skipping: {file_path}")
                return
            
            logger.debug(f"File validation passed: {file_path}")
            
            # Additional safety check for binary files
            if self._should_skip_file(file_path):
                logger.debug(f"File should be skipped, storing metadata only: {file_path}")
                metadata = self._get_file_metadata(file_path)
                if self.metadata_enhancer:
                    metadata = self.metadata_enhancer(metadata, file_path)
                if self._index_metadata_only(file_path, metadata):
                    self._update_file_hash(file_path)
                return
            
            # Get file metadata
            metadata = self._get_file_metadata(file_path)
            if self.metadata_enhancer:
                metadata = self.metadata_enhancer(metadata, file_path)
            
            # Read content if appropriate
            content = self._read_file_content(file_path)
            
            if content is None:
                logger.debug(f"No content to index, storing metadata only: {file_path}")
                # Handle large files with metadata only
                if self._index_metadata_only(file_path, metadata):
                    self._update_file_hash(file_path)
            else:
                logger.debug(f"Content read successfully, processing chunks: {file_path}")
                # Sanitize content using base class method
                sanitized_content = self._sanitize_content(content, file_path)
                if sanitized_content:
                    # Process content into chunks
                    chunks = await self._process_file_chunks(sanitized_content, file_path)
                    if chunks:
                        # Index chunks
                        if await self._index_content_chunks(file_path, chunks, metadata):
                            self._update_file_hash(file_path)
            
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")

    async def index_directory(self, directory: str) -> None:
        """Recursively index all files in a directory."""
        logger.info(f"Starting initial indexing of directory: {directory}")
        try:
            # Track existing files to detect deletions
            current_files = set()
            
            for root, dirs, files in os.walk(directory):
                # Skip directories that match skip patterns
                dirs[:] = [d for d in dirs if not self.config.should_skip_directory(d)]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    current_files.add(file_path)
                    await self.index_file(file_path)
                    
            # Remove hashes for deleted files
            deleted_files = set(self.file_hashes.keys()) - current_files
            for file_path in deleted_files:
                del self.file_hashes[file_path]
                logger.info(f"Removed tracking for deleted file: {file_path}")
            
            if deleted_files:
                self._save_hashes()
                
        except Exception as e:
            logger.error(f"Error during directory indexing: {e}")

# Re-export functions from marqo_handlers for backward compatibility
from .marqo_handlers import ensure_index_exists, check_marqo_compatibility
