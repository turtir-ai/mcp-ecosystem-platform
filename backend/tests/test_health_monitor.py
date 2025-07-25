"""
Tests for Health Monitor System

This module contains unit tests for the health monitoring functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.services.health_monitor import HealthMonitor, HealthMetrics
from app.core.interfaces import (
    MCPServerConfig, HealthStatus, MCPServerStatus
)


@pytest.fixture
def sample_config():
    """Sample MCP server configuration"""
    return MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-mcp-server"],
        timeout=30,
        auto_restart=True
    )


@pytest.fixture
def mock_client_manager():
    """Mock MCP client manager"""
    manager = Mock()
    manager.get_client = Mock()
    manager.add_client = AsyncMock(return_value=True)
    manager.remove_client = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_config_manager():
    """Mock configuration manager"""
    manager = Mock()
    manager.load_configurations = AsyncMock(return_value={})
    manager.list_configurations = Mock(return_value=[])
    manager.get_configuration = Mock(return_value=None)
    return manager


class TestHealthMetrics:
    """Test cases for HealthMetrics class"""

    def test_initialization(self):
        """Test health metrics initialization"""
        metrics = HealthMetrics("test-server")

        assert metrics.server_name == "test-server"
        assert len(metrics.response_times) == 0
        assert len(metrics.uptime_checks) == 0
        assert metrics.consecutive_failures == 0
        assert metrics.total_checks == 0
        assert metrics.total_failures == 0

    def test_add_successful_check(self):
        """Test adding successful health check result"""
        metrics = HealthMetrics("test-server")

        metrics.add_check_result(True, 100.0)

        assert metrics.total_checks == 1
        assert metrics.total_failures == 0
        assert metrics.consecutive_failures == 0
        assert len(metrics.response_times) == 1
        assert metrics.response_times[0] == 100.0
        assert metrics.last_successful_check is not None

    def test_add_failed_check(self):
        """Test adding failed health check result"""
        metrics = HealthMetrics("test-server")

        metrics.add_check_result(False)

        assert metrics.total_checks == 1
        assert metrics.total_failures == 1
        assert metrics.consecutive_failures == 1
        assert len(metrics.response_times) == 0
        assert metrics.last_failed_check is not None

    def test_uptime_percentage_calculation(self):
        """Test uptime percentage calculation"""
        metrics = HealthMetrics("test-server")

        # Add mixed results
        metrics.add_check_result(True, 100.0)
        metrics.add_check_result(True, 150.0)
        metrics.add_check_result(False)
        metrics.add_check_result(True, 120.0)

        uptime = metrics.get_uptime_percentage()
        assert uptime == 75.0  # 3 out of 4 successful

    def test_average_response_time(self):
        """Test average response time calculation"""
        metrics = HealthMetrics("test-server")

        metrics.add_check_result(True, 100.0)
        metrics.add_check_result(True, 200.0)
        metrics.add_check_result(True, 150.0)

        avg_time = metrics.get_average_response_time()
        assert avg_time == 150.0

    def test_p95_response_time(self):
        """Test 95th percentile response time calculation"""
        metrics = HealthMetrics("test-server")

        # Add 20 response times
        for i in range(20):
            metrics.add_check_result(True, i * 10.0)

        p95_time = metrics.get_p95_response_time()
        assert p95_time == 180.0  # 95th percentile of 0-190


class TestHealthMonitor:
    """Test cases for HealthMonitor class"""

    def test_initialization(self, mock_client_manager, mock_config_manager):
        """Test health monitor initialization"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        assert monitor.client_manager == mock_client_manager
        assert monitor.config_manager == mock_config_manager
        assert not monitor.is_monitoring
        assert monitor.monitoring_task is None
        assert len(monitor.metrics) == 0

    @pytest.mark.asyncio
    async def test_start_monitoring(self, mock_client_manager, mock_config_manager, sample_config):
        """Test starting health monitoring"""
        mock_config_manager.load_configurations.return_value = {
            sample_config.name: sample_config
        }

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        await monitor.start_monitoring()

        assert monitor.is_monitoring
        assert monitor.monitoring_task is not None
        assert sample_config.name in monitor.metrics

        # Clean up
        await monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, mock_client_manager, mock_config_manager):
        """Test stopping health monitoring"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        monitor.is_monitoring = True
        monitor.monitoring_task = Mock()
        monitor.monitoring_task.cancel = Mock()

        await monitor.stop_monitoring()

        assert not monitor.is_monitoring
        monitor.monitoring_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_server_status_healthy(self, mock_client_manager, mock_config_manager):
        """Test getting status of healthy server"""
        mock_client = Mock()
        mock_client.health_check = AsyncMock(return_value=HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=100.0,
            last_check=datetime.now(),
            uptime_percentage=95.0
        ))
        mock_client_manager.get_client.return_value = mock_client

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        monitor.metrics["test-server"] = HealthMetrics("test-server")

        status = await monitor.get_server_status("test-server")

        assert status.status == MCPServerStatus.HEALTHY
        assert status.response_time_ms == 100.0

    @pytest.mark.asyncio
    async def test_get_server_status_client_not_found(self, mock_client_manager, mock_config_manager):
        """Test getting status when client not found"""
        mock_client_manager.get_client.return_value = None

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        status = await monitor.get_server_status("nonexistent-server")

        assert status.status == MCPServerStatus.OFFLINE
        assert status.error_message == "Client not found"

    @pytest.mark.asyncio
    async def test_get_all_statuses(self, mock_client_manager, mock_config_manager, sample_config):
        """Test getting status of all servers"""
        mock_config_manager.list_configurations.return_value = [sample_config]

        mock_client = Mock()
        mock_client.health_check = AsyncMock(return_value=HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=100.0,
            last_check=datetime.now(),
            uptime_percentage=95.0
        ))
        mock_client_manager.get_client.return_value = mock_client

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        monitor.metrics[sample_config.name] = HealthMetrics(sample_config.name)

        statuses = await monitor.get_all_statuses()

        assert len(statuses) == 1
        assert sample_config.name in statuses
        assert statuses[sample_config.name].status == MCPServerStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_register_server_success(self, mock_client_manager, mock_config_manager, sample_config):
        """Test successful server registration"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        result = await monitor.register_server(sample_config)

        assert result is True
        assert sample_config.name in monitor.metrics
        mock_client_manager.add_client.assert_called_once_with(sample_config)

    @pytest.mark.asyncio
    async def test_register_server_failure(self, mock_client_manager, mock_config_manager, sample_config):
        """Test failed server registration"""
        mock_client_manager.add_client.return_value = False

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        result = await monitor.register_server(sample_config)

        assert result is False

    @pytest.mark.asyncio
    async def test_unregister_server(self, mock_client_manager, mock_config_manager, sample_config):
        """Test server unregistration"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        monitor.metrics[sample_config.name] = HealthMetrics(sample_config.name)
        monitor.last_restart_times[sample_config.name] = datetime.now()

        result = await monitor.unregister_server(sample_config.name)

        assert result is True
        assert sample_config.name not in monitor.metrics
        assert sample_config.name not in monitor.last_restart_times
        mock_client_manager.remove_client.assert_called_once_with(
            sample_config.name)

    def test_add_alert_callback(self, mock_client_manager, mock_config_manager):
        """Test adding alert callback"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        def test_callback(server_name, status):
            pass

        monitor.add_alert_callback(test_callback)

        assert test_callback in monitor.alert_callbacks

    def test_remove_alert_callback(self, mock_client_manager, mock_config_manager):
        """Test removing alert callback"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        def test_callback(server_name, status):
            pass

        monitor.add_alert_callback(test_callback)
        monitor.remove_alert_callback(test_callback)

        assert test_callback not in monitor.alert_callbacks

    def test_should_restart_server_auto_restart_disabled(self, mock_client_manager, mock_config_manager):
        """Test restart decision when auto restart is disabled"""
        config = MCPServerConfig(
            name="test-server",
            command="uvx",
            args=["test"],
            auto_restart=False
        )

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        metrics = HealthMetrics("test-server")
        metrics.consecutive_failures = 5

        should_restart = monitor._should_restart_server(config, metrics)

        assert should_restart is False

    def test_should_restart_server_below_threshold(self, mock_client_manager, mock_config_manager):
        """Test restart decision when failures below threshold"""
        config = MCPServerConfig(
            name="test-server",
            command="uvx",
            args=["test"],
            auto_restart=True
        )

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        metrics = HealthMetrics("test-server")
        metrics.consecutive_failures = 2  # Below default threshold of 3

        should_restart = monitor._should_restart_server(config, metrics)

        assert should_restart is False

    def test_should_restart_server_cooldown_active(self, mock_client_manager, mock_config_manager):
        """Test restart decision when cooldown is active"""
        config = MCPServerConfig(
            name="test-server",
            command="uvx",
            args=["test"],
            auto_restart=True
        )

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        metrics = HealthMetrics("test-server")
        metrics.consecutive_failures = 5

        # Set recent restart time
        monitor.last_restart_times["test-server"] = datetime.now() - \
            timedelta(seconds=60)

        should_restart = monitor._should_restart_server(config, metrics)

        assert should_restart is False

    def test_should_restart_server_conditions_met(self, mock_client_manager, mock_config_manager):
        """Test restart decision when all conditions are met"""
        config = MCPServerConfig(
            name="test-server",
            command="uvx",
            args=["test"],
            auto_restart=True
        )

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        metrics = HealthMetrics("test-server")
        metrics.consecutive_failures = 5

        should_restart = monitor._should_restart_server(config, metrics)

        assert should_restart is True

    @pytest.mark.asyncio
    async def test_restart_server_success(self, mock_client_manager, mock_config_manager, sample_config):
        """Test successful server restart"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        monitor.metrics[sample_config.name] = HealthMetrics(sample_config.name)
        monitor.metrics[sample_config.name].consecutive_failures = 5

        await monitor._restart_server(sample_config)

        mock_client_manager.remove_client.assert_called_once_with(
            sample_config.name)
        mock_client_manager.add_client.assert_called_once_with(sample_config)

        assert monitor.metrics[sample_config.name].restart_count == 1
        assert monitor.metrics[sample_config.name].consecutive_failures == 0
        assert sample_config.name in monitor.last_restart_times

    @pytest.mark.asyncio
    async def test_force_restart_server(self, mock_client_manager, mock_config_manager, sample_config):
        """Test force restarting a server"""
        mock_config_manager.get_configuration.return_value = sample_config

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        monitor.metrics[sample_config.name] = HealthMetrics(sample_config.name)

        with patch.object(monitor, '_restart_server') as mock_restart:
            result = await monitor.force_restart_server(sample_config.name)

        assert result is True
        mock_restart.assert_called_once_with(sample_config)

    @pytest.mark.asyncio
    async def test_force_restart_server_not_found(self, mock_client_manager, mock_config_manager):
        """Test force restarting a server that doesn't exist"""
        mock_config_manager.get_configuration.return_value = None

        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        result = await monitor.force_restart_server("nonexistent")

        assert result is False

    def test_set_check_interval(self, mock_client_manager, mock_config_manager):
        """Test setting check interval"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        monitor.set_check_interval(60)

        assert monitor.check_interval == 60

    def test_set_check_interval_invalid(self, mock_client_manager, mock_config_manager):
        """Test setting invalid check interval"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        with pytest.raises(ValueError):
            monitor.set_check_interval(3)

    def test_set_failure_threshold(self, mock_client_manager, mock_config_manager):
        """Test setting failure threshold"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        monitor.set_failure_threshold(5)

        assert monitor.failure_threshold == 5

    def test_set_failure_threshold_invalid(self, mock_client_manager, mock_config_manager):
        """Test setting invalid failure threshold"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        with pytest.raises(ValueError):
            monitor.set_failure_threshold(0)

    def test_set_restart_cooldown(self, mock_client_manager, mock_config_manager):
        """Test setting restart cooldown"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        monitor.set_restart_cooldown(600)

        assert monitor.restart_cooldown == 600

    def test_set_restart_cooldown_invalid(self, mock_client_manager, mock_config_manager):
        """Test setting invalid restart cooldown"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        with pytest.raises(ValueError):
            monitor.set_restart_cooldown(30)

    def test_get_server_metrics(self, mock_client_manager, mock_config_manager):
        """Test getting server metrics"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        metrics = HealthMetrics("test-server")
        monitor.metrics["test-server"] = metrics

        retrieved_metrics = monitor.get_server_metrics("test-server")

        assert retrieved_metrics == metrics

    def test_get_all_metrics(self, mock_client_manager, mock_config_manager):
        """Test getting all server metrics"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)
        metrics1 = HealthMetrics("server1")
        metrics2 = HealthMetrics("server2")
        monitor.metrics["server1"] = metrics1
        monitor.metrics["server2"] = metrics2

        all_metrics = monitor.get_all_metrics()

        assert len(all_metrics) == 2
        assert all_metrics["server1"] == metrics1
        assert all_metrics["server2"] == metrics2

    @pytest.mark.asyncio
    async def test_check_and_send_alerts_offline(self, mock_client_manager, mock_config_manager):
        """Test alert sending for offline server"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        alert_called = False

        def test_callback(server_name, status):
            nonlocal alert_called
            alert_called = True
            assert server_name == "test-server"
            assert status.status == MCPServerStatus.OFFLINE

        monitor.add_alert_callback(test_callback)

        status = HealthStatus(
            status=MCPServerStatus.OFFLINE,
            response_time_ms=0.0,
            last_check=datetime.now(),
            uptime_percentage=0.0
        )

        await monitor._check_and_send_alerts("test-server", status)

        assert alert_called

    @pytest.mark.asyncio
    async def test_check_and_send_alerts_slow_response(self, mock_client_manager, mock_config_manager):
        """Test alert sending for slow response"""
        monitor = HealthMonitor(mock_client_manager, mock_config_manager)

        alert_called = False

        def test_callback(server_name, status):
            nonlocal alert_called
            alert_called = True
            assert status.response_time_ms > 5000

        monitor.add_alert_callback(test_callback)

        status = HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=6000.0,  # 6 seconds
            last_check=datetime.now(),
            uptime_percentage=95.0
        )

        await monitor._check_and_send_alerts("test-server", status)

        assert alert_called
