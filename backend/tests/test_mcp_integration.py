"""
Integration Tests for MCP Server Management
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime, timedelta

from backend.app.main import app
from backend.app.core.interfaces import MCPServerStatus, HealthStatus


class TestMCPServerIntegration:
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    @patch('backend.app.services.health_monitor.get_health_monitor')
    def test_mcp_server_restart_integration(self, mock_health_monitor):
        """Test complete MCP server restart flow"""
        
        # Mock health monitor
        mock_health = Mock()
        
        # Initial status - server is offline
        initial_status = HealthStatus(
            status=MCPServerStatus.OFFLINE,
            response_time_ms=0,
            last_check=datetime.now(),
            uptime_percentage=0.0,
            error_message="Server not responding"
        )
        
        # After restart - server is starting
        restarting_status = HealthStatus(
            status=MCPServerStatus.STARTING,
            response_time_ms=0,
            last_check=datetime.now(),
            uptime_percentage=100.0
        )
        
        # Final status - server is healthy
        healthy_status = HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=150,
            last_check=datetime.now(),
            uptime_percentage=100.0
        )
        
        # Setup mock responses
        mock_health.get_server_status = AsyncMock(side_effect=[
            initial_status,
            restarting_status,
            healthy_status
        ])
        mock_health.force_restart_server = AsyncMock(return_value=True)
        mock_health_monitor.return_value = mock_health
        
        # 1. Check initial server status
        response = self.client.get("/api/v1/mcp/status/groq-llm")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "OFFLINE"
        
        # 2. Restart server
        response = self.client.post("/api/v1/mcp/restart/groq-llm")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "restarted successfully" in data["data"]["message"]
        
        # 3. Verify restart was called
        mock_health.force_restart_server.assert_called_once_with("groq-llm")
        
        # 4. Check server status after restart
        response = self.client.get("/api/v1/mcp/status/groq-llm")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "STARTING"
        
        # 5. Check final healthy status
        response = self.client.get("/api/v1/mcp/status/groq-llm")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "HEALTHY"
    
    @patch('backend.app.services.health_monitor.get_health_monitor')
    def test_mcp_server_metrics_collection(self, mock_health_monitor):
        """Test MCP server metrics collection and analysis"""
        
        # Mock server metrics
        mock_metrics = {
            'groq-llm': Mock(
                total_checks=1000,
                total_failures=50,
                consecutive_failures=0,
                restart_count=2,
                last_successful_check=datetime.now(),
                last_failed_check=datetime.now() - timedelta(hours=1)
            ),
            'openrouter-llm': Mock(
                total_checks=800,
                total_failures=120,
                consecutive_failures=3,
                restart_count=5,
                last_successful_check=datetime.now() - timedelta(minutes=30),
                last_failed_check=datetime.now() - timedelta(minutes=5)
            )
        }
        
        # Add methods to mock metrics
        for server_name, metrics in mock_metrics.items():
            metrics.get_uptime_percentage.return_value = 95.0 if server_name == 'groq-llm' else 85.0
            metrics.get_average_response_time.return_value = 150.0 if server_name == 'groq-llm' else 280.0
            metrics.get_p95_response_time.return_value = 300.0 if server_name == 'groq-llm' else 500.0
        
        # Mock health monitor
        mock_health = Mock()
        mock_health.get_all_metrics.return_value = mock_metrics
        mock_health_monitor.return_value = mock_health
        
        # Get metrics
        response = self.client.get("/api/v1/mcp/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        metrics_data = data["data"]
        assert "groq-llm" in metrics_data
        assert "openrouter-llm" in metrics_data
        
        # Check groq-llm metrics (healthy server)
        groq_metrics = metrics_data["groq-llm"]
        assert groq_metrics["total_checks"] == 1000
        assert groq_metrics["total_failures"] == 50
        assert groq_metrics["consecutive_failures"] == 0
        assert groq_metrics["uptime_percentage"] == 95.0
        assert groq_metrics["restart_count"] == 2
        
        # Check openrouter-llm metrics (problematic server)
        openrouter_metrics = metrics_data["openrouter-llm"]
        assert openrouter_metrics["consecutive_failures"] == 3
        assert openrouter_metrics["uptime_percentage"] == 85.0
        assert openrouter_metrics["restart_count"] == 5
    
    @patch('backend.app.services.health_monitor.get_health_monitor')
    @patch('backend.app.services.security_manager.get_security_manager')
    def test_ai_actionable_insights_integration(self, mock_security_manager, mock_health_monitor):
        """Test AI actionable insights generation based on server status"""
        
        # Mock unhealthy server statuses
        mock_statuses = {
            'groq-llm': HealthStatus(
                status=MCPServerStatus.OFFLINE,
                response_time_ms=0,
                last_check=datetime.now(),
                uptime_percentage=0.0,
                error_message="Connection refused"
            ),
            'openrouter-llm': HealthStatus(
                status=MCPServerStatus.DEGRADED,
                response_time_ms=450,
                last_check=datetime.now(),
                uptime_percentage=75.0,
                error_message="High response time"
            ),
            'kiro-tools': HealthStatus(
                status=MCPServerStatus.HEALTHY,
                response_time_ms=120,
                last_check=datetime.now(),
                uptime_percentage=99.5
            )
        }
        
        # Mock health monitor
        mock_health = Mock()
        mock_health.get_all_statuses = AsyncMock(return_value=mock_statuses)
        mock_health_monitor.return_value = mock_health
        
        # Mock security manager with realistic insights
        mock_security = Mock()
        mock_security.get_ai_actionable_insights.return_value = [
            {
                "id": "insight-1",
                "type": "error",
                "message": "MCP server groq-llm is offline",
                "suggested_action": "mcp_server_restart",
                "server_name": "groq-llm",
                "priority": "high",
                "can_auto_fix": False,
                "risk_level": "high",
                "reasoning": "Server is completely unresponsive",
                "estimated_fix_time": "2-3 minutes",
                "confidence_score": 95,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "insight-2", 
                "type": "warning",
                "message": "MCP server openrouter-llm has degraded performance",
                "suggested_action": "investigate_processes",
                "server_name": "openrouter-llm",
                "priority": "medium",
                "can_auto_fix": True,
                "risk_level": "low",
                "reasoning": "Response time is 3x normal threshold",
                "estimated_fix_time": "5-10 minutes",
                "confidence_score": 78,
                "created_at": datetime.now().isoformat()
            }
        ]
        mock_security_manager.return_value = mock_security
        
        # Mock system resources
        with patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_cpu.return_value = 45.0
            mock_memory.return_value = Mock(percent=60.0, available=4*1024**3)
            mock_disk.return_value = Mock(percent=30.0, free=200*1024**3)
            
            # Get system health with insights
            response = self.client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        health_data = data["data"]
        assert health_data["status"] == "degraded"  # Due to offline/degraded servers
        
        # Check actionable insights
        insights = health_data["actionable_insights"]
        assert len(insights) == 2
        
        # Verify offline server insight
        offline_insight = next(i for i in insights if i["server_name"] == "groq-llm")
        assert offline_insight["type"] == "error"
        assert offline_insight["suggested_action"] == "mcp_server_restart"
        assert offline_insight["can_auto_fix"] is False
        assert offline_insight["priority"] == "high"
        
        # Verify degraded server insight
        degraded_insight = next(i for i in insights if i["server_name"] == "openrouter-llm")
        assert degraded_insight["type"] == "warning"
        assert degraded_insight["suggested_action"] == "investigate_processes"
        assert degraded_insight["can_auto_fix"] is True
        assert degraded_insight["priority"] == "medium"
    
    @patch('backend.app.services.mcp_client.get_mcp_client_manager')
    def test_mcp_tool_execution_with_security(self, mock_client_manager):
        """Test MCP tool execution with security controls"""
        
        # Mock MCP client
        mock_client = Mock()
        mock_client.call_tool = AsyncMock(return_value={
            "success": True,
            "result": "Tool executed successfully",
            "execution_time": 0.5
        })
        
        mock_manager = Mock()
        mock_manager.get_client.return_value = mock_client
        mock_client_manager.return_value = mock_manager
        
        # Mock security manager for safe operation
        with patch('backend.app.services.security_manager.get_security_manager') as mock_security_manager:
            mock_security = Mock()
            mock_security.assess_risk.return_value = ("safe", "Safe operation")
            mock_security.requires_approval.return_value = False
            mock_security.sanitize_parameters.return_value = {"param1": "value1"}
            mock_security_manager.return_value = mock_security
            
            # Execute tool
            response = self.client.post(
                "/api/v1/tools/execute/groq-llm/test_tool",
                json={"param1": "value1"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify security checks were performed
        mock_security.assess_risk.assert_called_once()
        mock_security.sanitize_parameters.assert_called_once()
        mock_security.log_operation.assert_called_once()
        
        # Verify tool was executed
        mock_client.call_tool.assert_called_once_with("test_tool", {"param1": "value1"})
    
    def test_mcp_server_not_found_handling(self):
        """Test handling of non-existent MCP servers"""
        
        # Try to get status of non-existent server
        response = self.client.get("/api/v1/mcp/status/nonexistent-server")
        assert response.status_code == 500  # Should handle gracefully
        
        # Try to restart non-existent server
        response = self.client.post("/api/v1/mcp/restart/nonexistent-server")
        assert response.status_code == 400
        data = response.json()
        assert "Failed to restart" in data["detail"]
    
    @patch('backend.app.services.health_monitor.get_health_monitor')
    def test_concurrent_server_operations(self, mock_health_monitor):
        """Test handling of concurrent server operations"""
        
        # Mock health monitor
        mock_health = Mock()
        mock_health.force_restart_server = AsyncMock(return_value=True)
        mock_health_monitor.return_value = mock_health
        
        # Simulate concurrent restart requests
        import threading
        import time
        
        results = []
        
        def restart_server():
            response = self.client.post("/api/v1/mcp/restart/groq-llm")
            results.append(response.status_code)
        
        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=restart_server)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed (or handle gracefully)
        assert all(status in [200, 400, 500] for status in results)
        
        # Restart should have been called multiple times
        assert mock_health.force_restart_server.call_count == 3


class TestMCPServerLifecycle:
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    @patch('backend.app.services.health_monitor.get_health_monitor')
    def test_server_lifecycle_monitoring(self, mock_health_monitor):
        """Test complete server lifecycle monitoring"""
        
        # Mock health monitor with lifecycle states
        mock_health = Mock()
        
        # Simulate server lifecycle: STARTING -> HEALTHY -> DEGRADED -> OFFLINE -> STARTING
        lifecycle_states = [
            HealthStatus(MCPServerStatus.STARTING, 0, datetime.now(), 0.0),
            HealthStatus(MCPServerStatus.HEALTHY, 120, datetime.now(), 100.0),
            HealthStatus(MCPServerStatus.DEGRADED, 350, datetime.now(), 85.0, "High latency"),
            HealthStatus(MCPServerStatus.OFFLINE, 0, datetime.now(), 0.0, "Connection lost"),
            HealthStatus(MCPServerStatus.STARTING, 0, datetime.now(), 0.0)
        ]
        
        mock_health.get_server_status = AsyncMock(side_effect=lifecycle_states)
        mock_health.force_restart_server = AsyncMock(return_value=True)
        mock_health_monitor.return_value = mock_health
        
        # 1. Server starting
        response = self.client.get("/api/v1/mcp/status/groq-llm")
        data = response.json()
        assert data["data"]["status"] == "STARTING"
        
        # 2. Server becomes healthy
        response = self.client.get("/api/v1/mcp/status/groq-llm")
        data = response.json()
        assert data["data"]["status"] == "HEALTHY"
        assert data["data"]["response_time_ms"] == 120
        
        # 3. Server degrades
        response = self.client.get("/api/v1/mcp/status/groq-llm")
        data = response.json()
        assert data["data"]["status"] == "DEGRADED"
        assert data["data"]["error_message"] == "High latency"
        
        # 4. Server goes offline
        response = self.client.get("/api/v1/mcp/status/groq-llm")
        data = response.json()
        assert data["data"]["status"] == "OFFLINE"
        
        # 5. Restart server
        response = self.client.post("/api/v1/mcp/restart/groq-llm")
        assert response.status_code == 200
        
        # 6. Server restarting
        response = self.client.get("/api/v1/mcp/status/groq-llm")
        data = response.json()
        assert data["data"]["status"] == "STARTING"


if __name__ == '__main__':
    pytest.main([__file__])