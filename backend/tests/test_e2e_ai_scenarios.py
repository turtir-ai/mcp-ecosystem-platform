"""
End-to-End AI Action Scenarios Tests

Tests complete AI decision-making workflows from detection to resolution.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from backend.app.main import app
from backend.app.services.security_manager import RiskLevel
from backend.app.core.interfaces import MCPServerStatus, HealthStatus


class TestE2EAIScenarios:
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    @patch('backend.app.services.health_monitor.get_health_monitor')
    @patch('backend.app.services.security_manager.get_security_manager')
    @patch('backend.app.services.proactive_monitor.get_proactive_monitor')
    def test_e2e_mcp_server_unhealthy_to_restart_scenario(self, mock_proactive_monitor, 
                                                         mock_security_manager, mock_health_monitor):
        """
        E2E Test: MCP server "unhealthy" → AI önerisi → Kullanıcı onayı → Restart → Doğrulama
        """
        
        # Step 1: Setup - Server is unhealthy
        unhealthy_status = HealthStatus(
            status=MCPServerStatus.OFFLINE,
            response_time_ms=0,
            last_check=datetime.now(),
            uptime_percentage=0.0,
            error_message="Connection refused"
        )
        
        healthy_status = HealthStatus(
            status=MCPServerStatus.HEALTHY,
            response_time_ms=120,
            last_check=datetime.now(),
            uptime_percentage=100.0
        )
        
        # Mock health monitor
        mock_health = Mock()
        mock_health.get_all_statuses = AsyncMock(return_value={
            'groq-llm': unhealthy_status
        })
        mock_health.get_server_status = AsyncMock(side_effect=[
            unhealthy_status,  # Initial check
            healthy_status     # After restart
        ])
        mock_health.force_restart_server = AsyncMock(return_value=True)
        mock_health_monitor.return_value = mock_health
        
        # Mock security manager
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
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # AI restart requires approval
        mock_security.can_ai_perform_operation.return_value = (
            False, "High risk operation requires approval", RiskLevel.HIGH
        )
        
        approval_request = {
            "operation_id": "test-restart-123",
            "operation_type": "mcp_server_restart",
            "parameters": {"server_name": "groq-llm"},
            "risk_level": "high",
            "status": "pending",
            "requester": "AI_AGENT",
            "timeout_minutes": 5
        }
        mock_security.create_ai_approval_request.return_value = approval_request
        mock_security.is_operation_approved.return_value = True
        mock_security.approve_operation.return_value = True
        mock_security.get_pending_approvals.return_value = [approval_request]
        mock_security_manager.return_value = mock_security
        
        # Mock proactive monitor
        mock_monitor = Mock()
        mock_monitor.get_active_alerts.return_value = []
        mock_proactive_monitor.return_value = mock_monitor
        
        # Step 2: Get system health - should detect unhealthy server
        with patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_cpu.return_value = 45.0
            mock_memory.return_value = Mock(percent=60.0, available=4*1024**3)
            mock_disk.return_value = Mock(percent=30.0, free=200*1024**3)
            
            response = self.client.get("/api/v1/health/")
        
        assert response.status_code == 200
        health_data = response.json()["data"]
        
        # Verify system detected as degraded due to offline server
        assert health_data["status"] == "degraded"
        assert len(health_data["actionable_insights"]) > 0
        
        # Find the server restart insight
        restart_insight = next(
            (insight for insight in health_data["actionable_insights"] 
             if insight.get("suggested_action") == "mcp_server_restart"),
            None
        )
        assert restart_insight is not None
        assert restart_insight["server_name"] == "groq-llm"
        assert restart_insight["can_auto_fix"] is False
        
        # Step 3: AI attempts restart - should require approval
        response = self.client.post(
            "/api/v1/ai/mcp/restart/groq-llm",
            params={"reasoning": "Server detected as offline by health check"}
        )
        
        assert response.status_code == 200
        restart_response = response.json()
        assert restart_response["success"] is False
        assert restart_response["error"] == "User approval required"
        assert restart_response["data"]["approval_required"] is True
        assert restart_response["data"]["risk_level"] == "high"
        
        # Step 4: Check pending approvals
        response = self.client.get("/api/v1/security/approvals")
        assert response.status_code == 200
        approvals = response.json()["data"]
        assert len(approvals) == 1
        assert approvals[0]["operation_type"] == "mcp_server_restart"
        
        # Step 5: User approves the operation
        operation_id = approvals[0]["operation_id"]
        response = self.client.post(f"/api/v1/security/approve/{operation_id}")
        assert response.status_code == 200
        
        # Step 6: Execute the approved restart
        # In real scenario, this would be triggered automatically after approval
        response = self.client.post("/api/v1/mcp/restart/groq-llm")
        assert response.status_code == 200
        restart_result = response.json()
        assert restart_result["success"] is True
        
        # Step 7: Verify server is now healthy
        response = self.client.get("/api/v1/mcp/status/groq-llm")
        assert response.status_code == 200
        server_status = response.json()["data"]
        assert server_status["status"] == "HEALTHY"
        
        # Step 8: Verify system health improved
        response = self.client.get("/api/v1/health/")
        assert response.status_code == 200
        final_health = response.json()["data"]
        assert final_health["status"] in ["healthy", "degraded"]  # Should be better than before
        
        # Verify all expected calls were made
        mock_security.create_ai_approval_request.assert_called_once()
        mock_health.force_restart_server.assert_called_once_with("groq-llm")
    
    @patch('backend.app.services.security_manager.get_security_manager')
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.process_iter')
    def test_e2e_high_resource_usage_optimization_scenario(self, mock_process_iter, 
                                                          mock_memory, mock_cpu, mock_security_manager):
        """
        E2E Test: Sistem kaynak kullanımı yüksek → AI uyarısı → Optimizasyon önerisi
        """
        
        # Step 1: Setup - High resource usage
        mock_cpu.return_value = 88.5  # High CPU
        mock_memory.return_value = Mock(percent=92.3)  # High memory
        
        # Mock high-resource processes
        mock_processes = [
            Mock(info={'pid': 1234, 'name': 'python', 'cpu_percent': 25.5, 'memory_percent': 15.2}),
            Mock(info={'pid': 5678, 'name': 'node', 'cpu_percent': 18.3, 'memory_percent': 22.1}),
            Mock(info={'pid': 9012, 'name': 'chrome', 'cpu_percent': 12.1, 'memory_percent': 18.7})
        ]
        mock_process_iter.return_value = mock_processes
        
        # Mock security manager
        mock_security = Mock()
        mock_security.get_ai_actionable_insights.return_value = [
            {
                "id": "insight-cpu",
                "type": "warning",
                "message": "High CPU usage detected at 88.5%",
                "suggested_action": "investigate_processes",
                "priority": "medium",
                "can_auto_fix": True,
                "risk_level": "low",
                "reasoning": "CPU usage above 85% threshold"
            },
            {
                "id": "insight-memory",
                "type": "error",
                "message": "Critical memory usage at 92.3%",
                "suggested_action": "restart_services",
                "priority": "high",
                "can_auto_fix": False,
                "risk_level": "medium",
                "reasoning": "Memory usage above 90% critical threshold"
            }
        ]
        
        mock_security.can_ai_perform_operation.return_value = (
            True, "Process investigation allowed", RiskLevel.LOW
        )
        mock_security_manager.return_value = mock_security
        
        # Step 2: Get system health - should detect resource issues
        with patch('psutil.disk_usage') as mock_disk, \
             patch('backend.app.services.health_monitor.get_health_monitor') as mock_health_monitor:
            
            mock_disk.return_value = Mock(percent=45.0, free=100*1024**3)
            
            # Mock healthy MCP servers
            mock_health = Mock()
            mock_health.get_all_statuses = AsyncMock(return_value={
                'groq-llm': HealthStatus(MCPServerStatus.HEALTHY, 120, datetime.now(), 99.5)
            })
            mock_health_monitor.return_value = mock_health
            
            response = self.client.get("/api/v1/health/")
        
        assert response.status_code == 200
        health_data = response.json()["data"]
        
        # Verify high resource usage detected
        assert health_data["resource_usage"]["cpu_percent"] == 88.5
        assert health_data["resource_usage"]["memory_percent"] == 92.3
        assert len(health_data["actionable_insights"]) >= 2
        
        # Find resource-related insights
        cpu_insight = next(
            (insight for insight in health_data["actionable_insights"] 
             if "CPU" in insight.get("message", "")),
            None
        )
        memory_insight = next(
            (insight for insight in health_data["actionable_insights"] 
             if "memory" in insight.get("message", "")),
            None
        )
        
        assert cpu_insight is not None
        assert memory_insight is not None
        assert cpu_insight["suggested_action"] == "investigate_processes"
        assert memory_insight["suggested_action"] == "restart_services"
        
        # Step 3: AI investigates processes (auto-approved for low risk)
        with patch('psutil.pids') as mock_pids, \
             patch('psutil.getloadavg') as mock_loadavg:
            
            mock_pids.return_value = list(range(150))  # 150 processes
            mock_loadavg.return_value = [2.1, 2.3, 2.5]
            
            response = self.client.post(
                "/api/v1/ai/system/investigate-processes",
                params={"reasoning": "High CPU usage detected by health monitoring"}
            )
        
        assert response.status_code == 200
        investigation_result = response.json()
        assert investigation_result["success"] is True
        
        investigation_data = investigation_result["data"]
        assert len(investigation_data["top_processes"]) > 0
        assert investigation_data["analysis"]["total_processes"] == 150
        
        # Should identify high CPU processes
        high_cpu_processes = investigation_data["analysis"]["high_cpu_processes"]
        assert len(high_cpu_processes) >= 1
        
        # Should have recommendations
        recommendations = investigation_data["recommendations"]
        assert len(recommendations) > 0
        
        # Step 4: Verify AI logged the investigation
        mock_security.log_operation.assert_called()
        
        # Step 5: Check that system recommendations include resource optimization
        response = self.client.get("/api/v1/health/")
        health_data = response.json()["data"]
        
        recommendations = health_data["system_recommendations"]
        resource_recommendations = [
            r for r in recommendations 
            if r["type"] == "performance" and "usage" in r["message"]
        ]
        assert len(resource_recommendations) >= 1
    
    @patch('backend.app.services.health_monitor.get_health_monitor')
    @patch('backend.app.services.security_manager.get_security_manager')
    def test_e2e_database_latency_analysis_scenario(self, mock_security_manager, mock_health_monitor):
        """
        E2E Test: Database latency yüksek → AI analizi → Çözüm önerisi
        """
        
        # Step 1: Setup - High database latency
        mock_health = Mock()
        mock_health.get_all_statuses = AsyncMock(return_value={
            'groq-llm': HealthStatus(MCPServerStatus.HEALTHY, 150, datetime.now(), 98.5)
        })
        mock_health_monitor.return_value = mock_health
        
        # Mock security manager with database insights
        mock_security = Mock()
        mock_security.get_ai_actionable_insights.return_value = [
            {
                "id": "insight-db",
                "type": "warning",
                "message": "Database latency is high (250ms)",
                "suggested_action": "investigate_processes",
                "priority": "medium",
                "can_auto_fix": True,
                "risk_level": "low",
                "reasoning": "Database response time above 200ms threshold",
                "metadata": {
                    "component": "database",
                    "latency_ms": 250,
                    "threshold_ms": 200
                }
            }
        ]
        mock_security_manager.return_value = mock_security
        
        # Step 2: Get system health with high DB latency
        with patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('asyncio.sleep') as mock_sleep:
            
            mock_cpu.return_value = 45.0
            mock_memory.return_value = Mock(percent=60.0, available=4*1024**3)
            mock_disk.return_value = Mock(percent=30.0, free=200*1024**3)
            
            # Mock high database latency
            mock_sleep.return_value = None
            
            # Patch time.time to simulate high latency
            with patch('time.time') as mock_time:
                mock_time.side_effect = [0, 0.25]  # 250ms latency
                
                response = self.client.get("/api/v1/health/")
        
        assert response.status_code == 200
        health_data = response.json()["data"]
        
        # Verify database latency detected
        db_info = health_data["services"]["database"]
        assert db_info["latency_ms"] >= 200  # High latency
        
        # Should have database recommendation
        recommendations = health_data["system_recommendations"]
        db_recommendations = [
            r for r in recommendations 
            if r["type"] == "database" and "latency" in r["message"]
        ]
        assert len(db_recommendations) >= 1
        
        db_rec = db_recommendations[0]
        assert "database" in db_rec["message"].lower()
        assert db_rec["priority"] in ["medium", "high"]
        
        # Step 3: AI analyzes database issue
        insights = health_data["actionable_insights"]
        db_insight = next(
            (insight for insight in insights if "database" in insight.get("message", "").lower()),
            None
        )
        
        if db_insight:
            assert db_insight["suggested_action"] in ["investigate_processes", "restart_services"]
            assert db_insight["priority"] in ["medium", "high"]
    
    @patch('backend.app.services.proactive_monitor.get_proactive_monitor')
    @patch('backend.app.services.health_monitor.get_health_monitor')
    @patch('backend.app.services.security_manager.get_security_manager')
    def test_e2e_proactive_pattern_detection_scenario(self, mock_security_manager, 
                                                     mock_health_monitor, mock_proactive_monitor):
        """
        E2E Test: Proactive pattern detection and alert generation
        """
        
        # Step 1: Setup proactive monitor with detected patterns
        from backend.app.services.proactive_monitor import HealthPattern, PatternType, SystemAlert, AlertSeverity
        
        detected_pattern = HealthPattern(
            pattern_type=PatternType.RECURRING_FAILURE,
            description="Server groq-llm has recurring failures every 2 hours",
            confidence=0.85,
            first_occurrence=datetime.now() - timedelta(hours=8),
            last_occurrence=datetime.now() - timedelta(minutes=30),
            frequency=4,
            affected_components=["groq-llm"],
            suggested_resolution="Investigate root cause and consider server replacement",
            metadata={
                "server_name": "groq-llm",
                "failure_frequency": 0.5,  # failures per hour
                "failure_count": 4
            }
        )
        
        active_alert = SystemAlert(
            id="alert-pattern-123",
            severity=AlertSeverity.WARNING,
            title="Pattern Detected: recurring_failure",
            message="Server groq-llm has recurring failures every 2 hours",
            timestamp=datetime.now(),
            source="pattern_detection",
            metadata={
                "pattern_type": "recurring_failure",
                "confidence": 0.85,
                "affected_components": ["groq-llm"]
            },
            suggested_actions=["investigate_pattern", "apply_pattern_resolution"],
            acknowledged=False,
            resolved=False
        )
        
        mock_monitor = Mock()
        mock_monitor.get_detected_patterns.return_value = [detected_pattern]
        mock_monitor.get_active_alerts.return_value = [active_alert]
        mock_monitor.acknowledge_alert.return_value = True
        mock_monitor.resolve_alert.return_value = True
        mock_proactive_monitor.return_value = mock_monitor
        
        # Mock other services
        mock_health = Mock()
        mock_health.get_all_statuses = AsyncMock(return_value={})
        mock_health_monitor.return_value = mock_health
        
        mock_security = Mock()
        mock_security.get_ai_actionable_insights.return_value = []
        mock_security_manager.return_value = mock_security
        
        # Step 2: Get detected patterns
        response = self.client.get("/api/v1/monitoring/patterns")
        assert response.status_code == 200
        patterns_data = response.json()["data"]
        
        assert len(patterns_data) == 1
        pattern = patterns_data[0]
        assert pattern["pattern_type"] == "recurring_failure"
        assert pattern["confidence"] == 0.85
        assert "groq-llm" in pattern["affected_components"]
        assert pattern["frequency"] == 4
        
        # Step 3: Get active alerts
        response = self.client.get("/api/v1/monitoring/alerts")
        assert response.status_code == 200
        alerts_data = response.json()["data"]
        
        assert len(alerts_data) == 1
        alert = alerts_data[0]
        assert alert["severity"] == "warning"
        assert alert["title"] == "Pattern Detected: recurring_failure"
        assert "investigate_pattern" in alert["suggested_actions"]
        assert alert["acknowledged"] is False
        assert alert["resolved"] is False
        
        # Step 4: Acknowledge the alert
        alert_id = alert["id"]
        response = self.client.post(f"/api/v1/monitoring/alerts/{alert_id}/acknowledge")
        assert response.status_code == 200
        
        mock_monitor.acknowledge_alert.assert_called_once_with(alert_id)
        
        # Step 5: Resolve the alert
        response = self.client.post(f"/api/v1/monitoring/alerts/{alert_id}/resolve")
        assert response.status_code == 200
        
        mock_monitor.resolve_alert.assert_called_once_with(alert_id)
    
    @patch('backend.app.services.proactive_monitor.get_proactive_monitor')
    def test_e2e_connection_loss_analysis_scenario(self, mock_proactive_monitor):
        """
        E2E Test: Connection loss analysis and AI suggestions
        """
        
        # Mock proactive monitor
        mock_monitor = Mock()
        mock_monitor.analyze_connection_loss = AsyncMock(return_value={
            "component": "Backend API",
            "error_details": "Connection refused on port 8001",
            "timestamp": datetime.now().isoformat(),
            "possible_causes": [
                "Service is not running",
                "Port is blocked or changed"
            ],
            "suggested_solutions": [
                "restart_service",
                "check_port_configuration"
            ],
            "confidence": 0.8
        })
        mock_proactive_monitor.return_value = mock_monitor
        
        # Step 1: Analyze connection loss
        response = self.client.post("/api/v1/monitoring/analyze-connection-loss", json={
            "component": "Backend API",
            "error_details": "Connection refused on port 8001"
        })
        
        assert response.status_code == 200
        analysis = response.json()["data"]
        
        assert analysis["component"] == "Backend API"
        assert analysis["confidence"] == 0.8
        assert len(analysis["possible_causes"]) >= 1
        assert len(analysis["suggested_solutions"]) >= 1
        assert "restart_service" in analysis["suggested_solutions"]
        
        # Verify AI analysis was called
        mock_monitor.analyze_connection_loss.assert_called_once_with(
            "Backend API", 
            "Connection refused on port 8001"
        )
    
    def test_e2e_complete_ai_decision_workflow(self):
        """
        E2E Test: Complete AI decision-making workflow
        Detection → Analysis → Recommendation → Approval → Action → Verification
        """
        
        # This test combines multiple scenarios to test the complete workflow
        with patch('backend.app.services.health_monitor.get_health_monitor') as mock_health_monitor, \
             patch('backend.app.services.security_manager.get_security_manager') as mock_security_manager, \
             patch('backend.app.services.proactive_monitor.get_proactive_monitor') as mock_proactive_monitor:
            
            # Setup mocks for complete workflow
            self._setup_complete_workflow_mocks(
                mock_health_monitor, mock_security_manager, mock_proactive_monitor
            )
            
            # Step 1: Detection - System health check detects issues
            response = self.client.get("/api/v1/health/")
            assert response.status_code == 200
            health_data = response.json()["data"]
            assert health_data["status"] != "healthy"  # Issues detected
            
            # Step 2: Analysis - AI provides actionable insights
            insights = health_data["actionable_insights"]
            assert len(insights) > 0
            
            # Step 3: Recommendation - AI suggests actions
            high_priority_insight = next(
                (insight for insight in insights if insight["priority"] == "high"),
                insights[0]
            )
            assert high_priority_insight["suggested_action"] is not None
            
            # Step 4: Approval workflow (if needed)
            if not high_priority_insight["can_auto_fix"]:
                # Simulate approval process
                response = self.client.get("/api/v1/security/approvals")
                assert response.status_code == 200
            
            # Step 5: Action execution would happen here
            # (Tested in individual scenario tests)
            
            # Step 6: Verification - Check that system improved
            # (Would be tested with follow-up health checks)
    
    def _setup_complete_workflow_mocks(self, mock_health_monitor, mock_security_manager, mock_proactive_monitor):
        """Helper method to setup mocks for complete workflow test"""
        
        # Mock unhealthy system state
        mock_health = Mock()
        mock_health.get_all_statuses = AsyncMock(return_value={
            'groq-llm': HealthStatus(MCPServerStatus.OFFLINE, 0, datetime.now(), 0.0, "Connection lost"),
            'openrouter-llm': HealthStatus(MCPServerStatus.DEGRADED, 450, datetime.now(), 75.0, "High latency")
        })
        mock_health_monitor.return_value = mock_health
        
        # Mock security manager with insights and approval workflow
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
                "risk_level": "high"
            },
            {
                "id": "insight-2",
                "type": "warning", 
                "message": "MCP server openrouter-llm has high latency",
                "suggested_action": "investigate_processes",
                "server_name": "openrouter-llm",
                "priority": "medium",
                "can_auto_fix": True,
                "risk_level": "low"
            }
        ]
        mock_security.get_pending_approvals.return_value = []
        mock_security_manager.return_value = mock_security
        
        # Mock proactive monitor
        mock_monitor = Mock()
        mock_monitor.get_active_alerts.return_value = []
        mock_proactive_monitor.return_value = mock_monitor


if __name__ == '__main__':
    pytest.main([__file__])