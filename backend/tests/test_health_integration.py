"""
Integration tests for health monitoring system
Tests the complete flow from health check to AI insights to action recommendations
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.main import app
from app.services.health_monitor import HealthMonitor
from app.services.security_manager import SecurityManager, RiskLevel
from app.core.interfaces import HealthStatus, MCPServerStatus, MCPServerConfig


class TestHealthMonitoringIntegration:
    """Integration tests for complete health monitoring workflow"""
    
    def setup_method(self):
        """Setup test client and services"""
        self.client = TestClient(app)
        self.health_monitor = HealthMonitor()
        self.security_manager = SecurityManager()
    
    @pytest.mark.asyncio
    async def test_complete_health_check_workflow(self):
        """Test complete workflow: health check -> insights -> action recommendations"""
        
        # Step 1: Register mock MCP servers
        servers = [
            MCPServerConfig(
                name="groq-llm",
                command="uvx",
                args=["groq-llm-server"],
                env={},
                disabled=False
            ),
            MCPServerConfig(
                name="kiro-tools", 
                command="python",
                args=["kiro_tools_server.py"],
                env={},
                disabled=False
            ),
            MCPServerConfig(
                name="browser-automation",
                command="uvx",
                args=["browser-automation-server"],
                env={},
                disabled=False
            )
        ]
        
        for server in servers:
            await self.health_monitor.register_server(server)
        
        # Step 2: Simulate server statuses
        self.health_monitor.statuses = {
            "groq-llm": HealthStatus(
                status=MCPServerStatus.HEALTHY,
                response_time_ms=120,
                last_check=datetime.now(),
                uptime_percentage=99.2
            ),
            "kiro-tools": HealthStatus(
                status=MCPServerStatus.DEGRADED,
                response_time_ms=450,
                last_check=datetime.now(),
                error_message="High response time detected",
                uptime_percentage=87.5
            ),
            "browser-automation": HealthStatus(
                status=MCPServerStatus.OFFLINE,
                response_time_ms=0,
                last_check=datetime.now(),
                error_message="Connection refused",
                uptime_percentage=0.0
            )
        }
        
        # Step 3: Get health status
        all_statuses = await self.health_monitor.get_all_statuses()
        
        # Verify health statuses
        assert len(all_statuses) == 3
        assert all_statuses["groq-llm"].status == MCPServerStatus.HEALTHY
        assert all_statuses["kiro-tools"].status == MCPServerStatus.DEGRADED
        assert all_statuses["browser-automation"].status == MCPServerStatus.OFFLINE
        
        # Step 4: Generate AI insights
        system_status = {
            'mcp_servers': {
                'unhealthy_servers': ['kiro-tools', 'browser-automation']
            },
            'resource_usage': {
                'cpu_percent': 75,
                'memory_percent': 80
            }
        }
        
        insights = self.security_manager.get_ai_actionable_insights(system_status)
        
        # Verify insights generation
        assert len(insights) >= 3  # 2 servers + resource usage
        
        # Check server insights
        server_insights = [i for i in insights if 'server_name' in i]
        assert len(server_insights) == 2
        
        kiro_insight = next(i for i in server_insights if i['server_name'] == 'kiro-tools')
        browser_insight = next(i for i in server_insights if i['server_name'] == 'browser-automation')
        
        assert kiro_insight['suggested_action'] == 'mcp_server_restart'
        assert browser_insight['suggested_action'] == 'mcp_server_restart'
        
        # Step 5: Test AI action permissions
        can_restart_kiro, reason_kiro, risk_kiro = self.security_manager.can_ai_perform_operation(
            'mcp_server_restart',
            {'server_name': 'kiro-tools'}
        )
        
        can_restart_browser, reason_browser, risk_browser = self.security_manager.can_ai_perform_operation(
            'mcp_server_restart', 
            {'server_name': 'browser-automation'}
        )
        
        # kiro-tools should be restricted
        assert can_restart_kiro is False
        assert risk_kiro == RiskLevel.CRITICAL
        
        # browser-automation should require approval
        assert can_restart_browser is False
        assert risk_browser == RiskLevel.HIGH
    
    @pytest.mark.asyncio
    async def test_mcp_server_restart_integration(self):
        """Test MCP server restart integration with approval workflow"""
        
        # Setup server
        server_config = MCPServerConfig(
            name="test-server",
            command="python",
            args=["test_server.py"],
            env={},
            disabled=False
        )
        
        await self.health_monitor.register_server(server_config)
        
        # Set server as offline
        self.health_monitor.statuses["test-server"] = HealthStatus(
            status=MCPServerStatus.OFFLINE,
            response_time_ms=0,
            last_check=datetime.now(),
            error_message="Server crashed",
            uptime_percentage=0.0
        )
        
        # Test restart functionality
        restart_success = await self.health_monitor.force_restart_server("test-server")
        assert restart_success is True
        
        # Verify server status changed to STARTING
        status = await self.health_monitor.get_server_status("test-server")
        assert status.status == MCPServerStatus.STARTING
    
    def test_end_to_end_health_api_integration(self):
        """Test end-to-end health API integration"""
        
        with patch('backend.app.services.health_monitor.get_health_monitor') as mock_health_monitor, \
             patch('backend.app.services.security_manager.get_security_manager') as mock_security_manager, \
             patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            # Mock system resources
            mock_cpu.return_value = 65.5
            mock_memory.return_value = Mock(percent=72.3, available=4*1024**3)
            mock_disk.return_value = Mock(percent=35.7, free=200*1024**3)
            
            # Mock health monitor
            mock_health = Mock()
            mock_health.get_all_statuses = AsyncMock(return_value={
                'groq-llm': Mock(
                    status='HEALTHY',
                    response_time_ms=95,
                    uptime_percentage=99.8,
                    last_check=datetime.now(),
                    error_message=None
                ),
                'browser-automation': Mock(
                    status='DEGRADED',
                    response_time_ms=380,
                    uptime_percentage=85.2,
                    last_check=datetime.now(),
                    error_message='High response time'
                )
            })
            mock_health_monitor.return_value = mock_health
            
            # Mock security manager
            mock_security = Mock()
            mock_security.get_ai_actionable_insights.return_value = [
                {
                    "type": "warning",
                    "message": "MCP server browser-automation is degraded",
                    "suggested_action": "mcp_server_restart",
                    "server_name": "browser-automation",
                    "priority": "medium",
                    "can_auto_fix": False,
                    "risk_level": "high"
                }
            ]
            mock_security_manager.return_value = mock_security
            
            # Make health API request
            response = self.client.get("/api/v1/health/")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            health_data = data["data"]
            assert health_data["status"] == "degraded"  # Due to degraded server
            
            # Verify MCP server data
            mcp_servers = health_data["services"]["mcp_servers"]
            assert mcp_servers["active_count"] == 1
            assert mcp_servers["total_count"] == 2
            assert "browser-automation" in mcp_servers["unhealthy_servers"]
            
            # Verify actionable insights
            insights = health_data["actionable_insights"]
            assert len(insights) == 1
            assert insights[0]["server_name"] == "browser-automation"
            assert insights[0]["suggested_action"] == "mcp_server_restart"
    
    def test_ai_restart_approval_workflow_integration(self):
        """Test complete AI restart approval workflow"""
        
        with patch('backend.app.services.security_manager.get_security_manager') as mock_security_manager, \
             patch('backend.app.services.health_monitor.get_health_monitor') as mock_health_monitor:
            
            # Mock security manager
            mock_security = Mock()
            mock_security.can_ai_perform_operation.return_value = (
                False, "High risk operation requires approval", RiskLevel.HIGH
            )
            mock_security.create_ai_approval_request.return_value = {
                "operation_id": "test-restart-123",
                "operation_type": "mcp_server_restart",
                "parameters": {"server_name": "groq-llm"},
                "ai_reasoning": "Server showing degraded performance",
                "risk_level": "high",
                "status": "pending",
                "requester": "AI_AGENT",
                "timeout_minutes": 5
            }
            mock_security_manager.return_value = mock_security
            
            # Step 1: AI requests restart
            response = self.client.post(
                "/api/v1/ai/mcp/restart/groq-llm",
                params={"reasoning": "Server showing degraded performance"}
            )
            
            # Should require approval
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["error"] == "User approval required"
            assert data["data"]["approval_required"] is True
            
            operation_id = data["data"]["approval_request"]["operation_id"]
            
            # Step 2: Check pending approvals
            mock_security.get_pending_approvals.return_value = [
                {
                    "operation_id": operation_id,
                    "operation_type": "mcp_server_restart",
                    "status": "pending"
                }
            ]
            
            response = self.client.get("/api/v1/security/approvals")
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 1
            
            # Step 3: Approve operation
            mock_security.approve_operation.return_value = True
            
            response = self.client.post(
                f"/api/v1/security/approve/{operation_id}",
                params={"user_id": "test_user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_ai_log_analysis_integration(self):
        """Test AI log analysis integration"""
        
        with patch('backend.app.services.security_manager.get_security_manager') as mock_security_manager:
            
            # Mock security manager
            mock_security = Mock()
            mock_security.can_ai_perform_operation.return_value = (
                True, "Log access allowed", RiskLevel.LOW
            )
            mock_security_manager.return_value = mock_security
            
            # Request logs
            response = self.client.get("/api/v1/ai/mcp/logs/groq-llm?lines=100")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            log_data = data["data"]
            assert log_data["server_name"] == "groq-llm"
            assert "log_lines" in log_data
            assert "analysis" in log_data
            
            # Verify analysis structure
            analysis = log_data["analysis"]
            assert "error_count" in analysis
            assert "warning_count" in analysis
            assert "status" in analysis
            
            # Verify operation was logged
            mock_security.log_operation.assert_called_once()
            call_args = mock_security.log_operation.call_args
            assert call_args[0][0] == 'ai_log_access'
            assert call_args[0][4] == 'AI_AGENT'
    
    @pytest.mark.asyncio
    async def test_proactive_monitoring_scenario(self):
        """Test proactive monitoring scenario where AI detects and responds to issues"""
        
        # Setup: Healthy system initially
        server_config = MCPServerConfig(
            name="monitored-server",
            command="python", 
            args=["server.py"],
            env={},
            disabled=False
        )
        
        await self.health_monitor.register_server(server_config)
        
        # Initial healthy status
        self.health_monitor.statuses["monitored-server"] = HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=100,
            last_check=datetime.now(),
            uptime_percentage=99.5
        )
        
        # Simulate degradation
        self.health_monitor.statuses["monitored-server"] = HealthStatus(
            status=MCPServerStatus.DEGRADED,
            response_time_ms=500,
            last_check=datetime.now(),
            error_message="Response time increasing",
            uptime_percentage=95.0
        )
        
        # AI should detect this and generate insights
        system_status = {
            'mcp_servers': {
                'unhealthy_servers': ['monitored-server']
            },
            'resource_usage': {
                'cpu_percent': 45,
                'memory_percent': 60
            }
        }
        
        insights = self.security_manager.get_ai_actionable_insights(system_status)
        
        # Should have insight for degraded server
        server_insights = [i for i in insights if i.get('server_name') == 'monitored-server']
        assert len(server_insights) == 1
        
        insight = server_insights[0]
        assert insight['type'] == 'warning'
        assert insight['suggested_action'] == 'mcp_server_restart'
        assert insight['can_auto_fix'] is False  # Requires approval


if __name__ == '__main__':
    pytest.main([__file__])