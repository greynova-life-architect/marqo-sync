"""Resource management utilities for preventing machine stalls."""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Try to import psutil, fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)

@dataclass
class ResourceLimits:
    """Resource limits configuration."""
    max_memory_percent: float = 80.0
    max_cpu_percent: float = 90.0
    min_available_memory_gb: float = 2.0
    batch_size_memory_threshold: float = 4.0  # GB
    max_concurrent_files: int = 4
    max_batch_size: int = 64
    min_batch_size: int = 8

class ResourceManager:
    """Manages system resources to prevent stalls."""
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        """Initialize resource manager."""
        self.limits = limits or ResourceLimits()
        self.last_check_time = 0
        self.check_interval = 1.0  # Check every second
        self.resource_history = []
        self.max_history = 100
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage."""
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil not available, using fallback resource values")
            return {
                'memory_percent': 50.0,  # Conservative fallback
                'memory_available_gb': 4.0,  # Assume 4GB available
                'memory_used_gb': 4.0,
                'memory_total_gb': 8.0,
                'cpu_percent': 50.0,
                'disk_percent': 50.0,
                'disk_free_gb': 100.0,
                'timestamp': time.time()
            }
        
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            disk = psutil.disk_usage('/')
            
            return {
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'cpu_percent': cpu_percent,
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {
                'memory_percent': 0,
                'memory_available_gb': 0,
                'memory_used_gb': 0,
                'memory_total_gb': 0,
                'cpu_percent': 0,
                'disk_percent': 0,
                'disk_free_gb': 0,
                'timestamp': time.time()
            }
    
    def is_system_under_pressure(self) -> bool:
        """Check if system is under resource pressure."""
        resources = self.get_system_resources()
        
        # Check memory pressure
        if resources['memory_percent'] > self.limits.max_memory_percent:
            logger.warning(f"High memory usage: {resources['memory_percent']:.1f}%")
            return True
        
        # Check available memory
        if resources['memory_available_gb'] < self.limits.min_available_memory_gb:
            logger.warning(f"Low available memory: {resources['memory_available_gb']:.1f}GB")
            return True
        
        # Check CPU pressure
        if resources['cpu_percent'] > self.limits.max_cpu_percent:
            logger.warning(f"High CPU usage: {resources['cpu_percent']:.1f}%")
            return True
        
        return False
    
    def get_optimal_batch_size(self) -> int:
        """Get optimal batch size based on available memory."""
        resources = self.get_system_resources()
        available_memory_gb = resources['memory_available_gb']
        
        if available_memory_gb < 2.0:
            batch_size = self.limits.min_batch_size
        elif available_memory_gb < 4.0:
            batch_size = 16
        elif available_memory_gb < 8.0:
            batch_size = 32
        else:
            batch_size = self.limits.max_batch_size
        
        logger.debug(f"Optimal batch size: {batch_size} (available memory: {available_memory_gb:.1f}GB)")
        return batch_size
    
    def get_optimal_concurrency(self) -> int:
        """Get optimal concurrency level based on system resources."""
        resources = self.get_system_resources()
        
        # Base concurrency on available memory and CPU
        if resources['memory_available_gb'] < 2.0:
            concurrency = 1
        elif resources['memory_available_gb'] < 4.0:
            concurrency = 2
        elif resources['cpu_percent'] > 80:
            concurrency = 2
        else:
            concurrency = self.limits.max_concurrent_files
        
        logger.debug(f"Optimal concurrency: {concurrency}")
        return concurrency
    
    async def wait_for_resources(self, timeout: float = 30.0) -> bool:
        """Wait for system resources to become available."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self.is_system_under_pressure():
                return True
            
            logger.info("System under pressure, waiting for resources...")
            await asyncio.sleep(1.0)
        
        logger.warning(f"Timeout waiting for resources after {timeout}s")
        return False
    
    def should_throttle(self) -> bool:
        """Check if processing should be throttled."""
        current_time = time.time()
        
        # Only check if enough time has passed
        if current_time - self.last_check_time < self.check_interval:
            return False
        
        self.last_check_time = current_time
        
        # Get current resources
        resources = self.get_system_resources()
        self.resource_history.append(resources)
        
        # Keep only recent history
        if len(self.resource_history) > self.max_history:
            self.resource_history = self.resource_history[-self.max_history:]
        
        # Check if system is under pressure
        return self.is_system_under_pressure()
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get a summary of current resource usage."""
        resources = self.get_system_resources()
        
        return {
            'memory': {
                'percent': resources['memory_percent'],
                'available_gb': resources['memory_available_gb'],
                'used_gb': resources['memory_used_gb'],
                'total_gb': resources['memory_total_gb']
            },
            'cpu': {
                'percent': resources['cpu_percent']
            },
            'disk': {
                'percent': resources['disk_percent'],
                'free_gb': resources['disk_free_gb']
            },
            'recommendations': {
                'batch_size': self.get_optimal_batch_size(),
                'concurrency': self.get_optimal_concurrency(),
                'should_throttle': self.should_throttle()
            }
        }
    
    def log_resource_status(self):
        """Log current resource status."""
        summary = self.get_resource_summary()
        
        logger.info("Resource Status:")
        logger.info(f"  Memory: {summary['memory']['percent']:.1f}% used, "
                   f"{summary['memory']['available_gb']:.1f}GB available")
        logger.info(f"  CPU: {summary['cpu']['percent']:.1f}%")
        logger.info(f"  Disk: {summary['disk']['percent']:.1f}% used, "
                   f"{summary['disk']['free_gb']:.1f}GB free")
        logger.info(f"  Recommended batch size: {summary['recommendations']['batch_size']}")
        logger.info(f"  Recommended concurrency: {summary['recommendations']['concurrency']}")

# Global resource manager instance
resource_manager = ResourceManager()

def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    return resource_manager

async def wait_for_resources(timeout: float = 30.0) -> bool:
    """Wait for system resources to become available."""
    return await resource_manager.wait_for_resources(timeout)

def should_throttle() -> bool:
    """Check if processing should be throttled."""
    return resource_manager.should_throttle()

def get_optimal_batch_size() -> int:
    """Get optimal batch size based on available memory."""
    return resource_manager.get_optimal_batch_size()

def get_optimal_concurrency() -> int:
    """Get optimal concurrency level based on system resources."""
    return resource_manager.get_optimal_concurrency()

def log_resource_status():
    """Log current resource status."""
    resource_manager.log_resource_status()
