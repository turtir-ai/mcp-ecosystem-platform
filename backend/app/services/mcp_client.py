"""
MCP Client Implementation

This module provides the unified MCP client for communicating with
MCP servers using JSON-RPC protocol over stdio.
"""

import asyncio
import json
import logging
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.interfaces import (
    IMCPClient, MCPServerConfig, HealthStatus, ToolDefinition,
    MCPServerStatus, MCPError, MCPConnectionError, MCPTimeoutError
)

logger = logging.getLogger(__name__)


class MCPClient(IMCPClient):
    """
    Unified MCP client for JSON-RPC communication with MCP servers
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.is_initialized = False
        self.tools_cache: List[ToolDefinition] = []
        self.last_health_check: Optional[datetime] = None
        self._request_id = 0
        self._lock = asyncio.Lock()

    async def initialize(self, config: MCPServerConfig) -> bool:
        """Initialize connection to MCP server"""
        async with self._lock:
            if self.is_initialized and self.process and self.process.poll() is None:
                return True

            try:
                logger.info(f"Initializing MCP server: {config.name}")

                # Build command
                cmd = [config.command] + config.args
                env = {**dict(os.environ), **config.env}

                # Start process
                self.process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    bufsize=0
                )

                # Wait a moment for startup
                await asyncio.sleep(1)

                # Check if process started successfully
                if self.process.poll() is not None:
                    stdout, stderr = self.process.communicate()
                    raise MCPConnectionError(
                        f"MCP server {config.name} failed to start: {stderr}",
                        server_name=config.name
                    )

                # Send initialize request
                init_response = await self._send_request("initialize", {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": True},
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "mcp-ecosystem-platform",
                        "version": "1.0.0"
                    }
                })

                if "error" in init_response:
                    raise MCPConnectionError(
                        f"MCP server {config.name} initialization failed: {init_response['error']}",
                        server_name=config.name
                    )

                # Send initialized notification
                await self._send_notification("notifications/initialized")

                # Cache available tools
                await self._refresh_tools_cache()

                self.is_initialized = True
                logger.info(
                    f"MCP server {config.name} initialized successfully")
                return True

            except Exception as e:
                logger.error(
                    f"Failed to initialize MCP server {config.name}: {e}")
                await self._cleanup()
                if isinstance(e, MCPError):
                    raise
                raise MCPConnectionError(
                    f"Failed to initialize MCP server {config.name}: {str(e)}",
                    server_name=config.name
                )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(MCPTimeoutError)
    )
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the MCP server with retry logic"""
        if not self.is_initialized:
            raise MCPConnectionError(
                f"MCP server {self.config.name} not initialized",
                server_name=self.config.name
            )

        try:
            logger.debug(f"Calling tool {tool_name} on {self.config.name}")

            response = await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            }, timeout=self.config.timeout)

            if "error" in response:
                raise MCPError(
                    f"Tool call failed: {response['error']}",
                    server_name=self.config.name,
                    error_code=response.get("error", {}).get("code")
                )

            return response.get("result", {})

        except asyncio.TimeoutError:
            raise MCPTimeoutError(
                f"Tool call {tool_name} timed out on {self.config.name}",
                server_name=self.config.name
            )
        except Exception as e:
            logger.error(
                f"Tool call {tool_name} failed on {self.config.name}: {e}")
            if isinstance(e, MCPError):
                raise
            raise MCPError(
                f"Tool call failed: {str(e)}",
                server_name=self.config.name
            )

    async def health_check(self) -> HealthStatus:
        """Check server health and response time"""
        start_time = time.time()

        try:
            if not self.process or self.process.poll() is not None:
                return HealthStatus(
                    status=MCPServerStatus.OFFLINE,
                    response_time_ms=0,
                    last_check=datetime.now(),
                    error_message="Process not running",
                    uptime_percentage=0.0
                )

            # Send ping request
            response = await self._send_request("ping", {}, timeout=5)

            response_time = (time.time() - start_time) * 1000

            if "error" in response:
                return HealthStatus(
                    status=MCPServerStatus.DEGRADED,
                    response_time_ms=response_time,
                    last_check=datetime.now(),
                    error_message=str(response["error"]),
                    uptime_percentage=75.0
                )

            # Determine status based on response time
            if response_time > 5000:  # 5 seconds
                status = MCPServerStatus.DEGRADED
            elif response_time > 1000:  # 1 second
                status = MCPServerStatus.DEGRADED
            else:
                status = MCPServerStatus.HEALTHY

            self.last_health_check = datetime.now()

            return HealthStatus(
                status=status,
                response_time_ms=response_time,
                last_check=self.last_health_check,
                uptime_percentage=95.0 if status == MCPServerStatus.HEALTHY else 80.0
            )

        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            return HealthStatus(
                status=MCPServerStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                error_message=str(e),
                uptime_percentage=0.0
            )

    async def list_tools(self) -> List[ToolDefinition]:
        """Get available tools from server"""
        if not self.is_initialized:
            await self._refresh_tools_cache()

        return self.tools_cache.copy()

    async def shutdown(self) -> bool:
        """Gracefully shutdown the MCP server connection"""
        try:
            logger.info(f"Shutting down MCP server: {self.config.name}")

            if self.is_initialized and self.process:
                # Send shutdown notification
                try:
                    await self._send_notification("notifications/cancelled")
                except:
                    pass  # Ignore errors during shutdown

            await self._cleanup()
            return True

        except Exception as e:
            logger.error(f"Error during shutdown of {self.config.name}: {e}")
            return False

    async def _refresh_tools_cache(self) -> None:
        """Refresh the cached list of available tools"""
        try:
            if not self.is_initialized:
                return

            response = await self._send_request("tools/list", {})

            if "error" not in response and "result" in response:
                tools_data = response["result"].get("tools", [])
                self.tools_cache = [
                    ToolDefinition(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        parameters=tool.get("inputSchema", {}),
                        required_parameters=tool.get(
                            "inputSchema", {}).get("required", [])
                    )
                    for tool in tools_data
                ]
                logger.debug(
                    f"Cached {len(self.tools_cache)} tools for {self.config.name}")

        except Exception as e:
            logger.warning(
                f"Failed to refresh tools cache for {self.config.name}: {e}")

    async def _send_request(self, method: str, params: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server"""
        if not self.process or self.process.poll() is not None:
            raise MCPConnectionError(
                f"MCP server {self.config.name} process not running",
                server_name=self.config.name
            )

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }

        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # Read response with timeout
            response_line = await asyncio.wait_for(
                self._read_line(),
                timeout=timeout
            )

            if not response_line:
                raise MCPConnectionError(
                    f"No response from MCP server {self.config.name}",
                    server_name=self.config.name
                )

            response = json.loads(response_line)
            return response

        except asyncio.TimeoutError:
            raise MCPTimeoutError(
                f"Request {method} timed out on {self.config.name}",
                server_name=self.config.name
            )
        except json.JSONDecodeError as e:
            raise MCPError(
                f"Invalid JSON response from {self.config.name}: {e}",
                server_name=self.config.name
            )

    async def _send_notification(self, method: str, params: Dict[str, Any] = None) -> None:
        """Send JSON-RPC notification (no response expected)"""
        if not self.process or self.process.poll() is not None:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method
        }

        if params:
            notification["params"] = params

        try:
            notification_json = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_json)
            self.process.stdin.flush()
        except Exception as e:
            logger.warning(
                f"Failed to send notification to {self.config.name}: {e}")

    async def _read_line(self) -> str:
        """Read a line from the MCP server stdout"""
        if not self.process:
            return ""

        # This is a simplified implementation
        # In production, you'd want proper async I/O handling
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process.stdout.readline)

    async def _cleanup(self) -> None:
        """Clean up resources"""
        self.is_initialized = False
        self.tools_cache.clear()

        if self.process:
            try:
                # Try graceful termination first
                self.process.terminate()

                # Wait for process to exit
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(self._wait_for_process()),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    # Force kill if graceful termination fails
                    self.process.kill()
                    await self._wait_for_process()

            except Exception as e:
                logger.error(
                    f"Error during cleanup of {self.config.name}: {e}")
            finally:
                self.process = None

    async def _wait_for_process(self) -> None:
        """Wait for process to exit"""
        if not self.process:
            return

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.process.wait)


class MCPClientManager:
    """
    Manages multiple MCP clients
    """

    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self._lock = asyncio.Lock()

    async def add_client(self, config: MCPServerConfig) -> bool:
        """Add and initialize a new MCP client"""
        async with self._lock:
            if config.name in self.clients:
                logger.warning(f"MCP client {config.name} already exists")
                return True

            client = MCPClient(config)
            success = await client.initialize(config)

            if success:
                self.clients[config.name] = client
                logger.info(f"Added MCP client: {config.name}")

            return success

    async def remove_client(self, name: str) -> bool:
        """Remove and shutdown an MCP client"""
        async with self._lock:
            if name not in self.clients:
                return True

            client = self.clients[name]
            success = await client.shutdown()

            if success:
                del self.clients[name]
                logger.info(f"Removed MCP client: {name}")

            return success

    def get_client(self, name: str) -> Optional[MCPClient]:
        """Get MCP client by name"""
        return self.clients.get(name)

    async def get_all_health_status(self) -> Dict[str, HealthStatus]:
        """Get health status of all clients"""
        status = {}

        for name, client in self.clients.items():
            try:
                status[name] = await client.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                status[name] = HealthStatus(
                    status=MCPServerStatus.UNHEALTHY,
                    response_time_ms=0,
                    last_check=datetime.now(),
                    error_message=str(e),
                    uptime_percentage=0.0
                )

        return status

    async def shutdown_all(self) -> None:
        """Shutdown all MCP clients"""
        tasks = []
        for client in self.clients.values():
            tasks.append(client.shutdown())

        await asyncio.gather(*tasks, return_exceptions=True)
        self.clients.clear()
        logger.info("All MCP clients shut down")


# Global client manager instance
mcp_client_manager = MCPClientManager()


def get_mcp_client_manager() -> MCPClientManager:
    """Get the global MCP client manager"""
    return mcp_client_manager
