"""
Tests for AI Action Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime

from app.main import app
from app.services.security_manager import RiskLevel


class TestAIActionEndpoints:
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    @patch('app.services.security_manager.get_security_manager')
    @patch('app.services.health_monitor.get_health_monitor')
    def test_ai_restart_mcp_server_requires_approval(self, mock_health_monitor, mock_security_manager):
        """Test that AI MCP server restart requires user approval"""
        
        # Mock security manager
        mock_security = Mock()
        mock_security.can_ai_perform_operation.return_value = (
            False, "High risk operation requires approval", RiskLevel.HIGH
        )
        mock_security.create_ai_approval_request.return_value = {
            "operation_id": "test-op-123",
            "operation_type": "mcp_server_restart",
            "parameters": {"server_name": "groq-llm"},
            "risk_level": "high",
            "status": "pending",
            "requester": "AI_AGENT",
            "timeout_minutes": 5
        }
        mock_security_manager.return_value = mock_security
        
        # Make request
        response = self.client.post(
            "/api/v1/ai/mcp/restart/groq-llm",
            params={"reasoning": "Server appears unresponsive"}
        )
        
        # Should require approval
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "User approval required"
        assert data["data"]["approval_required"] is True
        assert data["data"]["risk_level"] == "high"
        
        # Verify security manager was called correctly
        mock_security.can_ai_perform_operation.assert_called_once_with(
            'mcp_server_restart',
            {'server_name': 'groq-llm'}
        )
        mock_security.create_ai_approval_request.assert_called_once()
    
    @patch('app.services.security_manager.get_security_manager')
    def test_ai_get_mcp_logs_success(self, mock_security_manager):
        """Test AI MCP server log retrieval"""
        
        # Mock security manager
        mock_security = Mock()
        mock_security.can_ai_perform_operation.return_value = (
            True, "Log access allowed", RiskLevel.LOW
        )
        mock_security_manager.return_value = mock_security
        
        # Make request
        response = self.client.get(
            "/api/v1/ai/mcp/logs/groq-llm",
            params={"lines": 50}
        )
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "log_lines" in data["data"]
        assert "analysis" in data["data"]
        assert data["data"]["server_name"] == "groq-llm"
        
        # Verify security check
        mock_security.can_ai_perform_operation.assert_called_once_with(
            'mcp_server_logs',
            {'server_name': 'groq-llm', 'lines': 50}
        )
        mock_security.log_operation.assert_called_once()
    
    @patch('app.services.security_manager.get_security_manager')
    def test_ai_get_mcp_logs_access_denied(self, mock_security_manager):
        """Test AI MCP server log access denied"""
        
        # Mock security manager
        mock_security = Mock()
        mock_security.can_ai_perform_operation.return_value = (
            False, "Debug log access requires approval", RiskLevel.MEDIUM
        )
        mock_security_manager.return_value = mock_security
        
        # Make request
        response = self.client.get("/api/v1/ai/mcp/logs/kiro-tools")
        
        # Should be denied
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Access denied"
        assert data["data"]["reason"] == "Debug log access requires approval"
    
    @patch('app.services.security_manager.get_security_manager')
    @patch('app.services.health_monitor.get_health_monitor')
    def test_ai_stop_mcp_server_requires_approval(self, mock_health_monitor, mock_security_manager):
        """Test that AI MCP server stop requires user approval"""
        
        # Mock security manager
        mock_security = Mock()
        mock_security.can_ai_perform_operation.return_value = (
            False, "Server stop is high risk operation", RiskLevel.HIGH
        )
        mock_security.create_ai_approval_request.return_value = {
            "operation_id": "test-stop-123",
            "operation_type": "mcp_server_stop",
            "parameters": {"server_name": "groq-llm"},
            "risk_level": "high",
            "status": "pending"
        }
        mock_security_manager.return_value = mock_security
        
        # Make request
        response = self.client.post(
            "/api/v1/ai/mcp/stop/groq-llm",
            params={"reasoning": "Server consuming too many resources"}
        )
        
        # Should require approval
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "User approval required"
        assert data["data"]["approval_required"] is True
    
    @patch('app.services.security_manager.get_security_manager')
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.pids')
    @patch('psutil.getloadavg')
    def test_ai_system_health_check_success(self, mock_loadavg, mock_pids, mock_disk, 
                                          mock_memory, mock_cpu, mock_security_manager):
        """Test AI system health check"""
        
        # Mock system metrics
        mock_cpu.return_value = 45.2
        mock_memory.return_value = Mock(percent=67.8)
        mock_disk.return_value = Mock(percent=23.4)
        mock_pids.return_value = [1, 2, 3, 4, 5]  # 5 processes
        mock_loadavg.return_value = [0.5, 0.7, 0.9]
        
        # Mock security manager
        mock_security = Mock()
        mock_security.can_ai_perform_operation.return_value = (
            True, "Health check allowed", RiskLevel.SAFE
        )
        mock_security_manager.return_value = mock_security
        
        # Mock health monitor
        with patch('app.services.health_monitor.get_health_monitor') as mock_health_monitor:
            mock_health = Mock()
            mock_health.get_all_statuses = AsyncMock(return_value={
                'groq-llm': Mock(status='HEALTHY'),
                'openrouter-llm': Mock(status='DEGRADED', error_message='High latency')
            })
            mock_health_monitor.return_value = mock_health
            
            # Make request
            response = self.client.post(
                "/api/v1/ai/system/health-check",
                params={"reasoning": "Routine health check"}
            )
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "system_metrics" in data["data"]
        assert "health_issues" in data["data"]
        assert "recommendations" in data["data"]
        assert data["data"]["system_metrics"]["cpu_percent"] == 45.2
        assert data["data"]["healthy_servers"] == 1
        assert len(data["data"]["health_issues"]) >= 1  # Should detect degraded server
    
    @patch('app.services.security_manager.get_security_manager')
    @patch('psutil.process_iter')
    def test_ai_investigate_processes_success(self, mock_process_iter, mock_security_manager):
        """Test AI process investigation"""
        
        # Mock processes
        mock_processes = [
            Mock(info={'pid': 1234, 'name': 'python', 'cpu_percent': 15.5, 'memory_percent': 8.2}),
            Mock(info={'pid': 5678, 'name': 'node', 'cpu_percent': 5.3, 'memory_percent': 12.1}),
            Mock(info={'pid': 9012, 'name': 'chrome', 'cpu_percent': 2.1, 'memory_percent': 15.7})
        ]
        mock_process_iter.return_value = mock_processes
        
        # Mock security manager
        mock_security = Mock()
        mock_security.can_ai_perform_operation.return_value = (
            True, "Process investigation allowed", RiskLevel.LOW
        )
        mock_security_manager.return_value = mock_security
        
        # Mock system functions
        with patch('psutil.pids') as mock_pids, \
             patch('psutil.getloadavg') as mock_loadavg:
            
            mock_pids.return_value = list(range(100))  # 100 processes
            mock_loadavg.return_value = [1.2, 1.5, 1.8]
            
            # Make request
            response = self.client.post(
                "/api/v1/ai/system/investigate-processes",
                params={"reasoning": "High CPU usage detected"}
            )
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "top_processes" in data["data"]
        assert "analysis" in data["data"]
        assert "recommendations" in data["data"]
        assert len(data["data"]["top_processes"]) == 3
        assert data["data"]["analysis"]["total_processes"] == 100
        
        # Should identify high CPU process
        high_cpu = data["data"]["analysis"]["high_cpu_processes"]
        assert len(high_cpu) == 1
        assert high_cpu[0]["name"] == "python"
    
    def test_ai_endpoint_error_handling(self):
        """Test AI endpoint error handling"""
        
        # Test with invalid server name
        response = self.client.post("/api/v1/ai/mcp/restart/nonexistent-server")
        
        # Should handle gracefully
        assert response.status_code in [200, 500]  # Depends on implementation
    
    @patch('app.services.security_manager.get_security_manager')
    def test_ai_operation_logging(self, mock_security_manager):
        """Test that AI operations are properly logged"""
        
        # Mock security manager
        mock_security = Mock()
        mock_security.can_ai_perform_operation.return_value = (
            True, "Operation allowed", RiskLevel.LOW
        )
        mock_security_manager.return_value = mock_security
        
        # Make request
        response = self.client.get("/api/v1/ai/mcp/logs/groq-llm")
        
        # Verify logging was called
        assert response.status_code == 200
        mock_security.log_operation.assert_called_once()
        
        # Check log parameters
        call_args = mock_security.log_operation.call_args
        assert call_args[0][0] == 'ai_log_access'  # operation type
        assert call_args[0][4] == 'AI_AGENT'  # requester


class TestHealthEndpointEnhancements:
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    @patch('app.services.health_monitor.get_health_monitor')
    @patch('app.services.security_manager.get_security_manager')
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_enhanced_health_endpoint_with_insights(self, mock_disk, mock_memory, 
                                                  mock_cpu, mock_security_manager, 
                                                  mock_health_monitor):
        """Test enhanced health endpoint with AI actionable insights"""
        
        # Mock system resources
        mock_cpu.return_value = 75.5
        mock_memory.return_value = Mock(percent=82.3, available=2*1024**3)
        mock_disk.return_value = Mock(percent=45.7, free=100*1024**3)
        
        # Mock health monitor
        mock_health = Mock()
        mock_health.get_all_statuses = AsyncMock(return_value={
            'groq-llm': Mock(
                status='HEALTHY',
                response_time_ms=120,
                uptime_percentage=99.5,
                last_check=datetime.now(),
                error_message=None
            ),
            'kiro-tools': Mock(
                status='DEGRADED',
                response_time_ms=350,
                uptime_percentage=87.2,
                last_check=datetime.now(),
                error_message='High response time'
            )
        })
        mock_health_monitor.return_value = mock_health
        
        # Mock security manager with actionable insights
        mock_security = Mock()
        mock_security.get_ai_actionable_insights.return_value = [
            {
                "type": "warning",
                "message": "MCP server kiro-tools is degraded",
                "suggested_action": "mcp_server_restart",
                "server_name": "kiro-tools",
                "priority": "medium",
                "can_auto_fix": False,
                "risk_level": "high",
                "reasoning": "Server showing high response times"
            },
            {
                "type": "info",
                "message": "CPU usage is elevated at 75.5%",
                "suggested_action": "investigate_processes",
                "priority": "low",
                "can_auto_fix": True,
                "risk_level": "low",
                "reasoning": "CPU usage above normal threshold"
            }
        ]
        mock_security_manager.return_value = mock_security
        
        # Make request
        response = self.client.get("/api/v1/health/")
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        health_data = data["data"]
        assert health_data["status"] == "degraded"  # Due to degraded server
        assert "services" in health_data
        assert "resource_usage" in health_data
        assert "actionable_insights" in health_data
        assert "system_recommendations" in health_data
        
        # Check MCP server details
        mcp_servers = health_data["services"]["mcp_servers"]
        assert mcp_servers["active_count"] == 1  # Only groq-llm is healthy
        assert mcp_servers["total_count"] == 2
        assert "kiro-tools" in mcp_servers["unhealthy_servers"]
        
        # Check actionable insights
        insights = health_data["actionable_insights"]
        assert len(insights) == 2
        
        server_insight = next(i for i in insights if i["server_name"] == "kiro-tools")
        assert server_insight["suggested_action"] == "mcp_server_restart"
        assert server_insight["can_auto_fix"] is False
        
        cpu_insight = next(i for i in insights if "CPU" in i["message"])
        assert cpu_insight["can_auto_fix"] is True
        
        # Check system recommendations
        recommendations = health_data["system_recommendations"]
        assert len(recommendations) >= 1  # Should have CPU recommendation
    
    def test_simple_health_endpoint(self):
        """Test simple health endpoint for basic monitoring"""
        
        response = self.client.get("/api/v1/health/simple")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "mcp-ecosystem-platform"


if __name__ == '__main__':
    pytest.main([__file__])
