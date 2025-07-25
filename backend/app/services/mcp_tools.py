"""
MCP Tools for System Health Integration
Provides tools that can be used by other MCP servers to query system health
"""

import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from .health_monitor import get_health_monitor
from .security_manager import get_security_manager


class SystemHealthMCPTool:
    """MCP tool for system health queries"""
    
    def __init__(self):
        self.name = "get_system_health"
        self.description = "Get comprehensive system health information including MCP servers, resource usage, and AI insights"
        self.input_schema = {
            "type": "object",
            "properties": {
                "include_insights": {
                    "type": "boolean",
                    "description": "Whether to include AI actionable insights",
                    "default": True
                },
                "include_metrics": {
                    "type": "boolean", 
                    "description": "Whether to include resource usage metrics",
                    "default": True
                },
                "server_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of specific MCP servers to check",
                    "default": []
                }
            }
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the system health check"""
        try:
            include_insights = arguments.get("include_insights", True)
            include_metrics = arguments.get("include_metrics", True)
            server_filter = arguments.get("server_filter", [])
            
            health_monitor = get_health_monitor()
            security_manager = get_security_manager()
            
            # Get MCP server statuses
            mcp_statuses = await health_monitor.get_all_statuses()
            
            # Filter servers if requested
            if server_filter:
                mcp_statuses = {
                    name: status for name, status in mcp_statuses.items()
                    if name in server_filter
                }
            
            # Calculate MCP server health summary
            total_servers = len(mcp_statuses)
            healthy_servers = sum(1 for status in mcp_statuses.values() 
                                if status.status == "HEALTHY")
            unhealthy_servers = [name for name, status in mcp_statuses.items() 
                               if status.status != "HEALTHY"]
            
            # Build response
            response = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy" if len(unhealthy_servers) == 0 else "degraded" if len(unhealthy_servers) < total_servers * 0.5 else "unhealthy",
                "mcp_servers": {
                    "total_count": total_servers,
                    "healthy_count": healthy_servers,
                    "unhealthy_servers": unhealthy_servers,
                    "server_details": {
                        name: {
                            "status": status.status,
                            "response_time_ms": status.response_time_ms,
                            "uptime_percentage": status.uptime_percentage,
                            "last_check": status.last_check.isoformat() if status.last_check else None,
                            "error_message": status.error_message
                        }
                        for name, status in mcp_statuses.items()
                    }
                }
            }
            
            # Add resource metrics if requested
            if include_metrics:
                try:
                    import psutil
                    response["resource_usage"] = {
                        "cpu_percent": round(psutil.cpu_percent(interval=1), 1),
                        "memory_percent": round(psutil.virtual_memory().percent, 1),
                        "disk_usage_percent": round(psutil.disk_usage('/').percent, 1)
                    }
                except ImportError:
                    response["resource_usage"] = {
                        "cpu_percent": 0,
                        "memory_percent": 0,
                        "disk_usage_percent": 0,
                        "note": "psutil not available for resource monitoring"
                    }
            
            # Add AI insights if requested
            if include_insights:
                system_status = {
                    "mcp_servers": {
                        "unhealthy_servers": unhealthy_servers
                    },
                    "resource_usage": response.get("resource_usage", {})
                }
                
                insights = security_manager.get_ai_actionable_insights(system_status)
                response["actionable_insights"] = insights
            
            return {
                "success": True,
                "data": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get system health: {str(e)}"
            }


class MCPServerControlTool:
    """MCP tool for controlling MCP servers"""
    
    def __init__(self):
        self.name = "restart_mcp_server"
        self.description = "Restart a specific MCP server (requires appropriate permissions)"
        self.input_schema = {
            "type": "object",
            "properties": {
                "server_name": {
                    "type": "string",
                    "description": "Name of the MCP server to restart"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Reason for restarting the server",
                    "default": "Manual restart requested"
                }
            },
            "required": ["server_name"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP server restart"""
        try:
            server_name = arguments["server_name"]
            reasoning = arguments.get("reasoning", "Manual restart requested")
            
            security_manager = get_security_manager()
            
            # Check if operation is allowed
            can_perform, reason, risk_level = security_manager.can_ai_perform_operation(
                'mcp_server_restart',
                {'server_name': server_name}
            )
            
            if not can_perform:
                return {
                    "success": False,
                    "error": f"Operation not allowed: {reason}",
                    "requires_approval": True,
                    "risk_level": risk_level.value
                }
            
            # Perform restart
            health_monitor = get_health_monitor()
            success = await health_monitor.force_restart_server(server_name)
            
            if success:
                # Log the operation
                security_manager.log_operation(
                    'mcp_restart_via_tool',
                    {'server_name': server_name, 'reasoning': reasoning},
                    'success',
                    risk_level,
                    'MCP_TOOL'
                )
                
                return {
                    "success": True,
                    "data": {
                        "message": f"Server {server_name} restarted successfully",
                        "server_name": server_name,
                        "reasoning": reasoning
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to restart server {server_name}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to restart MCP server: {str(e)}"
            }


class MCPToolRegistry:
    """Registry for MCP tools"""
    
    def __init__(self):
        self.tools = {
            "get_system_health": SystemHealthMCPTool(),
            "restart_mcp_server": MCPServerControlTool()
        }
    
    def get_tool(self, name: str):
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found"
            }
        
        return await tool.execute(arguments)


