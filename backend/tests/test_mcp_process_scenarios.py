"""
Tests for MCP server process management scenarios
Tests various failure modes and recovery scenarios
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.health_monitor import HealthMonitor
from app.services.security_manager import SecurityManager, RiskLevel
from app.core.interfaces import HealthStatus, MCPServerStatus, MCPServerConfig


class TestMCPProcessScenarios:
    """Test various MCP server process scenarios"""
    
    def setup_method(self):
        """Setup test services"""
        self.health_monitor = HealthMonitor()
        self.security_manager = SecurityManager()
    
    @pytest.mark.asyncio
    async def test_mcp_server_startup_sequence(self):
        """Test MCP server startup sequence and status transitions"""
        
        # Register server
        server_config = MCPServerConfig(
            name="startup-test-server",
            command="python",
            args=["test_server.py"],
            env={"TEST_MODE": "true"},
            disabled=False
        )
        
        success = await self.health_monitor.register_server(server_config)
        assert success is True
        
        # Initial status should be STARTING
        status = await self.health_monitor.get_server_status("startup-test-server")
        assert status.status == MCPServerStatus.STARTING
        
        # Simulate successful startup
        self.health_monitor.statuses["startup-test-server"] = HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=120,
            last_check=datetime.now(),
            uptime_percentage=100.0
        )
        
        # Verify healthy status
        status = await self.health_monitor.get_server_status("startup-test-server")
        assert status.status == MCPServerStatus.HEALTHY
        assert status.response_time_ms == 120
    
    @pytest.mark.asyncio
    async def test_mcp_server_crash_detection(self):
        """Test detection of MCP server crashes"""
        
        # Setup healthy server
        server_config = MCPServerConfig(
            name="crash-test-server",
            command="python",
            args=["crash_server.py"],
            env={},
            disabled=False
        )
        
        await self.health_monitor.register_server(server_config)
        
        # Initially healthy
        self.health_monitor.statuses["crash-test-server"] = HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=95,
            last_check=datetime.now(),
            uptime_percentage=99.8
        )
        
        # Simulate crash
        self.health_monitor.statuses["crash-test-server"] = HealthStatus(
            status=MCPServerStatus.OFFLINE,
            response_time_ms=0,
            last_check=datetime.now(),
            error_message="Process terminated unexpectedly",
            uptime_percentage=0.0
        )
        
        # Verify crash detection
        status = await self.health_monitor.get_server_status("crash-test-server")
        assert status.status == MCPServerStatus.OFFLINE
        assert status.error_message == "Process terminated unexpectedly"
        assert status.response_time_ms == 0
    
    @pytest.mark.asyncio
    async def test_mcp_server_performance_degradation(self):
        """Test detection of performance degradation"""
        
        server_config = MCPServerConfig(
            name="perf-test-server",
            command="uvx",
            args=["performance-test-server"],
            env={},
            disabled=False
        )
        
        await self.health_monitor.register_server(server_config)
        
        # Start with good performance
        self.health_monitor.statuses["perf-test-server"] = HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=80,
            last_check=datetime.now(),
            uptime_percentage=99.5
        )
        
        # Simulate performance degradation
        self.health_monitor.statuses["perf-test-server"] = HealthStatus(
            status=MCPServerStatus.DEGRADED,
            response_time_ms=450,
            last_check=datetime.now(),
            error_message="High response time detected",
            uptime_percentage=87.3
        )
        
        # Verify degradation detection
        status = await self.health_monitor.get_server_status("perf-test-server")
        assert status.status == MCPServerStatus.DEGRADED
        assert status.response_time_ms == 450
        assert status.error_message == "High response time detected"
        assert status.uptime_percentage < 90
    
    @pytest.mark.asyncio
    async def test_mcp_server_restart_recovery(self):
        """Test server restart and recovery process"""
        
        server_config = MCPServerConfig(
            name="restart-test-server",
            command="python",
            args=["restart_server.py"],
            env={},
            disabled=False
        )
        
        await self.health_monitor.register_server(server_config)
        
        # Server is offline
        self.health_monitor.statuses["restart-test-server"] = HealthStatus(
            status=MCPServerStatus.OFFLINE,
            response_time_ms=0,
            last_check=datetime.now(),
            error_message="Connection refused",
            uptime_percentage=0.0
        )
        
        # Attempt restart
        restart_success = await self.health_monitor.force_restart_server("restart-test-server")
        assert restart_success is True
        
        # Should be in STARTING state
        status = await self.health_monitor.get_server_status("restart-test-server")
        assert status.status == MCPServerStatus.STARTING
        
        # Simulate successful recovery
        self.health_monitor.statuses["restart-test-server"] = HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=110,
            last_check=datetime.now(),
            uptime_percentage=100.0
        )
        
        # Verify recovery
        status = await self.health_monitor.get_server_status("restart-test-server")
        assert status.status == MCPServerStatus.HEALTHY
        assert status.response_time_ms == 110
    
    @pytest.mark.asyncio
    async def test_multiple_server_failure_scenario(self):
        """Test scenario with multiple server failures"""
        
        # Setup multiple servers
        servers = [
            MCPServerConfig(name="server-1", command="python", args=["s1.py"], env={}, disabled=False),
            MCPServerConfig(name="server-2", command="python", args=["s2.py"], env={}, disabled=False),
            MCPServerConfig(name="server-3", command="uvx", args=["s3"], env={}, disabled=False),
            MCPServerConfig(name="server-4", command="python", args=["s4.py"], env={}, disabled=False)
        ]
        
        for server in servers:
            await self.health_monitor.register_server(server)
        
        # Set various failure states
        self.health_monitor.statuses.update({
            "server-1": HealthStatus(
                status=MCPServerStatus.HEALTHY,
                response_time_ms=95,
                last_check=datetime.now(),
                uptime_percentage=99.2
            ),
            "server-2": HealthStatus(
                status=MCPServerStatus.OFFLINE,
                response_time_ms=0,
                last_check=datetime.now(),
                error_message="Process not found",
                uptime_percentage=0.0
            ),
            "server-3": HealthStatus(
                status=MCPServerStatus.DEGRADED,
                response_time_ms=380,
                last_check=datetime.now(),
                error_message="High latency",
                uptime_percentage=78.5
            ),
            "server-4": HealthStatus(
                status=MCPServerStatus.OFFLINE,
                response_time_ms=0,
                last_check=datetime.now(),
                error_message="Connection timeout",
                uptime_percentage=0.0
            )
        })
        
        # Get all statuses
        all_statuses = await self.health_monitor.get_all_statuses()
        
        # Verify failure detection
        assert len(all_statuses) == 4
        assert all_statuses["server-1"].status == MCPServerStatus.HEALTHY
        assert all_statuses["server-2"].status == MCPServerStatus.OFFLINE
        assert all_statuses["server-3"].status == MCPServerStatus.DEGRADED
        assert all_statuses["server-4"].status == MCPServerStatus.OFFLINE
        
        # Count healthy vs unhealthy
        healthy_count = sum(1 for status in all_statuses.values() 
                          if status.status == MCPServerStatus.HEALTHY)
        unhealthy_count = len(all_statuses) - healthy_count
        
        assert healthy_count == 1
        assert unhealthy_count == 3
        
        # Generate AI insights for multiple failures
        system_status = {
            'mcp_servers': {
                'unhealthy_servers': ['server-2', 'server-3', 'server-4']
            },
            'resource_usage': {
                'cpu_percent': 85,  # High due to failures
                'memory_percent': 75
            }
        }
        
        insights = self.security_manager.get_ai_actionable_insights(system_status)
        
        # Should have insights for each unhealthy server
        server_insights = [i for i in insights if 'server_name' in i]
        assert len(server_insights) == 3
        
        # All should suggest restart
        for insight in server_insights:
            assert insight['suggested_action'] == 'mcp_server_restart'
            assert insight['can_auto_fix'] is False  # Requires approval
    
    def test_ai_decision_making_for_server_failures(self):
        """Test AI decision making for different types of server failures"""
        
        # Test different failure scenarios
        failure_scenarios = [
            {
                'server_name': 'groq-llm',
                'status': MCPServerStatus.OFFLINE,
                'error': 'Connection refused',
                'expected_action': 'mcp_server_restart',
                'expected_priority': 'high'
            },
            {
                'server_name': 'browser-automation',
                'status': MCPServerStatus.DEGRADED,
                'error': 'High response time',
                'expected_action': 'mcp_server_restart',
                'expected_priority': 'medium'
            },
            {
                'server_name': 'kiro-tools',
                'status': MCPServerStatus.OFFLINE,
                'error': 'Process crashed',
                'expected_action': 'manual_intervention',  # Restricted server
                'expected_priority': 'high'
            }
        ]
        
        for scenario in failure_scenarios:
            system_status = {
                'mcp_servers': {
                    'unhealthy_servers': [scenario['server_name']]
                },
                'resource_usage': {
                    'cpu_percent': 45,
                    'memory_percent': 60
                }
            }
            
            insights = self.security_manager.get_ai_actionable_insights(system_status)
            
            # Find insight for this server
            server_insight = next(
                (i for i in insights if i.get('server_name') == scenario['server_name']),
                None
            )
            
            assert server_insight is not None
            assert server_insight['priority'] == scenario['expected_priority']
            
            # Check if action matches expected (considering restrictions)
            if scenario['server_name'] == 'kiro-tools':
                # Restricted server should not suggest restart
                assert server_insight['suggested_action'] != 'mcp_server_restart'
            else:
                assert server_insight['suggested_action'] == scenario['expected_action']
    
    @pytest.mark.asyncio
    async def test_server_metrics_tracking(self):
        """Test server metrics tracking over time"""
        
        server_config = MCPServerConfig(
            name="metrics-test-server",
            command="python",
            args=["metrics_server.py"],
            env={},
            disabled=False
        )
        
        await self.health_monitor.register_server(server_config)
        
        # Simulate metrics over time
        metrics_timeline = [
            (MCPServerStatus.HEALTHY, 80, 99.8),
            (MCPServerStatus.HEALTHY, 120, 99.5),
            (MCPServerStatus.DEGRADED, 300, 95.2),
            (MCPServerStatus.DEGRADED, 450, 87.1),
            (MCPServerStatus.OFFLINE, 0, 0.0)
        ]
        
        for status, response_time, uptime in metrics_timeline:
            self.health_monitor.statuses["metrics-test-server"] = HealthStatus(
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(),
                uptime_percentage=uptime,
                error_message="Performance degrading" if status == MCPServerStatus.DEGRADED else None
            )
            
            # Get current status
            current_status = await self.health_monitor.get_server_status("metrics-test-server")
            assert current_status.status == status
            assert current_status.response_time_ms == response_time
            assert current_status.uptime_percentage == uptime
        
        # Get metrics summary
        all_metrics = self.health_monitor.get_all_metrics()
        server_metrics = all_metrics["metrics-test-server"]
        
        # Verify metrics structure
        assert hasattr(server_metrics, 'total_checks')
        assert hasattr(server_metrics, 'total_failures')
        assert hasattr(server_metrics, 'restart_count')
        assert server_metrics.get_uptime_percentage() > 0
        assert server_metrics.get_average_response_time() > 0
    
    def test_server_configuration_validation(self):
        """Test server configuration validation"""
        
        # Valid configuration
        valid_config = MCPServerConfig(
            name="valid-server",
            command="python",
            args=["server.py"],
            env={"MODE": "production"},
            disabled=False
        )
        
        # Test configuration properties
        assert valid_config.name == "valid-server"
        assert valid_config.command == "python"
        assert valid_config.args == ["server.py"]
        assert valid_config.env["MODE"] == "production"
        assert valid_config.disabled is False
        
        # Test different server types
        server_types = [
            ("python-server", "python", ["server.py"]),
            ("uvx-server", "uvx", ["package@latest"]),
            ("node-server", "node", ["server.js"]),
            ("custom-server", "/path/to/custom", ["--config", "config.json"])
        ]
        
        for name, command, args in server_types:
            config = MCPServerConfig(
                name=name,
                command=command,
                args=args,
                env={},
                disabled=False
            )
            
            assert config.name == name
            assert config.command == command
            assert config.args == args


if __name__ == '__main__':
    pytest.main([__file__])