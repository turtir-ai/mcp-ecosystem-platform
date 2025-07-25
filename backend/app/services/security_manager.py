"""
Security Manager for MCP Ecosystem Platform

This module provides security controls and approval mechanisms for dangerous operations.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk levels for operations"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityManager:
    """Manages security policies and approval workflows"""
    
    def __init__(self):
        self.dangerous_commands = {
            # File system operations
            r'rm\s+-rf': RiskLevel.CRITICAL,
            r'del\s+/[sq]': RiskLevel.CRITICAL,
            r'format\s+[a-z]:': RiskLevel.CRITICAL,
            r'rmdir\s+/s': RiskLevel.HIGH,
            
            # Git operations
            r'git\s+push\s+--force': RiskLevel.HIGH,
            r'git\s+reset\s+--hard': RiskLevel.MEDIUM,
            r'git\s+clean\s+-fd': RiskLevel.MEDIUM,
            
            # System operations
            r'shutdown': RiskLevel.CRITICAL,
            r'reboot': RiskLevel.CRITICAL,
            r'sudo': RiskLevel.HIGH,
            r'chmod\s+777': RiskLevel.HIGH,
            
            # Network operations
            r'curl.*-X\s+DELETE': RiskLevel.MEDIUM,
            r'wget.*--delete-after': RiskLevel.MEDIUM,
        }
        
        # AI-specific operations and their risk levels
        self.ai_operations = {
            'mcp_server_restart': RiskLevel.HIGH,
            'mcp_server_stop': RiskLevel.HIGH,
            'mcp_server_logs': RiskLevel.LOW,
            'system_health_check': RiskLevel.SAFE,
            'database_restart': RiskLevel.CRITICAL,
            'config_modify': RiskLevel.HIGH,
            'auto_fix_apply': RiskLevel.MEDIUM,
        }
        
        self.protected_paths = [
            r'C:\\Windows\\System32',
            r'C:\\Program Files',
            r'/etc',
            r'/usr/bin',
            r'/System',
            r'\.git/config',
            r'\.env',
            r'\.kiro/settings'
        ]
        
        self.auto_approved_operations = set()
        self.pending_approvals: Dict[str, Dict] = {}
    
    def assess_risk(self, operation: str, tool_name: str, parameters: Dict) -> Tuple[RiskLevel, str]:
        """Assess the risk level of an operation"""
        
        # Check AI-specific operations first
        if operation in self.ai_operations:
            risk_level = self.ai_operations[operation]
            return risk_level, f"AI operation: {operation}"
        
        # Check for dangerous commands
        for pattern, risk_level in self.dangerous_commands.items():
            if re.search(pattern, operation, re.IGNORECASE):
                return risk_level, f"Dangerous command pattern detected: {pattern}"
        
        # Check for protected paths
        if 'path' in parameters:
            path = str(parameters['path'])
            for protected_pattern in self.protected_paths:
                if re.search(protected_pattern, path, re.IGNORECASE):
                    return RiskLevel.HIGH, f"Protected path access: {path}"
        
        # Tool-specific risk assessment
        if tool_name in ['write_file', 'execute_command']:
            return RiskLevel.MEDIUM, "File system modification or command execution"
        
        if tool_name in ['git_push', 'git_reset']:
            return RiskLevel.MEDIUM, "Git repository modification"
        
        # MCP server operations
        if tool_name.startswith('mcp_'):
            if 'restart' in tool_name or 'stop' in tool_name:
                return RiskLevel.HIGH, "MCP server control operation"
            elif 'logs' in tool_name:
                return RiskLevel.LOW, "MCP server log access"
        
        return RiskLevel.SAFE, "Operation appears safe"
    
    def requires_approval(self, risk_level: RiskLevel) -> bool:
        """Check if operation requires user approval"""
        return risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def create_approval_request(self, operation_id: str, tool_name: str, 
                             parameters: Dict, risk_level: RiskLevel, 
                             reason: str) -> Dict:
        """Create an approval request for dangerous operations"""
        
        request = {
            'operation_id': operation_id,
            'tool_name': tool_name,
            'parameters': parameters,
            'risk_level': risk_level.value,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        self.pending_approvals[operation_id] = request
        logger.warning(f"Approval required for {tool_name}: {reason}")
        
        return request
    
    def approve_operation(self, operation_id: str, user_id: str = "system") -> bool:
        """Approve a pending operation"""
        if operation_id in self.pending_approvals:
            self.pending_approvals[operation_id]['status'] = 'approved'
            self.pending_approvals[operation_id]['approved_by'] = user_id
            self.pending_approvals[operation_id]['approved_at'] = datetime.now().isoformat()
            logger.info(f"Operation {operation_id} approved by {user_id}")
            return True
        return False
    
    def reject_operation(self, operation_id: str, user_id: str = "system", reason: str = "") -> bool:
        """Reject a pending operation"""
        if operation_id in self.pending_approvals:
            self.pending_approvals[operation_id]['status'] = 'rejected'
            self.pending_approvals[operation_id]['rejected_by'] = user_id
            self.pending_approvals[operation_id]['rejected_at'] = datetime.now().isoformat()
            self.pending_approvals[operation_id]['rejection_reason'] = reason
            logger.info(f"Operation {operation_id} rejected by {user_id}: {reason}")
            return True
        return False
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approval requests"""
        return [req for req in self.pending_approvals.values() if req['status'] == 'pending']
    
    def is_operation_approved(self, operation_id: str) -> bool:
        """Check if operation is approved"""
        return (operation_id in self.pending_approvals and 
                self.pending_approvals[operation_id]['status'] == 'approved')
    
    def sanitize_parameters(self, tool_name: str, parameters: Dict) -> Dict:
        """Sanitize parameters to prevent injection attacks"""
        sanitized = parameters.copy()
        
        # Remove potentially dangerous characters from file paths
        if 'path' in sanitized:
            path = str(sanitized['path'])
            # Remove path traversal attempts
            path = path.replace('..', '').replace('//', '/').replace('\\\\', '\\')
            sanitized['path'] = path
        
        # Sanitize command strings
        if 'command' in sanitized:
            command = str(sanitized['command'])
            # Remove dangerous characters
            dangerous_chars = ['|', '&', ';', '`', '$', '(', ')', '{', '}']
            for char in dangerous_chars:
                command = command.replace(char, '')
            sanitized['command'] = command
        
        return sanitized
    
    def log_operation(self, tool_name: str, parameters: Dict, result: str, 
                     risk_level: RiskLevel, user_id: str = "system"):
        """Log all operations for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'tool_name': tool_name,
            'parameters': parameters,
            'result': result[:500] if len(result) > 500 else result,  # Truncate long results
            'risk_level': risk_level.value,
            'user_id': user_id
        }
        
        # In production, this should go to a secure audit log
        logger.info(f"AUDIT: {json.dumps(log_entry)}")
    
    def can_ai_perform_operation(self, operation: str, parameters: Dict = None) -> Tuple[bool, str, RiskLevel]:
        """Check if AI can perform an operation based on current permissions"""
        if parameters is None:
            parameters = {}
            
        risk_level, reason = self.assess_risk(operation, operation, parameters)
        
        # Check AI-specific rules
        if operation in ['mcp_server_restart', 'mcp_server_stop']:
            server_name = parameters.get('server_name', '')
            
            # Check if server is in restricted list
            restricted_servers = ['kiro-tools', 'simple-warp']
            if server_name in restricted_servers:
                return False, f"Server {server_name} is restricted for AI operations", RiskLevel.CRITICAL
        
        # Auto-approve safe operations
        if risk_level == RiskLevel.SAFE:
            return True, "Operation is safe for AI", risk_level
        
        # Low risk operations can be auto-approved in development
        if risk_level == RiskLevel.LOW:
            return True, "Low risk operation approved", risk_level
        
        # Medium and above require approval
        return False, f"Operation requires user approval: {reason}", risk_level
    
    def create_ai_approval_request(self, operation: str, parameters: Dict, 
                                 ai_reasoning: str = "") -> Dict:
        """Create an approval request specifically for AI operations"""
        import uuid
        
        operation_id = str(uuid.uuid4())
        risk_level, reason = self.assess_risk(operation, operation, parameters)
        
        request = {
            'operation_id': operation_id,
            'operation_type': operation,
            'parameters': parameters,
            'risk_level': risk_level.value,
            'reason': reason,
            'ai_reasoning': ai_reasoning,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'requester': 'AI_AGENT',
            'timeout_minutes': 5 if risk_level == RiskLevel.HIGH else 2
        }
        
        self.pending_approvals[operation_id] = request
        logger.warning(f"AI approval required for {operation}: {reason}")
        
        return request
    
    def get_ai_actionable_insights(self, system_status: Dict) -> List[Dict]:
        """Generate actionable insights for AI based on system status"""
        insights = []
        
        # Check for unhealthy MCP servers
        if 'mcp_servers' in system_status:
            mcp_status = system_status['mcp_servers']
            if isinstance(mcp_status, dict) and 'unhealthy_servers' in mcp_status:
                for server in mcp_status['unhealthy_servers']:
                    can_restart, reason, risk = self.can_ai_perform_operation(
                        'mcp_server_restart', 
                        {'server_name': server}
                    )
                    
                    insights.append({
                        'type': 'warning',
                        'message': f"MCP server '{server}' is unhealthy",
                        'suggested_action': 'mcp_server_restart' if can_restart else 'manual_intervention',
                        'server_name': server,
                        'can_auto_fix': can_restart,
                        'risk_level': risk.value,
                        'reasoning': reason
                    })
        
        # Check resource usage
        if 'resource_usage' in system_status:
            resources = system_status['resource_usage']
            
            if resources.get('cpu_percent', 0) > 80:
                insights.append({
                    'type': 'warning',
                    'message': f"High CPU usage: {resources['cpu_percent']}%",
                    'suggested_action': 'investigate_processes',
                    'can_auto_fix': False,
                    'risk_level': 'medium',
                    'reasoning': 'High resource usage requires investigation'
                })
            
            if resources.get('memory_percent', 0) > 85:
                insights.append({
                    'type': 'error',
                    'message': f"High memory usage: {resources['memory_percent']}%",
                    'suggested_action': 'restart_services',
                    'can_auto_fix': False,
                    'risk_level': 'high',
                    'reasoning': 'Memory pressure may cause system instability'
                })
        
        return insights


# Singleton instance
_security_manager = None


def get_security_manager() -> SecurityManager:
    """Get security manager singleton"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager