#!/usr/bin/env python3
"""
MCP Server Manager

This service manages the lifecycle of all MCP servers, including:
- Starting and stopping servers
- Health monitoring
- Automatic restarts
- Resource management
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import aiohttp
from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPServerProcess:
    """Manages a single MCP server process"""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
        self.last_health_check: Optional[datetime] = None
        self.health_status = "unknown"

    async def start(self) -> bool:
        """Start the MCP server process"""
        if self.is_running():
            logger.warning(f"Server {self.name} is already running")
            return True

        try:
            cmd = [self.config["command"]] + self.config.get("args", [])
            env = {**os.environ, **self.config.get("env", {})}

            logger.info(f"Starting MCP server {self.name}: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.start_time = datetime.now()

            # Give the process a moment to start
            await asyncio.sleep(1)

            if self.process.poll() is None:
                logger.info(
                    f"MCP server {self.name} started successfully (PID: {self.process.pid})")
                return True
            else:
                stdout, stderr = self.process.communicate()
                logger.error(
                    f"MCP server {self.name} failed to start: {stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to start MCP server {self.name}: {e}")
            return False

    async def stop(self) -> bool:
        """Stop the MCP server process"""
        if not self.is_running():
            return True

        try:
            logger.info(f"Stopping MCP server {self.name}")
            self.process.terminate()

            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(
                    asyncio.create_task(self._wait_for_exit()),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"Force killing MCP server {self.name}")
                self.process.kill()
                await self._wait_for_exit()

            self.process = None
            self.start_time = None
            logger.info(f"MCP server {self.name} stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop MCP server {self.name}: {e}")
            return False

    async def _wait_for_exit(self):
        """Wait for process to exit"""
        while self.process and self.process.poll() is None:
            await asyncio.sleep(0.1)

    def is_running(self) -> bool:
        """Check if the server process is running"""
        return self.process is not None and self.process.poll() is None

    async def health_check(self) -> dict:
        """Perform health check on the server"""
        if not self.is_running():
            self.health_status = "offline"
            return {
                "status": "offline",
                "uptime": 0,
                "restart_count": self.restart_count
            }

        # For now, just check if process is alive
        # In a real implementation, you'd send JSON-RPC health check
        uptime = (datetime.now() -
                  self.start_time).total_seconds() if self.start_time else 0

        self.health_status = "healthy"
        self.last_health_check = datetime.now()

        return {
            "status": "healthy",
            "uptime": uptime,
            "restart_count": self.restart_count,
            "pid": self.process.pid if self.process else None
        }

    async def restart(self) -> bool:
        """Restart the MCP server"""
        logger.info(f"Restarting MCP server {self.name}")
        await self.stop()
        await asyncio.sleep(2)  # Brief pause
        success = await self.start()
        if success:
            self.restart_count += 1
        return success


class MCPServerManager:
    """Manages all MCP servers"""

    def __init__(self, config_file: str = "mcp.json"):
        self.config_file = config_file
        self.servers: Dict[str, MCPServerProcess] = {}
        self.running = False
        self.health_check_interval = 30  # seconds

    async def load_config(self):
        """Load MCP server configurations"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                logger.error(f"Config file not found: {config_path}")
                return

            with open(config_path, 'r') as f:
                config = json.load(f)

            mcp_servers = config.get("mcpServers", {})

            for name, server_config in mcp_servers.items():
                if server_config.get("disabled", False):
                    logger.info(f"Skipping disabled server: {name}")
                    continue

                self.servers[name] = MCPServerProcess(name, server_config)
                logger.info(f"Loaded config for MCP server: {name}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    async def start_all(self):
        """Start all configured MCP servers"""
        logger.info("Starting all MCP servers...")

        for name, server in self.servers.items():
            success = await server.start()
            if not success:
                logger.error(f"Failed to start server: {name}")

        logger.info("All MCP servers start attempts completed")

    async def stop_all(self):
        """Stop all MCP servers"""
        logger.info("Stopping all MCP servers...")

        tasks = []
        for server in self.servers.values():
            tasks.append(server.stop())

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All MCP servers stopped")

    async def health_check_loop(self):
        """Continuous health checking loop"""
        while self.running:
            try:
                for name, server in self.servers.items():
                    health = await server.health_check()

                    if health["status"] == "offline" and server.config.get("auto_restart", True):
                        logger.warning(
                            f"Server {name} is offline, attempting restart...")
                        await server.restart()

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)

    async def get_status(self) -> dict:
        """Get status of all servers"""
        status = {}

        for name, server in self.servers.items():
            health = await server.health_check()
            status[name] = health

        return status

    async def start(self):
        """Start the manager"""
        self.running = True
        await self.load_config()
        await self.start_all()

        # Start health check loop
        asyncio.create_task(self.health_check_loop())

    async def stop(self):
        """Stop the manager"""
        self.running = False
        await self.stop_all()


# Web API for health checks and management
async def health_handler(request):
    """Health check endpoint"""
    manager = request.app['manager']
    status = await manager.get_status()

    return web.json_response({
        "status": "healthy",
        "servers": status,
        "timestamp": datetime.now().isoformat()
    })


async def status_handler(request):
    """Detailed status endpoint"""
    manager = request.app['manager']
    status = await manager.get_status()

    return web.json_response(status)


async def restart_handler(request):
    """Restart specific server"""
    server_name = request.match_info.get('server_name')
    manager = request.app['manager']

    if server_name not in manager.servers:
        return web.json_response(
            {"error": f"Server {server_name} not found"},
            status=404
        )

    server = manager.servers[server_name]
    success = await server.restart()

    return web.json_response({
        "success": success,
        "message": f"Server {server_name} restart {'successful' if success else 'failed'}"
    })


async def init_app():
    """Initialize the web application"""
    app = web.Application()

    # Create and start manager
    manager = MCPServerManager()
    app['manager'] = manager
    await manager.start()

    # Setup routes
    app.router.add_get('/health', health_handler)
    app.router.add_get('/status', status_handler)
    app.router.add_post('/restart/{server_name}', restart_handler)

    return app


async def cleanup(app):
    """Cleanup on shutdown"""
    manager = app['manager']
    await manager.stop()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run app
    app = await init_app()

    # Setup cleanup
    app.on_cleanup.append(cleanup)

    # Run web server
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    logger.info("MCP Server Manager started on http://0.0.0.0:8080")

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
