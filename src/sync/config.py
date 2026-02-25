"""Configuration management for the codebase sync service."""
from dataclasses import dataclass
from typing import Set
import os
from .env_config import env_config

@dataclass
class SyncConfig:
    source_dir: str
    marqo_url: str
    index_name: str
    skip_extensions: Set[str]
    skip_directories: Set[str]
    max_file_size_bytes: int
    store_large_files_metadata_only: bool
    
    @classmethod
    def from_env(cls) -> 'SyncConfig':
        """Create configuration from environment variables."""
        import logging
        logger = logging.getLogger(__name__)
        
        default_skip_dirs = {
            'compiled', 'bin', 'obj', 'build', 'dist',
            'node_modules', '__pycache__', '.git',
            '.idea', '.vscode', '.vs', 'venv',
            'Debug', 'Release', 'x64', 'x86'
        }
        
        source_dir = env_config.get_sync_source_dir()
        marqo_url = env_config.get_marqo_url()
        index_name = env_config.get_sync_index_name()
        skip_directories = env_config.get_sync_skip_dirs(default_skip_dirs)
        max_file_size_bytes = env_config.get_sync_max_file_size()
        store_large_files_metadata_only = env_config.get_sync_store_large_files_meta()
        
        config = cls(
            source_dir=source_dir,
            marqo_url=marqo_url,
            index_name=index_name,
            skip_extensions={
                '.exe', '.dll', '.pdb', '.bin', '.obj', '.lib', '.a', '.o',
                '.pyc', '.pyo', '.pyd', '.so', '.dylib', '.dll', '.sys',
                '.jpg', '.jpeg', '.png', '.gif', '.ico', '.bmp', '.tiff', '.tga',
                '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv', '.flv', '.webm',
                '.wma', '.aac', '.ogg', '.flac', '.m4a', '.m4v', '.3gp',
                '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz', '.lzma',
                '.deb', '.rpm', '.pkg', '.msi', '.dmg', '.iso',
                '.cache', '.log', '.tmp', '.swp', '.bak', '.old', '.orig',
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
                '.ttf', '.otf', '.woff', '.woff2', '.eot',
                '.pyc', '.pyo', '.class', '.o', '.obj', '.exe', '.com',
                '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.fdb',
                '.ldb', '.ndb', '.ibd', '.myd', '.myi', '.frm'
            },
            skip_directories=skip_directories,
            max_file_size_bytes=max_file_size_bytes,
            store_large_files_metadata_only=store_large_files_metadata_only
        )
        
        try:
            logger.info(f"Configuration created with index_name: {config.index_name}")
        except Exception as e:
            pass
        
        return config
    
    def validate(self) -> None:
        """Validate configuration settings."""
        if not os.path.exists(self.source_dir):
            raise ValueError(f"Source directory does not exist: {self.source_dir}")
        
        if self.max_file_size_bytes <= 0:
            raise ValueError("Maximum file size must be positive")
            
        # Convert source_dir to absolute path
        self.source_dir = os.path.abspath(self.source_dir)
        
    def should_skip_directory(self, dir_path: str) -> bool:
        """Check if directory should be skipped."""
        dir_name = os.path.basename(dir_path)
        return dir_name in self.skip_directories 