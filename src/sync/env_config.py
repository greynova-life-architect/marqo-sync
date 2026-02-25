import os
import logging
from typing import Optional, List, Set
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EnvironmentConfig:
    _instance: Optional['EnvironmentConfig'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_environment()
            self._initialized = True
    
    def _load_environment(self):
        try:
            current_dir = Path.cwd()
            parent_dir = current_dir.parent
            
            for check_dir in [current_dir, parent_dir]:
                env_file = check_dir / '.env'
                if env_file.exists():
                    logger.info(f"Loading .env file: {env_file}")
                    load_dotenv(env_file)
                    break
            else:
                load_dotenv()
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
            load_dotenv()
    
    def _get_str(self, key: str, default: str = '') -> str:
        value = os.getenv(key, default)
        return value.strip() if value else default
    
    def _get_int(self, key: str, default: int) -> int:
        value = os.getenv(key)
        if value is None:
            return default
        try:
            parsed = int(value.strip())
            if parsed < 0:
                logger.warning(f"Negative integer value for {key}: {parsed}, using default {default}")
                return default
            return parsed
        except (ValueError, AttributeError):
            logger.warning(f"Invalid integer value for {key}: {value}, using default {default}")
            return default
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        value = os.getenv(key)
        if value is None:
            return default
        value_lower = str(value).strip().lower()
        return value_lower in ('1', 'true', 'yes', 'on')
    
    def _get_list(self, key: str, default: List[str] = None) -> List[str]:
        if default is None:
            default = []
        value = os.getenv(key)
        if not value:
            return default
        return [item.strip() for item in value.split(',') if item.strip()]
    
    def _validate_url(self, url: str) -> bool:
        if not url:
            return False
        return url.startswith('http://') or url.startswith('https://')
    
    def _validate_port(self, port: int) -> bool:
        return 1 <= port <= 65535
    
    def get_marqo_url(self) -> str:
        url = self._get_str('MARQO_URL', 'http://localhost:8882')
        if not self._validate_url(url):
            logger.warning(f"Invalid MARQO_URL format: {url}, using default")
            url = 'http://localhost:8882'
        return url
    
    def get_sync_config_file(self) -> Optional[str]:
        value = self._get_str('SYNC_CONFIG_FILE')
        if value and Path(value).exists():
            return value
        return None
    
    def get_chunking_config_file(self) -> Optional[str]:
        value = self._get_str('CHUNKING_CONFIG_FILE')
        if value and Path(value).exists():
            return value
        return None
    
    def get_sync_source_dir(self) -> str:
        return self._get_str('SYNC_SOURCE_DIR', './data')
    
    def get_sync_index_name(self) -> str:
        return self._get_str('SYNC_INDEX_NAME', 'deepcache')
    
    def get_sync_skip_dirs(self, default_dirs: Set[str]) -> Set[str]:
        default_str = ','.join(default_dirs)
        dirs_str = self._get_str('SYNC_SKIP_DIRS', default_str)
        return set(dirs_str.split(',')) if dirs_str else default_dirs
    
    def get_sync_codebases(self) -> str:
        return self._get_str('SYNC_CODEBASES', '')
    
    def get_sync_codex(self) -> str:
        return self._get_str('SYNC_CODEX', '')
    
    def get_sync_conversations(self) -> str:
        return self._get_str('SYNC_CONVERSATIONS', '')
    
    def get_sync_max_file_size(self) -> int:
        size = self._get_int('SYNC_MAX_FILE_SIZE', 1024 * 1024)
        if size <= 0:
            logger.warning(f"Invalid file size: {size}, using default 1MB")
            size = 1024 * 1024
        return size
    
    def get_sync_store_large_files_meta(self) -> bool:
        return self._get_bool('SYNC_STORE_LARGE_FILES_META', True)
    
    def get_health_check_port(self) -> int:
        port = self._get_int('HEALTH_CHECK_PORT', 8080)
        if not self._validate_port(port):
            logger.warning(f"Invalid port value: {port}, using default 8080")
            port = 8080
        return port
    
    def get_watchdog_use_polling(self) -> bool:
        return self._get_bool('WATCHDOG_USE_POLLING', False)
    
    def get_force_index_recreate(self) -> bool:
        return self._get_bool('FORCE_INDEX_RECREATE', False)
    
    def get_api_server_host(self) -> str:
        return self._get_str('API_SERVER_HOST', '0.0.0.0')
    
    def get_api_server_port(self) -> int:
        port = self._get_int('API_SERVER_PORT', 8000)
        if not self._validate_port(port):
            logger.warning(f"Invalid API server port: {port}, using default 8000")
            port = 8000
        return port
    
    def get_frontend_dev_port(self) -> int:
        port = self._get_int('FRONTEND_DEV_PORT', 3000)
        if not self._validate_port(port):
            logger.warning(f"Invalid frontend dev port: {port}, using default 3000")
            port = 3000
        return port
    
    def get_health_server_host(self) -> str:
        return self._get_str('HEALTH_SERVER_HOST', 'localhost')
    
    def get_default_config_file(self) -> str:
        return self._get_str('DEFAULT_CONFIG_FILE', 'marqo-sync-config.yaml')

env_config = EnvironmentConfig()

