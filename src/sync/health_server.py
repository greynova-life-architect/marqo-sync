import asyncio
import logging
from typing import Dict, Any, Optional

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None

from .env_config import env_config

logger = logging.getLogger(__name__)

class HealthServer:
    def __init__(self, port: int = 8080):
        self.port = port
        self.enabled = AIOHTTP_AVAILABLE
        self.app = None
        self.runner = None
        self.site = None
        self.service_status = {
            'status': 'initializing',
            'indexers': {},
            'watchers': {}
        }
        
        if self.enabled:
            self.app = web.Application()
            self.app.router.add_get('/health', self.health_check)
            self.app.router.add_get('/status', self.status_check)
        else:
            logger.warning("aiohttp not available, health check server disabled")
    
    def update_status(self, status: str, indexers: Dict[str, Any] = None, watchers: Dict[str, Any] = None):
        self.service_status['status'] = status
        if indexers:
            self.service_status['indexers'] = indexers
        if watchers:
            self.service_status['watchers'] = watchers
    
    async def health_check(self, request):
        return web.json_response({'status': 'healthy'})
    
    async def status_check(self, request):
        return web.json_response(self.service_status)
    
    async def start(self):
        if not self.enabled:
            logger.info("Health check server disabled (aiohttp not available)")
            return
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        host = env_config.get_health_server_host()
        self.site = web.TCPSite(self.runner, host, self.port)
        await self.site.start()
        logger.info(f"Health check server started on {host}:{self.port}")
    
    async def stop(self):
        if not self.enabled:
            return
        
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Health check server stopped")

