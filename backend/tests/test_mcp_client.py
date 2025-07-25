"""
Tests for MCP Client Implementation

This module contains unit tests for the MCP client functionality.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.mcp_client import MCPClient, MCPClientManager
from app.core.interfaces import (
    MCPServerConfig, MCPServerStatus, MCPError,
    MCPConnectionError, MCPTimeoutError
)


@pytest.fixture
def sample_config():
    """Sample MCP server configuration for testing"""
    return MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-mcp-server"],
        env={"TEST_ENV": "true"},
        timeout=30
    )


@pytest.fixture
def mock_process():
    """Mock subprocess for testing"""
    process = Mock()
    process.poll.return_value = None
    process.stdin = Mock()
    process.stdout = Mock()
    process.stderr = Mock()
    return process


class TestMCPClient:
    """Test cases for MCPClient class"""

    @pytest.mark.asyncio
    async def test_initialization_success(self, sample_config, mock_process):
        """Test successful MCP client initialization"""
        client = MCPClient(sample_config)

        with patch('subprocess.Popen', return_value=mock_process):
            # Mock successful initialization response
            mock_process.stdout.readline.return_value = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {}
                }
            }) + "\n"

            result = await client.initialize(sample_config)
            assert result is True
            assert client.is_initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self, sample_config):
        """Test MCP client initialization failure"""
        client = MCPClient(sample_config)

        with patch('subprocess.Popen') as mock_popen:
            # Mock process that fails to start
            mock_process = Mock()
            mock_process.poll.return_value = 1  # Process exited
            mock_process.communicate.return_value = (
                "", "Error starting server")
            mock_popen.return_value = mock_process

            with pytest.raises(MCPConnectionError):
                await client.initialize(sample_config)

    @pytest.mark.asyncio
    async def test_tool_call_success(self, sample_config, mock_process):
        """Test successful tool call"""
        client = MCPClient(sample_config)
        client.is_initialized = True
        client.process = mock_process

        # Mock successful tool call response
        mock_process.stdout.readline.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [{"type": "text", "text": "Tool executed successfully"}]
            }
        }) + "\n"

        result = await client.call_tool("test_tool", {"param": "value"})
        assert "content" in result
        assert result["content"][0]["text"] == "Tool executed successfully"

    @pytest.mark.asyncio
    async def test_tool_call_error(self, sample_config, mock_process):
        """Test tool call with error response"""
        client = MCPClient(sample_config)
        client.is_initialized = True
        client.process = mock_process

        # Mock error response
        mock_process.stdout.readline.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -1,
                "message": "Tool not found"
            }
        }) + "\n"

        with pytest.raises(MCPError) as exc_info:
            await client.call_tool("nonexistent_tool", {})

        assert "Tool not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, sample_config, mock_process):
        """Test health check for healthy server"""
        client = MCPClient(sample_config)
        client.process = mock_process

        # Mock ping response
        mock_process.stdout.readline.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "ok"}
        }) + "\n"

        health = await client.health_check()
        assert health.status == MCPServerStatus.HEALTHY
        assert health.response_time_ms > 0

    @pytest.mark.asyncio
    async def test_health_check_offline(self, sample_config):
        """Test health check for offline server"""
        client = MCPClient(sample_config)
        client.process = None

        health = await client.health_check()
        assert health.status == MCPServerStatus.OFFLINE
        assert health.response_time_ms == 0

    @pytest.mark.asyncio
    async def test_list_tools(self, sample_config, mock_process):
        """Test listing available tools"""
        client = MCPClient(sample_config)
        client.is_initialized = True
        client.process = mock_process

        # Mock tools list response
        mock_process.stdout.readline.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"param": {"type": "string"}},
                            "required": ["param"]
                        }
                    }
                ]
            }
        }) + "\n"

        tools = await client.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        assert tools[0].description == "A test tool"

    @pytest.mark.asyncio
    async def test_shutdown(self, sample_config, mock_process):
        """Test graceful shutdown"""
        client = MCPClient(sample_config)
        client.is_initialized = True
        client.process = mock_process

        result = await client.shutdown()
        assert result is True
        assert client.is_initialized is False


class TestMCPClientManager:
    """Test cases for MCPClientManager class"""

    @pytest.mark.asyncio
    async def test_add_client_success(self, sample_config):
        """Test adding a client successfully"""
        manager = MCPClientManager()

        with patch.object(MCPClient, 'initialize', return_value=True):
            result = await manager.add_client(sample_config)
            assert result is True
            assert sample_config.name in manager.clients

    @pytest.mark.asyncio
    async def test_add_client_failure(self, sample_config):
        """Test adding a client that fails to initialize"""
        manager = MCPClientManager()

        with patch.object(MCPClient, 'initialize', return_value=False):
            result = await manager.add_client(sample_config)
            assert result is False
            assert sample_config.name not in manager.clients

    @pytest.mark.asyncio
    async def test_remove_client(self, sample_config):
        """Test removing a client"""
        manager = MCPClientManager()

        # Add client first
        with patch.object(MCPClient, 'initialize', return_value=True):
            await manager.add_client(sample_config)

        # Remove client
        with patch.object(MCPClient, 'shutdown', return_value=True):
            result = await manager.remove_client(sample_config.name)
            assert result is True
            assert sample_config.name not in manager.clients

    @pytest.mark.asyncio
    async def test_get_all_health_status(self, sample_config):
        """Test getting health status of all clients"""
        manager = MCPClientManager()

        # Add client
        with patch.object(MCPClient, 'initialize', return_value=True):
            await manager.add_client(sample_config)

        # Mock health check
        mock_health = Mock()
        mock_health.status = MCPServerStatus.HEALTHY
        mock_health.response_time_ms = 100.0
        mock_health.last_check = datetime.now()
        mock_health.uptime_percentage = 95.0

        with patch.object(MCPClient, 'health_check', return_value=mock_health):
            statuses = await manager.get_all_health_status()
            assert sample_config.name in statuses
            assert statuses[sample_config.name].status == MCPServerStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_shutdown_all(self, sample_config):
        """Test shutting down all clients"""
        manager = MCPClientManager()

        # Add multiple clients
        configs = [
            sample_config,
            MCPServerConfig(name="test-server-2",
                            command="uvx", args=["test-2"])
        ]

        with patch.object(MCPClient, 'initialize', return_value=True):
            for config in configs:
                await manager.add_client(config)

        # Shutdown all
        with patch.object(MCPClient, 'shutdown', return_value=True):
            await manager.shutdown_all()
            assert len(manager.clients) == 0


@pytest.mark.asyncio
async def test_connection_retry_logic(sample_config):
    """Test connection retry logic with exponential backoff"""
    client = MCPClient(sample_config)
    client.is_initialized = True
    client.process = Mock()
    client.process.poll.return_value = None

    # Mock timeout on first two calls, success on third
    call_count = 0

    def mock_readline():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise asyncio.TimeoutError()
        return json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "ok"}
        }) + "\n"

    client.process.stdout.readline.side_effect = mock_readline

    # Should succeed after retries
    result = await client.call_tool("test_tool", {})
    assert "status" in result
    assert call_count == 3


@pytest.mark.asyncio
async def test_json_rpc_protocol_compliance():
    """Test JSON-RPC protocol compliance"""
    config = MCPServerConfig(
        name="protocol-test",
        command="uvx",
        args=["test-server"]
    )

    client = MCPClient(config)

    # Test request format
    request_data = None

    def capture_request(data):
        nonlocal request_data
        request_data = json.loads(data.strip())

    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.stdin.write.side_effect = capture_request
    mock_process.stdout.readline.return_value = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {}
    }) + "\n"

    client.process = mock_process
    client.is_initialized = True

    await client.call_tool("test_tool", {"param": "value"})

    # Verify JSON-RPC format
    assert request_data["jsonrpc"] == "2.0"
    assert "id" in request_data
    assert request_data["method"] == "tools/call"
    assert request_data["params"]["name"] == "test_tool"
    assert request_data["params"]["arguments"]["param"] == "value"
