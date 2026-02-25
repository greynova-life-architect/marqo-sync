#!/usr/bin/env python3
"""Resource monitoring script for Marqo Sync service."""

import asyncio
import time
import logging
import sys
import os
from typing import Dict, Any
import json
from datetime import datetime

# Add the src/sync directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'sync'))

try:
    from resource_manager import ResourceManager, ResourceLimits
    import psutil
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install required dependencies: pip install psutil")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resource_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitor system resources and provide recommendations."""
    
    def __init__(self):
        """Initialize resource monitor."""
        self.resource_manager = ResourceManager()
        self.monitoring = False
        self.resource_history = []
        self.max_history = 1000
        self.alert_thresholds = {
            'memory_percent': 85.0,
            'cpu_percent': 90.0,
            'disk_percent': 90.0
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        try:
            # CPU information
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1.0)
            cpu_freq = psutil.cpu_freq()
            
            # Memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk information
            disk = psutil.disk_usage('/')
            
            # Network information
            network = psutil.net_io_counters()
            
            # Process information
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['memory_percent'] > 1.0:  # Only show processes using >1% memory
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'count': cpu_count,
                    'percent': cpu_percent,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent,
                    'swap_total_gb': swap.total / (1024**3),
                    'swap_used_gb': swap.used / (1024**3)
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'top_processes': processes[:10]  # Top 10 memory-consuming processes
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    def check_alerts(self, system_info: Dict[str, Any]) -> list:
        """Check for resource alerts."""
        alerts = []
        
        if not system_info:
            return alerts
        
        # Memory alert
        if system_info['memory']['percent'] > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'memory',
                'level': 'warning',
                'message': f"High memory usage: {system_info['memory']['percent']:.1f}%",
                'value': system_info['memory']['percent']
            })
        
        # CPU alert
        if system_info['cpu']['percent'] > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu',
                'level': 'warning',
                'message': f"High CPU usage: {system_info['cpu']['percent']:.1f}%",
                'value': system_info['cpu']['percent']
            })
        
        # Disk alert
        if system_info['disk']['percent'] > self.alert_thresholds['disk_percent']:
            alerts.append({
                'type': 'disk',
                'level': 'warning',
                'message': f"High disk usage: {system_info['disk']['percent']:.1f}%",
                'value': system_info['disk']['percent']
            })
        
        return alerts
    
    def get_recommendations(self, system_info: Dict[str, Any]) -> list:
        """Get optimization recommendations."""
        recommendations = []
        
        if not system_info:
            return recommendations
        
        # Memory recommendations
        memory_percent = system_info['memory']['percent']
        if memory_percent > 80:
            recommendations.append("Consider reducing batch size in sync service")
            recommendations.append("Check for memory leaks in running processes")
        elif memory_percent > 60:
            recommendations.append("Monitor memory usage closely")
        
        # CPU recommendations
        cpu_percent = system_info['cpu']['percent']
        if cpu_percent > 80:
            recommendations.append("Consider reducing concurrency in sync service")
            recommendations.append("Check for CPU-intensive processes")
        
        # Disk recommendations
        disk_percent = system_info['disk']['percent']
        if disk_percent > 80:
            recommendations.append("Consider cleaning up temporary files")
            recommendations.append("Monitor disk space usage")
        
        return recommendations
    
    def log_system_status(self, system_info: Dict[str, Any], alerts: list, recommendations: list):
        """Log system status."""
        if not system_info:
            logger.error("No system information available")
            return
        
        # Log basic status
        logger.info("=== System Status ===")
        logger.info(f"CPU: {system_info['cpu']['percent']:.1f}% ({system_info['cpu']['count']} cores)")
        logger.info(f"Memory: {system_info['memory']['percent']:.1f}% "
                   f"({system_info['memory']['used_gb']:.1f}GB / {system_info['memory']['total_gb']:.1f}GB)")
        logger.info(f"Disk: {system_info['disk']['percent']:.1f}% "
                   f"({system_info['disk']['used_gb']:.1f}GB / {system_info['disk']['total_gb']:.1f}GB)")
        
        # Log alerts
        if alerts:
            logger.warning("=== Alerts ===")
            for alert in alerts:
                logger.warning(f"{alert['type'].upper()}: {alert['message']}")
        
        # Log recommendations
        if recommendations:
            logger.info("=== Recommendations ===")
            for rec in recommendations:
                logger.info(f"- {rec}")
        
        # Log top processes
        if system_info['top_processes']:
            logger.info("=== Top Memory Processes ===")
            for proc in system_info['top_processes'][:5]:
                logger.info(f"  {proc['name']}: {proc['memory_percent']:.1f}% memory, {proc['cpu_percent']:.1f}% CPU")
    
    def save_snapshot(self, system_info: Dict[str, Any], alerts: list, recommendations: list):
        """Save system snapshot to file."""
        snapshot = {
            'timestamp': system_info['timestamp'],
            'system_info': system_info,
            'alerts': alerts,
            'recommendations': recommendations
        }
        
        # Add to history
        self.resource_history.append(snapshot)
        if len(self.resource_history) > self.max_history:
            self.resource_history = self.resource_history[-self.max_history:]
        
        # Save to file
        try:
            with open('resource_snapshots.json', 'w') as f:
                json.dump(self.resource_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
    
    async def monitor_loop(self, interval: float = 10.0):
        """Main monitoring loop."""
        logger.info(f"Starting resource monitoring (interval: {interval}s)")
        self.monitoring = True
        
        try:
            while self.monitoring:
                # Get system information
                system_info = self.get_system_info()
                
                # Check for alerts
                alerts = self.check_alerts(system_info)
                
                # Get recommendations
                recommendations = self.get_recommendations(system_info)
                
                # Log status
                self.log_system_status(system_info, alerts, recommendations)
                
                # Save snapshot
                self.save_snapshot(system_info, alerts, recommendations)
                
                # Wait for next check
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            self.monitoring = False
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False

async def main():
    """Main function."""
    monitor = ResourceMonitor()
    
    try:
        # Run monitoring loop
        await monitor.monitor_loop(interval=10.0)
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted")
    finally:
        monitor.stop_monitoring()
        logger.info("Resource monitoring stopped")

if __name__ == "__main__":
    asyncio.run(main())