# Global registry instance
mcp_tool_registry = MCPToolRegistry()


def get_mcp_tool_registry() -> MCPToolRegistry:
    """Get the MCP tool registry"""
    return mcp_tool_registry


class AIDiagnosticsMCPTool:
    """MCP tool for AI-powered system diagnostics"""
    
    def __init__(self):
        self.name = "diagnose_system_issue"
        self.description = "AI-powered diagnosis of system issues with actionable recommendations"
        self.input_schema = {
            "type": "object",
            "properties": {
                "issue_description": {
                    "type": "string",
                    "description": "Description of the system issue to diagnose"
                },
                "error_details": {
                    "type": "object",
                    "description": "Optional error details including stack traces, error messages, etc.",
                    "default": {}
                },
                "system_context": {
                    "type": "object",
                    "description": "Current system context including health status, resource usage, etc.",
                    "default": {}
                }
            },
            "required": ["issue_description"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI diagnostics"""
        try:
            from .ai_diagnostics import get_ai_diagnostics_engine, SystemContext
            
            issue_description = arguments["issue_description"]
            error_details = arguments.get("error_details", {})
            system_context_data = arguments.get("system_context", {})
            
            # Build system context
            health_monitor = get_health_monitor()
            mcp_statuses = await health_monitor.get_all_statuses()
            
            system_context = SystemContext(
                current_health={'mcp_statuses': {name: status.status for name, status in mcp_statuses.items()}},
                recent_errors=[],
                resource_usage=system_context_data.get('resource_usage', {}),
                mcp_server_status={name: status.status for name, status in mcp_statuses.items()},
                user_activity=[],
                timestamp=datetime.now()
            )
            
            # Get AI diagnostics engine
            ai_engine = get_ai_diagnostics_engine()
            
            # Perform diagnosis
            diagnosis = await ai_engine.analyze_connection_error(
                error_details={
                    'issue_description': issue_description,
                    **error_details
                },
                system_context=system_context
            )
            
            return {
                "success": True,
                "diagnosis": {
                    "issue_type": diagnosis.issue_type,
                    "severity": diagnosis.severity.value,
                    "root_cause": diagnosis.root_cause_analysis,
                    "user_explanation": diagnosis.user_friendly_explanation,
                    "confidence": diagnosis.confidence_score,
                    "suggested_actions": [
                        {
                            "title": action.title,
                            "description": action.description,
                            "action_type": action.action_type.value,
                            "risk_level": action.risk_level,
                            "estimated_duration": action.estimated_duration,
                            "steps": action.steps
                        }
                        for action in diagnosis.suggested_actions
                    ]
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"AI diagnostics failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


class AIActionOrchestratorMCPTool:
    """MCP tool for AI action orchestration"""
    
    def __init__(self):
        self.name = "execute_ai_action"
        self.description = "Execute AI-suggested actions with security controls and approval workflow"
        self.input_schema = {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["mcp_server_restart", "system_cleanup", "performance_optimization", "diagnostic_analysis"],
                    "description": "Type of action to execute"
                },
                "parameters": {
                    "type": "object",
                    "description": "Action-specific parameters",
                    "default": {}
                },
                "reasoning": {
                    "type": "string",
                    "description": "AI reasoning for why this action is needed"
                },
                "force_approval": {
                    "type": "boolean",
                    "description": "Whether to force user approval regardless of risk level",
                    "default": False
                }
            },
            "required": ["action_type", "reasoning"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI action with security controls"""
        try:
            from .ai_orchestrator import get_ai_orchestrator, ActionType, ActionRequest
            from .security_manager import RiskLevel
            import uuid
            
            action_type_str = arguments["action_type"]
            parameters = arguments.get("parameters", {})
            reasoning = arguments["reasoning"]
            force_approval = arguments.get("force_approval", False)
            
            # Convert string to ActionType enum
            action_type = ActionType(action_type_str)
            
            # Determine risk level
            security_manager = get_security_manager()
            can_perform, reason, risk_level = security_manager.can_ai_perform_operation(
                action_type_str, parameters
            )
            
            # Create action request
            action_request = ActionRequest(
                id=str(uuid.uuid4()),
                action_type=action_type,
                title=f"AI Action: {action_type_str.replace('_', ' ').title()}",
                description=reasoning,
                parameters=parameters,
                risk_level=risk_level,
                estimated_duration="2-5 minutes",
                requires_approval=force_approval or not can_perform,
                created_at=datetime.now()
            )
            
            # Get orchestrator
            orchestrator = get_ai_orchestrator()
            
            if action_request.requires_approval:
                # Add to pending actions
                orchestrator.pending_actions[action_request.id] = action_request
                
                return {
                    "success": True,
                    "action_id": action_request.id,
                    "status": "pending_approval",
                    "message": "Action created and pending user approval",
                    "approval_required": True,
                    "risk_level": risk_level.value,
                    "reason": reason
                }
            else:
                # Execute immediately
                await orchestrator._execute_action(action_request)
                
                return {
                    "success": True,
                    "action_id": action_request.id,
                    "status": "executing",
                    "message": "Action started successfully"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute AI action: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


class AIRemediationMCPTool:
    """MCP tool for AI-powered remediation suggestions"""
    
    def __init__(self):
        self.name = "suggest_remediation"
        self.description = "Generate AI-powered remediation suggestions for system issues"
        self.input_schema = {
            "type": "object",
            "properties": {
                "diagnosis_result": {
                    "type": "object",
                    "description": "Diagnosis result from AI diagnostics",
                    "properties": {
                        "issue_type": {"type": "string"},
                        "severity": {"type": "string"},
                        "root_cause": {"type": "string"},
                        "confidence": {"type": "number"}
                    },
                    "required": ["issue_type", "severity"]
                },
                "system_constraints": {
                    "type": "object",
                    "description": "System constraints to consider for remediation",
                    "default": {}
                },
                "user_preferences": {
                    "type": "object",
                    "description": "User preferences for remediation approach",
                    "default": {}
                }
            },
            "required": ["diagnosis_result"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate remediation suggestions"""
        try:
            from .ai_diagnostics import get_ai_diagnostics_engine, DiagnosisResult, IssueSeverity
            
            diagnosis_data = arguments["diagnosis_result"]
            system_constraints = arguments.get("system_constraints", {})
            user_preferences = arguments.get("user_preferences", {})
            
            # Reconstruct diagnosis result
            diagnosis = DiagnosisResult(
                issue_type=diagnosis_data["issue_type"],
                severity=IssueSeverity(diagnosis_data["severity"]),
                root_cause_analysis=diagnosis_data.get("root_cause", ""),
                user_friendly_explanation="",
                confidence_score=diagnosis_data.get("confidence", 0.5),
                suggested_actions=[],
                learning_data={}
            )
            
            # Get AI diagnostics engine
            ai_engine = get_ai_diagnostics_engine()
            
            # Generate remediation suggestions
            remediation_actions = await ai_engine.suggest_remediation(diagnosis)
            
            return {
                "success": True,
                "remediation_suggestions": [
                    {
                        "title": action.title,
                        "description": action.description,
                        "action_type": action.action_type.value,
                        "risk_level": action.risk_level,
                        "estimated_duration": action.estimated_duration,
                        "steps": action.steps,
                        "automation_available": action.automation_script is not None
                    }
                    for action in remediation_actions
                ],
                "constraints_considered": system_constraints,
                "preferences_applied": user_preferences,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate remediation suggestions: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


# Tool registry
MCP_TOOLS = [
    SystemHealthMCPTool(),
    AIDiagnosticsMCPTool(),
    AIActionOrchestratorMCPTool(),
    AIRemediationMCPTool()
]


def get_mcp_tools() -> List[Dict[str, Any]]:
    """Get all available MCP tools"""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        }
        for tool in MCP_TOOLS
    ]


async def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a specific MCP tool"""
    for tool in MCP_TOOLS:
        if tool.name == tool_name:
            return await tool.execute(arguments)
    
    raise ValueError(f"Tool '{tool_name}' not found")