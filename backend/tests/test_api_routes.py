"""
Tests for API Routes

This module contains tests for the API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.main import app
from app.core.interfaces import HealthStatus, MCPServerStatus, ToolDefinition


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_health_monitor():
    """Mock health monitor"""
    monitor = Mock()
    monitor.get_all_statuses = AsyncMock()
    monitor.get_server_status = AsyncMock()
    monitor.force_restart_server = AsyncMock()
    monitor.get_all_metrics = Mock()
    return monitor


@pytest.fixture
def mock_config_manager():
    """Mock config manager"""
    manager = Mock()
    manager.list_configurations = Mock()
    manager.get_configuration = Mock()
    manager.update_configuration = AsyncMock()
    manager.save_configuration = AsyncMock()
    manager.delete_configuration = AsyncMock()
    return manager


@pytest.fixture
def mock_client_manager():
    """Mock MCP client manager"""
    manager = Mock()
    manager.get_client = Mock()
    return manager


class TestMCPStatusEndpoints:
    """Test MCP status API endpoints"""

    @patch('app.api.routes.get_health_monitor')
    def test_get_mcp_status_success(self, mock_get_monitor, client, mock_health_monitor):
        """Test successful MCP status retrieval"""
        mock_get_monitor.return_value = mock_health_monitor

        mock_statuses = {
            "test-server": HealthStatus(
                status=MCPServerStatus.HEALTHY,
                response_time_ms=100.0,
                last_check=datetime.now(),
                uptime_percentage=95.0
            )
        }
        mock_health_monitor.get_all_statuses.return_value = mock_statuses

        response = client.get("/api/v1/mcp/status")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test-server" in data["data"]

    @patch('app.api.routes.get_health_monitor')
    def test_get_server_status_success(self, mock_get_monitor, client, mock_health_monitor):
        """Test successful individual server status retrieval"""
        mock_get_monitor.return_value = mock_health_monitor

        mock_status = HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=100.0,
            last_check=datetime.now(),
            uptime_percentage=95.0
        )
        mock_health_monitor.get_server_status.return_value = mock_status

        response = client.get("/api/v1/mcp/status/test-server")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"

    @patch('app.api.routes.get_mcp_client_manager')
    def test_get_server_tools_success(self, mock_get_client_manager, client, mock_client_manager):
        """Test successful server tools retrieval"""
        mock_get_client_manager.return_value = mock_client_manager

        mock_client = Mock()
        mock_tools = [
            ToolDefinition(
                name="test_tool",
                description="A test tool",
                parameters={"param": {"type": "string"}},
                required_parameters=["param"]
            )
        ]
        mock_client.list_tools = AsyncMock(return_value=mock_tools)
        mock_client_manager.get_client.return_value = mock_client

        response = client.get("/api/v1/mcp/tools/test-server")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "test_tool"

    @patch('app.api.routes.get_mcp_client_manager')
    def test_get_server_tools_not_found(self, mock_get_client_manager, client, mock_client_manager):
        """Test server tools retrieval when server not found"""
        mock_get_client_manager.return_value = mock_client_manager
        mock_client_manager.get_client.return_value = None

        response = client.get("/api/v1/mcp/tools/nonexistent-server")

        assert response.status_code == 404

    @patch('app.api.routes.get_health_monitor')
    def test_restart_server_success(self, mock_get_monitor, client, mock_health_monitor):
        """Test successful server restart"""
        mock_get_monitor.return_value = mock_health_monitor
        mock_health_monitor.force_restart_server.return_value = True

        response = client.post("/api/v1/mcp/restart/test-server")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "restarted successfully" in data["data"]["message"]

    @patch('app.api.routes.get_health_monitor')
    def test_restart_server_failure(self, mock_get_monitor, client, mock_health_monitor):
        """Test failed server restart"""
        mock_get_monitor.return_value = mock_health_monitor
        mock_health_monitor.force_restart_server.return_value = False

        response = client.post("/api/v1/mcp/restart/test-server")

        assert response.status_code == 400

    @patch('app.api.routes.get_health_monitor')
    def test_get_mcp_metrics_success(self, mock_get_monitor, client, mock_health_monitor):
        """Test successful MCP metrics retrieval"""
        mock_get_monitor.return_value = mock_health_monitor

        mock_metrics = Mock()
        mock_metrics.total_checks = 100
        mock_metrics.total_failures = 5
        mock_metrics.consecutive_failures = 0
        mock_metrics.get_uptime_percentage.return_value = 95.0
        mock_metrics.get_average_response_time.return_value = 150.0
        mock_metrics.get_p95_response_time.return_value = 300.0
        mock_metrics.restart_count = 1
        mock_metrics.last_successful_check = datetime.now()
        mock_metrics.last_failed_check = None

        mock_health_monitor.get_all_metrics.return_value = {
            "test-server": mock_metrics
        }

        response = client.get("/api/v1/mcp/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test-server" in data["data"]
        assert data["data"]["test-server"]["total_checks"] == 100


class TestConfigurationEndpoints:
    """Test configuration management API endpoints"""

    @patch('app.api.routes.get_config_manager')
    def test_list_server_configs_success(self, mock_get_config_manager, client, mock_config_manager):
        """Test successful server configurations listing"""
        mock_get_config_manager.return_value = mock_config_manager

        from app.core.interfaces import MCPServerConfig
        mock_configs = [
            MCPServerConfig(
                name="test-server",
                command="uvx",
                args=["test-server"],
                timeout=30
            )
        ]
        mock_config_manager.list_configurations.return_value = mock_configs

        response = client.get("/api/v1/config/servers")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "test-server"

    @patch('app.api.routes.get_config_manager')
    def test_get_server_config_success(self, mock_get_config_manager, client, mock_config_manager):
        """Test successful individual server configuration retrieval"""
        mock_get_config_manager.return_value = mock_config_manager

        from app.core.interfaces import MCPServerConfig
        mock_config = MCPServerConfig(
            name="test-server",
            command="uvx",
            args=["test-server"],
            timeout=30
        )
        mock_config_manager.get_configuration.return_value = mock_config

        response = client.get("/api/v1/config/servers/test-server")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "test-server"

    @patch('app.api.routes.get_config_manager')
    def test_get_server_config_not_found(self, mock_get_config_manager, client, mock_config_manager):
        """Test server configuration retrieval when not found"""
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.get_configuration.return_value = None

        response = client.get("/api/v1/config/servers/nonexistent-server")

        assert response.status_code == 404

    @patch('app.api.routes.get_config_manager')
    def test_update_server_config_success(self, mock_get_config_manager, client, mock_config_manager):
        """Test successful server configuration update"""
        mock_get_config_manager.return_value = mock_config_manager

        from app.core.interfaces import MCPServerConfig
        updated_config = MCPServerConfig(
            name="test-server",
            command="uvx",
            args=["test-server"],
            timeout=60  # Updated timeout
        )
        mock_config_manager.update_configuration.return_value = updated_config

        updates = {"timeout": 60}
        response = client.put(
            "/api/v1/config/servers/test-server", json=updates)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["timeout"] == 60

    @patch('app.api.routes.get_config_manager')
    def test_create_server_config_success(self, mock_get_config_manager, client, mock_config_manager):
        """Test successful server configuration creation"""
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.save_configuration.return_value = None

        config_data = {
            "name": "new-server",
            "command": "uvx",
            "args": ["new-server"],
            "timeout": 30
        }

        response = client.post("/api/v1/config/servers", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "new-server"

    @patch('app.api.routes.get_config_manager')
    def test_delete_server_config_success(self, mock_get_config_manager, client, mock_config_manager):
        """Test successful server configuration deletion"""
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.delete_configuration.return_value = True

        response = client.delete("/api/v1/config/servers/test-server")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["data"]["message"]

    @patch('app.api.routes.get_config_manager')
    def test_delete_server_config_not_found(self, mock_get_config_manager, client, mock_config_manager):
        """Test server configuration deletion when not found"""
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.delete_configuration.return_value = False

        response = client.delete("/api/v1/config/servers/nonexistent-server")

        assert response.status_code == 404


class TestToolExecutionEndpoints:
    """Test tool execution API endpoints"""

    @patch('app.api.routes.get_mcp_client_manager')
    def test_execute_tool_success(self, mock_get_client_manager, client, mock_client_manager):
        """Test successful tool execution"""
        mock_get_client_manager.return_value = mock_client_manager

        mock_client = Mock()
        mock_result = {"output": "Tool executed successfully"}
        mock_client.call_tool = AsyncMock(return_value=mock_result)
        mock_client_manager.get_client.return_value = mock_client

        arguments = {"param": "value"}
        response = client.post(
            "/api/v1/tools/execute/test-server/test-tool",
            json=arguments
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["output"] == "Tool executed successfully"

    @patch('app.api.routes.get_mcp_client_manager')
    def test_execute_tool_server_not_found(self, mock_get_client_manager, client, mock_client_manager):
        """Test tool execution when server not found"""
        mock_get_client_manager.return_value = mock_client_manager
        mock_client_manager.get_client.return_value = None

        arguments = {"param": "value"}
        response = client.post(
            "/api/v1/tools/execute/nonexistent-server/test-tool",
            json=arguments
        )

        assert response.status_code == 404


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "name" in data["data"]
