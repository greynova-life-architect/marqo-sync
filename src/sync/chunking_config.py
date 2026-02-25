"""Configuration for enhanced chunking parameters."""
from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

class ContentType(Enum):
    """Content type enumeration."""
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONVERSATION = "conversation"
    MIXED = "mixed"
    UNKNOWN = "unknown"

@dataclass
class ChunkingConfig:
    """Configuration for content-type-specific chunking."""
    max_tokens: int
    overlap_tokens: int
    min_tokens: int = 50
    preserve_boundaries: bool = True
    semantic_aware: bool = True
    quality_threshold: float = 0.7

class ChunkingConfigManager:
    """Manager for chunking configurations."""
    
    def __init__(self):
        """Initialize with default configurations."""
        self.configs = {
            ContentType.CODE: ChunkingConfig(
                max_tokens=220,  # 180-260 range, using middle
                overlap_tokens=64,
                min_tokens=50,
                preserve_boundaries=True,
                semantic_aware=True,
                quality_threshold=0.8
            ),
            ContentType.DOCUMENTATION: ChunkingConfig(
                max_tokens=425,  # 350-500 range, using middle
                overlap_tokens=100,
                min_tokens=100,
                preserve_boundaries=True,
                semantic_aware=True,
                quality_threshold=0.7
            ),
            ContentType.CONVERSATION: ChunkingConfig(
                max_tokens=300,  # 3-5 turns per chunk
                overlap_tokens=50,
                min_tokens=100,
                preserve_boundaries=True,
                semantic_aware=True,
                quality_threshold=0.75
            ),
            ContentType.MIXED: ChunkingConfig(
                max_tokens=300,
                overlap_tokens=75,
                min_tokens=75,
                preserve_boundaries=True,
                semantic_aware=True,
                quality_threshold=0.7
            ),
            ContentType.UNKNOWN: ChunkingConfig(
                max_tokens=400,
                overlap_tokens=100,
                min_tokens=100,
                preserve_boundaries=False,
                semantic_aware=False,
                quality_threshold=0.6
            )
        }
    
    def get_config(self, content_type: ContentType) -> ChunkingConfig:
        """Get configuration for content type."""
        return self.configs.get(content_type, self.configs[ContentType.UNKNOWN])
    
    def update_config(self, content_type: ContentType, config: ChunkingConfig) -> None:
        """Update configuration for content type."""
        self.configs[content_type] = config
    
    def get_all_configs(self) -> Dict[ContentType, ChunkingConfig]:
        """Get all configurations."""
        return self.configs.copy()
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert configurations to dictionary."""
        return {
            content_type.value: {
                "max_tokens": config.max_tokens,
                "overlap_tokens": config.overlap_tokens,
                "min_tokens": config.min_tokens,
                "preserve_boundaries": config.preserve_boundaries,
                "semantic_aware": config.semantic_aware,
                "quality_threshold": config.quality_threshold
            }
            for content_type, config in self.configs.items()
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Dict[str, Any]]) -> 'ChunkingConfigManager':
        """Create configuration manager from dictionary."""
        manager = cls()
        
        for content_type_str, config_data in config_dict.items():
            try:
                content_type = ContentType(content_type_str)
                config = ChunkingConfig(**config_data)
                manager.update_config(content_type, config)
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid configuration for {content_type_str}: {e}")
        
        return manager

# Global configuration manager instance
config_manager = ChunkingConfigManager()

# Environment-based configuration loading
from typing import Optional
from .env_config import env_config

def load_config_from_env() -> Optional[ChunkingConfigManager]:
    """Load configuration from environment variables."""
    config_file = env_config.get_chunking_config_file()
    if config_file:
        try:
            import json
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
            return ChunkingConfigManager.from_dict(config_dict)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_file}: {e}")
    
    return None

# Load configuration if available
env_config = load_config_from_env()
if env_config:
    config_manager = env_config


