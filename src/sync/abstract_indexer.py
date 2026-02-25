"""Abstract base class for all indexers in the sync service."""
import os
import logging
import hashlib
import json
import re
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import marqo
from pathlib import Path

from .config import SyncConfig

logger = logging.getLogger(__name__)

class AbstractIndexer(ABC):
    """Base class for all indexers with common functionality."""
    
    def __init__(self, marqo_client: marqo.Client, config: SyncConfig):
        """Initialize the indexer with Marqo client and configuration.
        
        Args:
            marqo_client: Marqo client instance
            config: Configuration for the indexer
        """
        self.marqo_client = marqo_client
        self.config = config
        self.hash_file = Path(f"file_hashes_{config.index_name}.json")
        self.file_hashes = self._load_hashes()
        
    def _load_hashes(self) -> Dict[str, str]:
        """Load saved file hashes from disk."""
        if self.hash_file.exists():
            try:
                with open(self.hash_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading hash file: {e}")
        return {}
        
    def _save_hashes(self) -> None:
        """Save file hashes to disk."""
        try:
            with open(self.hash_file, 'w') as f:
                json.dump(self.file_hashes, f)
        except Exception as e:
            logger.error(f"Error saving hash file: {e}")
            
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash for {file_path}: {e}")
            return ""

    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get file metadata including size and modification time."""
        try:
            stat = os.stat(file_path)
            return {
                'size_bytes': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime
            }
        except Exception as e:
            logger.error(f"Error getting file metadata for {file_path}: {e}")
            return {}

    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped based on extension or directory."""
        # Check file extension
        if any(file_path.endswith(ext) for ext in self.config.skip_extensions):
            return True
            
        # Check if file is in a directory that should be skipped
        dir_path = os.path.dirname(file_path)
        while dir_path:
            if self.config.should_skip_directory(dir_path):
                return True
            parent = os.path.dirname(dir_path)
            if parent == dir_path:  # Reached root
                break
            dir_path = parent
            
        return False

    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content with size check and file type validation."""
        try:
            # First check if this file should be skipped (double-check)
            if self._should_skip_file(file_path):
                logger.debug(f"Skipping file due to extension or directory: {file_path}")
                return None
            
            file_size = os.path.getsize(file_path)
            
            # If file is too large and we're configured to store metadata only
            if file_size > self.config.max_file_size_bytes and self.config.store_large_files_metadata_only:
                logger.debug(f"File too large, storing metadata only: {file_path}")
                return None
            
            # Check file extension to determine if it's text-based
            text_extensions = {
                '.txt', '.md', '.rst', '.json', '.yaml', '.yml', '.xml', '.html', '.htm',
                '.css', '.js', '.ts', '.py', '.java', '.cpp', '.h', '.c', '.hpp',
                '.cs', '.go', '.rs', '.php', '.rb', '.pl', '.sh', '.bat', '.ps1',
                '.sql', '.r', '.m', '.scala', '.kt', '.swift', '.dart', '.lua'
            }
            
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in text_extensions:
                logger.debug(f"Skipping binary file: {file_path} (extension: {file_ext})")
                return None
                
            # Try to read as text file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.debug(f"Successfully read text file: {file_path} ({len(content)} chars)")
                return content
                
        except UnicodeDecodeError as e:
            logger.debug(f"File is not valid UTF-8 text, skipping: {file_path} - {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

    def _validate_file_for_indexing(self, file_path: str) -> bool:
        """Validate if a file should be indexed."""
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            if file_path in self.file_hashes:
                del self.file_hashes[file_path]
                self._save_hashes()
            return False
            
        if self._should_skip_file(file_path):
            return False
            
        # Check if file has changed
        current_hash = self._get_file_hash(file_path)
        if not current_hash:
            return False
            
        if file_path in self.file_hashes and self.file_hashes[file_path] == current_hash:
            logger.debug(f"File unchanged, skipping: {file_path}")
            return False
            
        return True

    def _sanitize_content(self, content: str, file_path: str) -> Optional[str]:
        """Common content sanitization logic."""
        try:
            logger.info(f"Sanitizing content for: {file_path}")
            # Remove null bytes and other problematic characters
            content = content.replace('\x00', '')
            content = content.replace('\r', '\n')
            
            # Remove excessive whitespace but preserve meaningful content
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Remove excessive blank lines
            content = content.strip()
            
            # Ensure content is not empty after sanitization
            if not content:
                logger.error(f"Content for {file_path} is empty after sanitization - skipping")
                return None
            
            # If content is very short, add a note to make it searchable
            if len(content) < 10:
                content = f"File: {os.path.basename(file_path)} - {content}"
            
            # Check content length
            if len(content) > 1000000:  # 1MB limit
                logger.warning(f"Content for {file_path} exceeds 1MB limit, truncating")
                content = content[:1000000]
            
            logger.info(f"Content sanitized successfully, length: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"EXCEPTION during content sanitization for {file_path}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def _update_file_hash(self, file_path: str) -> None:
        """Update file hash after successful indexing."""
        current_hash = self._get_file_hash(file_path)
        if current_hash:
            self.file_hashes[file_path] = current_hash
            self._save_hashes()
    
    @abstractmethod
    async def index_file(self, file_path: str) -> None:
        """Index a single file if it has changed.
        
        This method must be implemented by subclasses.
        
        Args:
            file_path: Path to the file to index
        """
        pass
        
    @abstractmethod
    async def index_directory(self, directory: str) -> None:
        """Recursively index all files in a directory.
        
        This method must be implemented by subclasses.
        
        Args:
            directory: Directory to index
        """
        pass
