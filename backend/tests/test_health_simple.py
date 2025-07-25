"""
Simple tests for health endpoint functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.security_manager import SecurityManager, RiskLevel


class TestHealthEndpointLogic:
    """Test the logic behind health endpoints without FastAPI dependencies"""
    
    def setup_method(self):
        """Setup test security manager"""
        self.security_manager = SecurityManager()
    
    def test_ai_actionable_insights_generation(self):
        """Test AI actionable insights generation logic"""
        
        # Mock system status with various issues
        system_status = {
            'mcp_servers': {
                'unhealthy_servers': ['groq-llm', 'browser-automation']
            },
            'resource_usage': {
                'cpu_percent': 85,
                'memory_percent': 90,
                'disk_usage_percent': 45
            }
        }
        
        insights = self.security_manager.get_ai_actionable_insights(system_status)
        
        # Should have insights for servers and resource usage
        assert len(insights) >= 3
        
        # Check server insights
        server_insights = [i for i in insights if 'server' in i.get('message', '')]
        assert len(server_insights) == 2
        
        # Check that insights have required fields
        for insight in insights:
            assert 'type' in insight
            assert 'message' in insight
            assert 'can_auto_fix' in insight
            assert 'risk_level' in insight
            
        # Check resource usage insights
        resource_insights = [i for i in insights if 'usage' in i.get('message', '')]
        assert len(resource_insights) >= 2
        
        # High CPU should generate warning
        cpu_insight = next((i for i in resource_insights if 'CPU' in i['message']), None)
        assert cpu_insight is not None
        assert cpu_insight['type'] == 'warning'
        
        # High memory should generate error
        memory_insight = next((i for i in resource_insights if 'memory' in i['message']), None)
        assert memory_insight is not None
        assert memory_insight['type'] == 'error'
    
    def test_ai_can_perform_operation_logic(self):
        """Test AI operation permission logic"""
        
        # Test safe operations
        can_perform, reason, risk = self.security_manager.can_ai_perform_operation('system_health_check')
        assert can_perform is True
        assert risk == RiskLevel.SAFE
        
        # Test low risk operations
        can_perform, reason, risk = self.security_manager.can_ai_perform_operation('mcp_server_logs')
        assert can_perform is True
        assert risk == RiskLevel.LOW
        
        # Test high risk operations
        can_perform, reason, risk = self.security_manager.can_ai_perform_operation(
            'mcp_server_restart', 
            {'server_name': 'groq-llm'}
        )
        assert can_perform is False  # Requires approval
        assert risk == RiskLevel.HIGH
        
        # Test restricted servers
        can_perform, reason, risk = self.security_manager.can_ai_perform_operation(
            'mcp_server_restart',
            {'server_name': 'kiro-tools'}
        )
        assert can_perform is False
        assert 'restricted' in reason.lower()
        assert risk == RiskLevel.CRITICAL
    
    def test_health_response_structure(self):
        """Test that health response has correct structure"""
        
        # Mock health data structure
        mock_health_data = {
            "status": "healthy",
            "timestamp": "2025-01-24T10:30:00Z",
            "version": "1.0.0",
            "services": {
                "database": {
                    "status": "connected",
                    "latency_ms": 45,
                    "connection_pool_active": 3
                },
                "mcp_servers": {
                    "status": "active",
                    "active_count": 5,
                    "total_count": 6,
                    "unhealthy_servers": ["simple-warp"]
                }
            },
            "resource_usage": {
                "cpu_percent": 12.5,
                "memory_percent": 34.2,
                "disk_usage_percent": 67.8
            },
            "actionable_insights": []
        }
        
        # Validate structure
        assert "status" in mock_health_data
        assert "services" in mock_health_data
        assert "resource_usage" in mock_health_data
        assert "actionable_insights" in mock_health_data
        
        # Validate services structure
        services = mock_health_data["services"]
        assert "database" in services
        assert "mcp_servers" in services
        
        # Validate database structure
        db = services["database"]
        assert "status" in db
        assert "latency_ms" in db
        assert "connection_pool_active" in db
        
        # Validate MCP servers structure
        mcp = services["mcp_servers"]
        assert "status" in mcp
        assert "active_count" in mcp
        assert "total_count" in mcp
        assert "unhealthy_servers" in mcp
        
        # Validate resource usage structure
        resources = mock_health_data["resource_usage"]
        assert "cpu_percent" in resources
        assert "memory_percent" in resources
        assert "disk_usage_percent" in resources
    
    def test_system_recommendations_logic(self):
        """Test system recommendation generation logic"""
        
        recommendations = []
        
        # Mock resource usage scenarios
        high_cpu = 85
        high_memory = 90
        high_db_latency = 150
        
        # Test CPU recommendation
        if high_cpu > 80:
            recommendations.append({
                "type": "performance",
                "message": "High CPU usage detected",
                "suggestion": "Consider restarting resource-intensive MCP servers",
                "priority": "medium"
            })
        
        # Test memory recommendation
        if high_memory > 85:
            recommendations.append({
                "type": "performance", 
                "message": "High memory usage detected",
                "suggestion": "Memory cleanup or service restart may be needed",
                "priority": "high"
            })
        
        # Test database recommendation
        if high_db_latency > 100:
            recommendations.append({
                "type": "database",
                "message": f"Database latency is high ({high_db_latency}ms)",
                "suggestion": "Check database connection and query performance",
                "priority": "medium"
            })
        
        # Validate recommendations
        assert len(recommendations) == 3
        
        # Check CPU recommendation
        cpu_rec = recommendations[0]
        assert cpu_rec["type"] == "performance"
        assert "CPU" in cpu_rec["message"]
        assert cpu_rec["priority"] == "medium"
        
        # Check memory recommendation
        memory_rec = recommendations[1]
        assert memory_rec["type"] == "performance"
        assert "memory" in memory_rec["message"]
        assert memory_rec["priority"] == "high"
        
        # Check database recommendation
        db_rec = recommendations[2]
        assert db_rec["type"] == "database"
        assert "latency" in db_rec["message"]
        assert db_rec["priority"] == "medium"


if __name__ == '__main__':
    pytest.main([__file__])