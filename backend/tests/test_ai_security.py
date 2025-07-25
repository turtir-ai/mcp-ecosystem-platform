"""
Tests for AI Security Manager
"""

import pytest
from app.services.security_manager import SecurityManager, RiskLevel


class TestAISecurityManager:
    
    def setup_method(self):
        """Setup test security manager"""
        self.security_manager = SecurityManager()
    
    def test_ai_operation_risk_assessment(self):
        """Test risk assessment for AI operations"""
        
        # Safe operations
        can_perform, reason, risk = self.security_manager.can_ai_perform_operation('system_health_check')
        assert can_perform is True
        assert risk == RiskLevel.SAFE
        
        # Low risk operations
        can_perform, reason, risk = self.security_manager.can_ai_perform_operation('mcp_server_logs')
        assert can_perform is True
        assert risk == RiskLevel.LOW
        
        # High risk operations
        can_perform, reason, risk = self.security_manager.can_ai_perform_operation(
            'mcp_server_restart', 
            {'server_name': 'groq-llm'}
        )
        assert can_perform is False  # Requires approval
        assert risk == RiskLevel.HIGH
    
    def test_restricted_server_operations(self):
        """Test that restricted servers cannot be restarted by AI"""
        
        # Restricted server
        can_perform, reason, risk = self.security_manager.can_ai_perform_operation(
            'mcp_server_restart',
            {'server_name': 'kiro-tools'}
        )
        assert can_perform is False
        assert 'restricted' in reason.lower()
        assert risk == RiskLevel.CRITICAL
        
        # Allowed server (but still requires approval)
        can_perform, reason, risk = self.security_manager.can_ai_perform_operation(
            'mcp_server_restart',
            {'server_name': 'groq-llm'}
        )
        assert can_perform is False  # Still requires approval
        assert risk == RiskLevel.HIGH
    
    def test_ai_approval_request_creation(self):
        """Test AI approval request creation"""
        
        request = self.security_manager.create_ai_approval_request(
            'mcp_server_restart',
            {'server_name': 'groq-llm'},
            'Server appears unresponsive based on health check'
        )
        
        assert request['operation_type'] == 'mcp_server_restart'
        assert request['parameters']['server_name'] == 'groq-llm'
        assert request['ai_reasoning'] == 'Server appears unresponsive based on health check'
        assert request['status'] == 'pending'
        assert request['requester'] == 'AI_AGENT'
        assert 'operation_id' in request
    
    def test_actionable_insights_generation(self):
        """Test AI actionable insights generation"""
        
        # Mock system status with unhealthy server
        system_status = {
            'mcp_servers': {
                'unhealthy_servers': ['groq-llm', 'kiro-tools']
            },
            'resource_usage': {
                'cpu_percent': 85,
                'memory_percent': 90
            }
        }
        
        insights = self.security_manager.get_ai_actionable_insights(system_status)
        
        # Should have insights for both servers and resource usage
        assert len(insights) >= 3
        
        # Check server insights
        server_insights = [i for i in insights if 'server' in i.get('message', '')]
        assert len(server_insights) == 2
        
        # groq-llm should be auto-fixable, kiro-tools should not
        groq_insight = next(i for i in server_insights if i['server_name'] == 'groq-llm')
        kiro_insight = next(i for i in server_insights if i['server_name'] == 'kiro-tools')
        
        assert groq_insight['can_auto_fix'] is False  # Still requires approval
        assert kiro_insight['can_auto_fix'] is False  # Restricted
        
        # Check resource insights
        resource_insights = [i for i in insights if 'usage' in i.get('message', '')]
        assert len(resource_insights) >= 2
    
    def test_approval_workflow(self):
        """Test complete approval workflow"""
        
        # Create approval request
        request = self.security_manager.create_ai_approval_request(
            'mcp_server_restart',
            {'server_name': 'groq-llm'}
        )
        
        operation_id = request['operation_id']
        
        # Check pending approvals
        pending = self.security_manager.get_pending_approvals()
        assert len(pending) == 1
        assert pending[0]['operation_id'] == operation_id
        
        # Approve operation
        approved = self.security_manager.approve_operation(operation_id, 'test_user')
        assert approved is True
        
        # Check approval status
        is_approved = self.security_manager.is_operation_approved(operation_id)
        assert is_approved is True
        
        # Check no longer in pending
        pending = self.security_manager.get_pending_approvals()
        assert len(pending) == 0


if __name__ == '__main__':
    pytest.main([__file__])