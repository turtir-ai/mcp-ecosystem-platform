"""
API Routes for MCP Ecosystem Platform

This module contains all API route definitions.
"""

from .research_routes import router as research_router
from .workflow_routes import router as workflow_router
from .privacy_routes import router as privacy_router
from .network_routes import router as network_router
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
import asyncio
from datetime import datetime

from ..core.interfaces import APIResponse, HealthStatus, MCPServerConfig
from ..services.health_monitor import get_health_monitor
from ..services.config_manager import get_config_manager
from ..services.mcp_client import get_mcp_client_manager
from ..services.smart_git_reviewer import get_smart_git_reviewer
from ..services.git_analyzer import GitAnalyzer
from ..services.security_manager import get_security_manager

logger = logging.getLogger(__name__)

# Create main API router
api_router = APIRouter()

# MCP Management Routes
mcp_router = APIRouter(prefix="/mcp", tags=["MCP Management"])


@mcp_router.get("/status")
async def get_mcp_status() -> APIResponse:
    """Get status of all MCP servers"""
    try:
        health_monitor = get_health_monitor()
        statuses = await health_monitor.get_all_statuses()

        return APIResponse(
            success=True,
            data=statuses
        )

    except Exception as e:
        logger.error(f"Failed to get MCP status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get MCP server status")


@mcp_router.get("/status/{server_name}")
async def get_server_status(server_name: str) -> APIResponse:
    """Get status of a specific MCP server"""
    try:
        health_monitor = get_health_monitor()
        status = await health_monitor.get_server_status(server_name)

        return APIResponse(
            success=True,
            data=status
        )

    except Exception as e:
        logger.error(f"Failed to get status for {server_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get status for {server_name}")


@mcp_router.get("/tools/{server_name}")
async def get_server_tools(server_name: str) -> APIResponse:
    """Get available tools for a specific MCP server"""
    try:
        client_manager = get_mcp_client_manager()
        client = client_manager.get_client(server_name)

        if not client:
            raise HTTPException(
                status_code=404, detail=f"Server {server_name} not found")

        tools = await client.list_tools()

        return APIResponse(
            success=True,
            data=tools
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tools for {server_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get tools for {server_name}")


@mcp_router.post("/restart/{server_name}")
async def restart_server(server_name: str) -> APIResponse:
    """Force restart a specific MCP server"""
    try:
        health_monitor = get_health_monitor()
        success = await health_monitor.force_restart_server(server_name)

        if not success:
            raise HTTPException(
                status_code=400, detail=f"Failed to restart {server_name}")

        return APIResponse(
            success=True,
            data={"message": f"Server {server_name} restarted successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart {server_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to restart {server_name}")


@mcp_router.get("/metrics")
async def get_mcp_metrics() -> APIResponse:
    """Get detailed metrics for all MCP servers"""
    try:
        health_monitor = get_health_monitor()
        metrics = health_monitor.get_all_metrics()

        # Convert metrics to serializable format
        metrics_data = {}
        for server_name, server_metrics in metrics.items():
            metrics_data[server_name] = {
                "total_checks": server_metrics.total_checks,
                "total_failures": server_metrics.total_failures,
                "consecutive_failures": server_metrics.consecutive_failures,
                "uptime_percentage": server_metrics.get_uptime_percentage(),
                "average_response_time": server_metrics.get_average_response_time(),
                "p95_response_time": server_metrics.get_p95_response_time(),
                "restart_count": server_metrics.restart_count,
                "last_successful_check": server_metrics.last_successful_check,
                "last_failed_check": server_metrics.last_failed_check
            }

        return APIResponse(
            success=True,
            data=metrics_data
        )

    except Exception as e:
        logger.error(f"Failed to get MCP metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get MCP metrics")


# Configuration Management Routes
config_router = APIRouter(prefix="/config", tags=["Configuration"])


@config_router.get("/servers")
async def list_server_configs() -> APIResponse:
    """List all MCP server configurations"""
    try:
        config_manager = get_config_manager()
        configs = config_manager.list_configurations()

        return APIResponse(
            success=True,
            data=configs
        )

    except Exception as e:
        logger.error(f"Failed to list server configs: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to list server configurations")


@config_router.get("/servers/{server_name}")
async def get_server_config(server_name: str) -> APIResponse:
    """Get configuration for a specific server"""
    try:
        config_manager = get_config_manager()
        config = config_manager.get_configuration(server_name)

        if not config:
            raise HTTPException(
                status_code=404, detail=f"Configuration for {server_name} not found")

        return APIResponse(
            success=True,
            data=config
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config for {server_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get configuration for {server_name}")


@config_router.put("/servers/{server_name}")
async def update_server_config(server_name: str, updates: Dict[str, Any]) -> APIResponse:
    """Update configuration for a specific server"""
    try:
        config_manager = get_config_manager()
        updated_config = await config_manager.update_configuration(server_name, updates)

        return APIResponse(
            success=True,
            data=updated_config
        )

    except Exception as e:
        logger.error(f"Failed to update config for {server_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update configuration for {server_name}")


@config_router.post("/servers")
async def create_server_config(config: MCPServerConfig) -> APIResponse:
    """Create a new server configuration"""
    try:
        config_manager = get_config_manager()
        await config_manager.save_configuration(config)

        return APIResponse(
            success=True,
            data=config
        )

    except Exception as e:
        logger.error(f"Failed to create server config: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create server configuration")


@config_router.delete("/servers/{server_name}")
async def delete_server_config(server_name: str) -> APIResponse:
    """Delete a server configuration"""
    try:
        config_manager = get_config_manager()
        success = await config_manager.delete_configuration(server_name)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Configuration for {server_name} not found")

        return APIResponse(
            success=True,
            data={"message": f"Configuration for {server_name} deleted successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete config for {server_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete configuration for {server_name}")


# Tool Execution Routes
tools_router = APIRouter(prefix="/tools", tags=["Tool Execution"])


@tools_router.post("/execute/{server_name}/{tool_name}")
async def execute_tool(
    server_name: str,
    tool_name: str,
    arguments: Dict[str, Any]
) -> APIResponse:
    """Execute a tool on a specific MCP server with security controls"""
    try:
        # Security check
        security_manager = get_security_manager()
        
        # Create operation string for risk assessment
        operation = f"{tool_name} with {arguments}"
        risk_level, reason = security_manager.assess_risk(operation, tool_name, arguments)
        
        # Check if approval is required
        if security_manager.requires_approval(risk_level):
            import uuid
            operation_id = str(uuid.uuid4())
            
            approval_request = security_manager.create_approval_request(
                operation_id, tool_name, arguments, risk_level, reason
            )
            
            return APIResponse(
                success=False,
                error="Approval required for this operation",
                data={
                    "approval_required": True,
                    "operation_id": operation_id,
                    "risk_level": risk_level.value,
                    "reason": reason,
                    "approval_request": approval_request
                }
            )
        
        # Sanitize parameters
        sanitized_args = security_manager.sanitize_parameters(tool_name, arguments)
        
        # Execute the tool
        client_manager = get_mcp_client_manager()
        client = client_manager.get_client(server_name)

        if not client:
            raise HTTPException(
                status_code=404, detail=f"Server {server_name} not found")

        result = await client.call_tool(tool_name, sanitized_args)
        
        # Log the operation
        security_manager.log_operation(tool_name, sanitized_args, str(result), risk_level)

        return APIResponse(
            success=True,
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to execute tool {tool_name} on {server_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute tool {tool_name} on {server_name}"
        )


# Import workflow and research routes

# Git Review Routes
git_router = APIRouter(prefix="/git", tags=["Git Review"])


@git_router.get("/repositories")
async def get_repositories() -> APIResponse:
    """Get available Git repositories"""
    try:
        git_analyzer = GitAnalyzer()
        repositories = await git_analyzer.get_repositories()

        return APIResponse(
            success=True,
            data=repositories
        )
    except Exception as e:
        logger.error(f"Failed to get repositories: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get repositories")


@git_router.get("/status")
async def get_git_status() -> APIResponse:
    """Get Git status for current repository"""
    try:
        git_analyzer = GitAnalyzer()
        status = await git_analyzer.get_git_status()

        return APIResponse(
            success=True,
            data=status
        )
    except Exception as e:
        logger.error(f"Failed to get git status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get git status")


@git_router.get("/diff")
async def get_git_diff(staged: bool = False) -> APIResponse:
    """Get Git diff"""
    try:
        git_analyzer = GitAnalyzer()
        diff = await git_analyzer.get_git_diff(staged=staged)

        return APIResponse(
            success=True,
            data=diff
        )
    except Exception as e:
        logger.error(f"Failed to get git diff: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get git diff")


@git_router.post("/review")
async def start_git_review(request: Dict[str, Any]) -> APIResponse:
    """Start a Git review"""
    try:
        smart_reviewer = get_smart_git_reviewer()
        review_result = await smart_reviewer.start_review(
            repository_id=request.get("repositoryId"),
            review_type=request.get("reviewType", "full")
        )

        return APIResponse(
            success=True,
            data=review_result
        )
    except Exception as e:
        logger.error(f"Failed to start git review: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to start git review")


@git_router.get("/review/{review_id}/results")
async def get_review_results(review_id: str) -> APIResponse:
    """Get results of a specific review"""
    try:
        # Check for invalid review ID
        if review_id == "undefined" or not review_id or review_id.strip() == "":
            logger.warning(f"Invalid review ID received: '{review_id}' - blocking request")
            raise HTTPException(
                status_code=400, 
                detail="Invalid review ID provided"
            )
            
        smart_reviewer = get_smart_git_reviewer()
        results = await smart_reviewer.get_review_results(review_id)

        return APIResponse(
            success=True,
            data=results
        )
    except ValueError as e:
        logger.error(f"Review not found: {e}")
        raise HTTPException(
            status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review results: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get review results")


@git_router.get("/review/history")
async def get_review_history(limit: int = 20) -> APIResponse:
    """Get review history"""
    try:
        smart_reviewer = get_smart_git_reviewer()
        history = await smart_reviewer.get_review_history(limit=limit)

        return APIResponse(
            success=True,
            data=history
        )
    except Exception as e:
        logger.error(f"Failed to get review history: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get review history")


@git_router.get("/review/{review_id}/report")
async def download_review_report(review_id: str) -> APIResponse:
    """Download review report"""
    try:
        smart_reviewer = get_smart_git_reviewer()
        report = await smart_reviewer.get_review_report(review_id)

        return APIResponse(
            success=True,
            data=report
        )
    except Exception as e:
        logger.error(f"Failed to get review report: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get review report")


# Security Routes
security_router = APIRouter(prefix="/security", tags=["Security"])


@security_router.get("/approvals")
async def get_pending_approvals() -> APIResponse:
    """Get all pending approval requests"""
    try:
        security_manager = get_security_manager()
        approvals = security_manager.get_pending_approvals()
        
        return APIResponse(
            success=True,
            data=approvals
        )
    except Exception as e:
        logger.error(f"Failed to get pending approvals: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get pending approvals")


@security_router.post("/approve/{operation_id}")
async def approve_operation(operation_id: str, user_id: str = "system") -> APIResponse:
    """Approve a pending operation"""
    try:
        security_manager = get_security_manager()
        success = security_manager.approve_operation(operation_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Operation {operation_id} not found")
        
        return APIResponse(
            success=True,
            data={"message": f"Operation {operation_id} approved"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve operation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to approve operation")


@security_router.post("/reject/{operation_id}")
async def reject_operation(operation_id: str, user_id: str = "system", reason: str = "") -> APIResponse:
    """Reject a pending operation"""
    try:
        security_manager = get_security_manager()
        success = security_manager.reject_operation(operation_id, user_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Operation {operation_id} not found")
        
        return APIResponse(
            success=True,
            data={"message": f"Operation {operation_id} rejected"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject operation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to reject operation")


# System Health Routes
health_router = APIRouter(prefix="/health", tags=["System Health"])


@health_router.get("/")
async def get_system_health() -> APIResponse:
    """Get comprehensive system health with AI actionable insights"""
    try:
        import psutil
        import time
        from datetime import datetime
        
        health_monitor = get_health_monitor()
        security_manager = get_security_manager()
        
        # Get MCP server statuses
        mcp_statuses = await health_monitor.get_all_statuses()
        
        # Calculate MCP server health summary
        total_servers = len(mcp_statuses)
        healthy_servers = sum(1 for status in mcp_statuses.values() 
                            if status.status == "HEALTHY")
        unhealthy_servers = [name for name, status in mcp_statuses.items() 
                           if status.status != "HEALTHY"]
        
        # Get system resource usage
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            resource_usage = {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "disk_usage_percent": round(disk.percent, 1),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
        except Exception as e:
            logger.warning(f"Could not get system resources: {e}")
            resource_usage = {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_usage_percent": 0,
                "memory_available_gb": 0,
                "disk_free_gb": 0
            }
        
        # Mock database latency check
        db_start = time.time()
        try:
            # In real implementation, this would be an actual DB query
            await asyncio.sleep(0.05)  # Simulate DB query
            db_latency_ms = round((time.time() - db_start) * 1000, 1)
            db_status = "connected"
            db_connection_pool_active = 3
        except Exception as e:
            db_latency_ms = 0
            db_status = "disconnected"
            db_connection_pool_active = 0
        
        # Determine overall system status
        overall_status = "healthy"
        if len(unhealthy_servers) > total_servers * 0.5:
            overall_status = "unhealthy"
        elif len(unhealthy_servers) > 0 or resource_usage["cpu_percent"] > 80:
            overall_status = "degraded"
        
        # Build system status for AI insights
        system_status = {
            "mcp_servers": {
                "status": "active" if healthy_servers > 0 else "inactive",
                "active_count": healthy_servers,
                "total_count": total_servers,
                "unhealthy_servers": unhealthy_servers
            },
            "resource_usage": resource_usage
        }
        
        # Get AI actionable insights
        actionable_insights = security_manager.get_ai_actionable_insights(system_status)
        
        # Build comprehensive health response
        health_response = {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "database": {
                    "status": db_status,
                    "latency_ms": db_latency_ms,
                    "connection_pool_active": db_connection_pool_active
                },
                "mcp_servers": {
                    "status": "active" if healthy_servers > 0 else "inactive",
                    "active_count": healthy_servers,
                    "total_count": total_servers,
                    "unhealthy_servers": unhealthy_servers,
                    "server_details": {
                        name: {
                            "status": status.status,
                            "response_time_ms": status.response_time_ms,
                            "uptime_percentage": status.uptime_percentage,
                            "last_check": status.last_check.isoformat(),
                            "error_message": status.error_message
                        }
                        for name, status in mcp_statuses.items()
                    }
                }
            },
            "resource_usage": resource_usage,
            "actionable_insights": actionable_insights,
            "system_recommendations": []
        }
        
        # Add system-level recommendations
        if resource_usage["cpu_percent"] > 80:
            health_response["system_recommendations"].append({
                "type": "performance",
                "message": "High CPU usage detected",
                "suggestion": "Consider restarting resource-intensive MCP servers",
                "priority": "medium"
            })
        
        if resource_usage["memory_percent"] > 85:
            health_response["system_recommendations"].append({
                "type": "performance", 
                "message": "High memory usage detected",
                "suggestion": "Memory cleanup or service restart may be needed",
                "priority": "high"
            })
        
        if db_latency_ms > 100:
            health_response["system_recommendations"].append({
                "type": "database",
                "message": f"Database latency is high ({db_latency_ms}ms)",
                "suggestion": "Check database connection and query performance",
                "priority": "medium"
            })
        
        return APIResponse(
            success=True,
            data=health_response
        )
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get system health")


@health_router.get("/simple")
async def get_simple_health() -> Dict[str, str]:
    """Simple health check endpoint for basic monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "mcp-ecosystem-platform"
    }


# AI Action Routes
ai_router = APIRouter(prefix="/ai", tags=["AI Actions"])


@ai_router.post("/mcp/restart/{server_name}")
async def ai_restart_mcp_server(server_name: str, reasoning: str = "") -> APIResponse:
    """AI-initiated MCP server restart with approval workflow"""
    try:
        security_manager = get_security_manager()
        
        # Check if AI can perform this operation
        can_perform, reason, risk_level = security_manager.can_ai_perform_operation(
            'mcp_server_restart',
            {'server_name': server_name}
        )
        
        if not can_perform:
            # Create approval request
            approval_request = security_manager.create_ai_approval_request(
                'mcp_server_restart',
                {'server_name': server_name},
                reasoning or f"AI detected that {server_name} server is unhealthy"
            )
            
            return APIResponse(
                success=False,
                error="User approval required",
                data={
                    "approval_required": True,
                    "approval_request": approval_request,
                    "reason": reason,
                    "risk_level": risk_level.value
                }
            )
        
        # If we reach here, operation is auto-approved (shouldn't happen for restart)
        health_monitor = get_health_monitor()
        success = await health_monitor.force_restart_server(server_name)
        
        if success:
            # Log the AI operation
            security_manager.log_operation(
                'ai_mcp_restart', 
                {'server_name': server_name, 'reasoning': reasoning},
                'success',
                risk_level,
                'AI_AGENT'
            )
            
            return APIResponse(
                success=True,
                data={
                    "message": f"Server {server_name} restart initiated by AI",
                    "reasoning": reasoning
                }
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to restart {server_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI restart failed for {server_name}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"AI restart failed for {server_name}"
        )


@ai_router.post("/analyze-error")
async def ai_analyze_error(request: Dict[str, Any]) -> APIResponse:
    """AI-powered error analysis endpoint"""
    try:
        from ..services.ai_diagnostics import get_ai_diagnostics_engine, SystemContext
        
        ai_engine = get_ai_diagnostics_engine()
        
        # Request'ten sistem context'i oluştur
        system_context = SystemContext(
            current_health=request.get('systemContext', {}).get('systemHealth', {}),
            recent_errors=[],
            resource_usage={},
            mcp_server_status={},
            user_activity=request.get('systemContext', {}).get('userActions', []),
            timestamp=datetime.now()
        )
        
        # Error analizi yap
        diagnosis = await ai_engine.analyze_connection_error(
            error_details={
                'error_type': request.get('errorType', 'unknown'),
                'error_message': request.get('errorMessage', ''),
                'request_context': request.get('requestContext', {})
            },
            system_context=system_context
        )
        
        # Response formatını frontend'e uygun hale getir
        response_data = {
            'userFriendlyMessage': diagnosis.user_friendly_explanation,
            'suggestedActions': [
                {
                    'title': action.title,
                    'description': action.description,
                    'actionType': action.action_type.value,
                    'estimatedTime': action.estimated_duration,
                    'riskLevel': action.risk_level,
                    'steps': action.steps
                }
                for action in diagnosis.suggested_actions
            ],
            'analysis': {
                'rootCause': diagnosis.root_cause_analysis,
                'confidence': diagnosis.confidence_score,
                'similarIssues': 0,  # TODO: Implement similar issues tracking
                'estimatedResolutionTime': '2-5 minutes'
            }
        }
        
        return APIResponse(
            success=True,
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"AI error analysis failed: {e}")
        # Fallback response
        return APIResponse(
            success=True,
            data={
                'userFriendlyMessage': 'Bir hata oluştu ancak AI analizi şu anda kullanılamıyor. Lütfen manuel çözüm adımlarını deneyin.',
                'suggestedActions': [
                    {
                        'title': 'Sayfayı Yenile',
                        'description': 'Tarayıcı sayfasını yenileyin',
                        'actionType': 'manual',
                        'estimatedTime': 'Anında',
                        'riskLevel': 'safe',
                        'steps': ['F5 tuşuna basın veya tarayıcının yenile butonuna tıklayın']
                    }
                ],
                'analysis': {
                    'rootCause': 'AI analysis temporarily unavailable',
                    'confidence': 0.5,
                    'similarIssues': 0,
                    'estimatedResolutionTime': '1 minute'
                }
            }
        )

@ai_router.post("/feedback")
async def ai_feedback(request: Dict[str, Any]) -> APIResponse:
    """AI feedback collection endpoint"""
    try:
        from ..services.ai_diagnostics import get_ai_diagnostics_engine
        
        ai_engine = get_ai_diagnostics_engine()
        
        # Feedback'i kaydet
        feedback_data = {
            'analysis_id': request.get('analysisId'),
            'user_rating': request.get('rating'),
            'user_comment': request.get('comment'),
            'resolution_successful': request.get('resolutionSuccessful'),
            'timestamp': datetime.now()
        }
        
        # TODO: Implement feedback storage and learning
        logger.info(f"AI feedback received: {feedback_data}")
        
        return APIResponse(
            success=True,
            data={'message': 'Feedback received successfully'}
        )
        
    except Exception as e:
        logger.error(f"AI feedback failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process AI feedback")


# AI Orchestrator Routes
orchestrator_router = APIRouter(prefix="/orchestrator", tags=["AI Orchestrator"])


@orchestrator_router.get("/actions/pending")
async def get_pending_actions() -> APIResponse:
    """Get all pending AI actions awaiting approval"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        pending_actions = orchestrator.get_pending_actions()
        
        return APIResponse(
            success=True,
            data=pending_actions
        )
        
    except Exception as e:
        logger.error(f"Failed to get pending actions: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get pending actions")


@orchestrator_router.post("/actions/{action_id}/approve")
async def approve_ai_action(action_id: str, user_id: str = "system") -> APIResponse:
    """Approve a pending AI action"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        success = await orchestrator.approve_action(action_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Action {action_id} not found")
        
        return APIResponse(
            success=True,
            data={"message": f"Action {action_id} approved and executing"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve action {action_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to approve action {action_id}")


@orchestrator_router.post("/actions/{action_id}/reject")
async def reject_ai_action(action_id: str, reason: str = "") -> APIResponse:
    """Reject a pending AI action"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        success = await orchestrator.reject_action(action_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Action {action_id} not found")
        
        return APIResponse(
            success=True,
            data={"message": f"Action {action_id} rejected"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject action {action_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to reject action {action_id}")


@orchestrator_router.get("/actions/{action_id}/status")
async def get_action_status(action_id: str) -> APIResponse:
    """Get status of a specific AI action"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        status = orchestrator.get_action_status(action_id)
        
        if not status:
            raise HTTPException(
                status_code=404, detail=f"Action {action_id} not found")
        
        return APIResponse(
            success=True,
            data=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get action status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get action status")


@orchestrator_router.post("/start")
async def start_orchestration() -> APIResponse:
    """Start AI orchestration process"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        await orchestrator.start_orchestration()
        
        return APIResponse(
            success=True,
            data={"message": "AI Orchestration started successfully"}
        )
        
    except Exception as e:
        logger.error(f"Failed to start orchestration: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to start AI orchestration")


@orchestrator_router.post("/stop")
async def stop_orchestration() -> APIResponse:
    """Stop AI orchestration process"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        await orchestrator.stop_orchestration()
        
        return APIResponse(
            success=True,
            data={"message": "AI Orchestration stopped successfully"}
        )
        
    except Exception as e:
        logger.error(f"Failed to stop orchestration: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to stop AI orchestration")


@orchestrator_router.get("/insights")
async def get_ai_insights() -> APIResponse:
    """Get current AI insights and recommendations"""
    try:
        from ..services.proactive_monitor import get_proactive_monitor
        
        proactive_monitor = get_proactive_monitor()
        insights = await proactive_monitor.get_ai_insights()
        
        return APIResponse(
            success=True,
            data=insights
        )
        
    except Exception as e:
        logger.error(f"Failed to get AI insights: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get AI insights")

@api_router.post("/ai/feedback")
async def submit_ai_feedback(request: dict):
    """AI feedback endpoint"""
    try:
        ai_engine = get_ai_diagnostics_engine()
        
        # Feedback'i öğrenme sistemine kaydet
        success = await ai_engine.learn_from_resolution(
            issue_id=request.get('notification_id', ''),
            resolution_outcome={
                'user_action': request.get('user_action', ''),
                'timestamp': request.get('timestamp', ''),
                'effectiveness': 1.0 if request.get('user_action') == 'accepted' else 0.0
            }
        )
        
        return APIResponse(
            success=success,
            data={'message': 'Feedback recorded successfully'}
        )
        
    except Exception as e:
        logger.error(f"AI feedback recording failed: {e}")
        return APIResponse(
            success=False,
            error="Failed to record feedback"
        )

@ai_router.get("/insights")
async def ai_get_insights() -> APIResponse:
    """Get AI-generated system insights"""
    try:
        from ..services.proactive_monitor import get_proactive_monitor
        
        proactive_monitor = get_proactive_monitor()
        insights = await proactive_monitor.get_ai_insights()
        
        return APIResponse(
            success=True,
            data={
                'insights': insights,
                'total_count': len(insights),
                'timestamp': datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get AI insights: {e}")
        return APIResponse(
            success=False,
            error="Failed to retrieve AI insights"
        )

@ai_router.get("/mcp/logs/{server_name}")
async def ai_get_mcp_logs(server_name: str, lines: int = 100) -> APIResponse:
    """AI-initiated MCP server log retrieval"""
    try:
        security_manager = get_security_manager()
        
        # Check if AI can access logs
        can_perform, reason, risk_level = security_manager.can_ai_perform_operation(
            'mcp_server_logs',
            {'server_name': server_name, 'lines': lines}
        )
        
        if not can_perform:
            return APIResponse(
                success=False,
                error="Access denied",
                data={"reason": reason}
            )
        
        # Mock log retrieval - in real implementation, read actual logs
        mock_logs = [
            f"[INFO] {datetime.now().isoformat()} - Server {server_name} started",
            f"[INFO] {datetime.now().isoformat()} - Processing requests normally",
            f"[WARN] {datetime.now().isoformat()} - High response time detected",
            f"[ERROR] {datetime.now().isoformat()} - Connection timeout to external service",
            f"[INFO] {datetime.now().isoformat()} - Recovered from error state"
        ]
        
        # Log the AI operation
        security_manager.log_operation(
            'ai_log_access',
            {'server_name': server_name, 'lines': lines},
            f"Retrieved {len(mock_logs)} log lines",
            risk_level,
            'AI_AGENT'
        )
        
        return APIResponse(
            success=True,
            data={
                "server_name": server_name,
                "log_lines": mock_logs[-lines:],
                "total_lines": len(mock_logs),
                "analysis": {
                    "error_count": 1,
                    "warning_count": 1,
                    "last_error": "Connection timeout to external service",
                    "status": "recovering"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"AI log access failed for {server_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve logs for {server_name}"
        )


@ai_router.post("/mcp/stop/{server_name}")
async def ai_stop_mcp_server(server_name: str, reasoning: str = "") -> APIResponse:
    """AI-initiated MCP server stop with approval workflow"""
    try:
        security_manager = get_security_manager()
        
        # Check if AI can perform this operation
        can_perform, reason, risk_level = security_manager.can_ai_perform_operation(
            'mcp_server_stop',
            {'server_name': server_name}
        )
        
        if not can_perform:
            # Create approval request
            approval_request = security_manager.create_ai_approval_request(
                'mcp_server_stop',
                {'server_name': server_name},
                reasoning or f"AI determined that {server_name} server should be stopped"
            )
            
            return APIResponse(
                success=False,
                error="User approval required",
                data={
                    "approval_required": True,
                    "approval_request": approval_request,
                    "reason": reason,
                    "risk_level": risk_level.value
                }
            )
        
        # If we reach here, operation is auto-approved (shouldn't happen for stop)
        health_monitor = get_health_monitor()
        success = await health_monitor.stop_server(server_name)
        
        if success:
            # Log the AI operation
            security_manager.log_operation(
                'ai_mcp_stop', 
                {'server_name': server_name, 'reasoning': reasoning},
                'success',
                risk_level,
                'AI_AGENT'
            )
            
            return APIResponse(
                success=True,
                data={
                    "message": f"Server {server_name} stop initiated by AI",
                    "reasoning": reasoning
                }
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to stop {server_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI stop failed for {server_name}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"AI stop failed for {server_name}"
        )


@ai_router.post("/system/health-check")
async def ai_system_health_check(reasoning: str = "") -> APIResponse:
    """AI-initiated comprehensive system health check"""
    try:
        security_manager = get_security_manager()
        
        # Check if AI can perform this operation
        can_perform, reason, risk_level = security_manager.can_ai_perform_operation(
            'system_health_check',
            {}
        )
        
        if not can_perform:
            return APIResponse(
                success=False,
                error="Access denied",
                data={"reason": reason}
            )
        
        # Perform comprehensive health check
        health_monitor = get_health_monitor()
        
        # Get all server statuses
        mcp_statuses = await health_monitor.get_all_statuses()
        
        # Get system metrics
        import psutil
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids()),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
        
        # Analyze health and generate insights
        health_issues = []
        recommendations = []
        
        # Check MCP servers
        for server_name, status in mcp_statuses.items():
            if status.status != "HEALTHY":
                health_issues.append({
                    "type": "mcp_server",
                    "server": server_name,
                    "status": status.status,
                    "issue": status.error_message or "Server is not healthy"
                })
                
                if status.status == "OFFLINE":
                    recommendations.append({
                        "action": "restart_server",
                        "target": server_name,
                        "priority": "high",
                        "reason": "Server is offline and needs restart"
                    })
        
        # Check system resources
        if system_metrics["cpu_percent"] > 80:
            health_issues.append({
                "type": "system_resource",
                "resource": "cpu",
                "value": system_metrics["cpu_percent"],
                "issue": "High CPU usage detected"
            })
            recommendations.append({
                "action": "investigate_processes",
                "priority": "medium",
                "reason": "High CPU usage may indicate resource-intensive processes"
            })
        
        if system_metrics["memory_percent"] > 85:
            health_issues.append({
                "type": "system_resource",
                "resource": "memory",
                "value": system_metrics["memory_percent"],
                "issue": "High memory usage detected"
            })
            recommendations.append({
                "action": "restart_services",
                "priority": "high",
                "reason": "High memory usage may require service restart"
            })
        
        # Log the AI operation
        security_manager.log_operation(
            'ai_health_check',
            {'reasoning': reasoning},
            f"Found {len(health_issues)} issues, {len(recommendations)} recommendations",
            risk_level,
            'AI_AGENT'
        )
        
        return APIResponse(
            success=True,
            data={
                "timestamp": datetime.now().isoformat(),
                "system_metrics": system_metrics,
                "mcp_server_count": len(mcp_statuses),
                "healthy_servers": sum(1 for s in mcp_statuses.values() if s.status == "HEALTHY"),
                "health_issues": health_issues,
                "recommendations": recommendations,
                "overall_status": "healthy" if len(health_issues) == 0 else "degraded",
                "ai_reasoning": reasoning
            }
        )
        
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="AI health check failed"
        )


@ai_router.post("/system/investigate-processes")
async def ai_investigate_processes(reasoning: str = "") -> APIResponse:
    """AI-initiated process investigation for performance issues"""
    try:
        security_manager = get_security_manager()
        
        # Check if AI can perform this operation
        can_perform, reason, risk_level = security_manager.can_ai_perform_operation(
            'investigate_processes',
            {}
        )
        
        if not can_perform:
            return APIResponse(
                success=False,
                error="Access denied",
                data={"reason": reason}
            )
        
        # Investigate system processes
        import psutil
        
        # Get top CPU consuming processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                if proc_info['cpu_percent'] > 1.0:  # Only processes using > 1% CPU
                    processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top_processes = processes[:10]  # Top 10 processes
        
        # Analyze for potential issues
        analysis = {
            "high_cpu_processes": [p for p in top_processes if p['cpu_percent'] > 10],
            "high_memory_processes": [p for p in top_processes if p['memory_percent'] > 5],
            "total_processes": len(psutil.pids()),
            "system_load": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
        
        # Generate recommendations
        recommendations = []
        if len(analysis["high_cpu_processes"]) > 0:
            recommendations.append({
                "type": "performance",
                "message": f"Found {len(analysis['high_cpu_processes'])} high CPU processes",
                "suggestion": "Consider restarting or optimizing high CPU processes",
                "priority": "medium"
            })
        
        # Log the AI operation
        security_manager.log_operation(
            'ai_process_investigation',
            {'reasoning': reasoning},
            f"Investigated {len(processes)} processes",
            risk_level,
            'AI_AGENT'
        )
        
        return APIResponse(
            success=True,
            data={
                "timestamp": datetime.now().isoformat(),
                "top_processes": top_processes,
                "analysis": analysis,
                "recommendations": recommendations,
                "ai_reasoning": reasoning
            }
        )
        
    except Exception as e:
        logger.error(f"AI process investigation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="AI process investigation failed"
        )


# AI Orchestrator Routes
@ai_router.get("/orchestrator/status")
async def get_orchestrator_status() -> APIResponse:
    """Get AI Orchestrator status and statistics"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        
        status_data = {
            "orchestration_active": orchestrator.orchestration_active,
            "pending_actions_count": len(orchestrator.pending_actions),
            "active_executions_count": len(orchestrator.active_executions),
            "completed_actions_count": len(orchestrator.completed_actions),
            "timestamp": datetime.now().isoformat()
        }
        
        return APIResponse(
            success=True,
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"Failed to get orchestrator status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get orchestrator status"
        )


@ai_router.post("/orchestrator/start")
async def start_orchestrator() -> APIResponse:
    """Start AI Orchestrator"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        await orchestrator.start_orchestration()
        
        return APIResponse(
            success=True,
            data={"message": "AI Orchestrator started successfully"}
        )
        
    except Exception as e:
        logger.error(f"Failed to start orchestrator: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start orchestrator"
        )


@ai_router.post("/orchestrator/stop")
async def stop_orchestrator() -> APIResponse:
    """Stop AI Orchestrator"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        await orchestrator.stop_orchestration()
        
        return APIResponse(
            success=True,
            data={"message": "AI Orchestrator stopped successfully"}
        )
        
    except Exception as e:
        logger.error(f"Failed to stop orchestrator: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to stop orchestrator"
        )


@ai_router.get("/orchestrator/actions/pending")
async def get_pending_actions() -> APIResponse:
    """Get all pending AI actions awaiting approval"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        pending_actions = orchestrator.get_pending_actions()
        
        return APIResponse(
            success=True,
            data=pending_actions
        )
        
    except Exception as e:
        logger.error(f"Failed to get pending actions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get pending actions"
        )


@ai_router.post("/orchestrator/actions/{action_id}/approve")
async def approve_action(action_id: str, user_id: str = "user") -> APIResponse:
    """Approve a pending AI action"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        success = await orchestrator.approve_action(action_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Action {action_id} not found or cannot be approved"
            )
        
        return APIResponse(
            success=True,
            data={"message": f"Action {action_id} approved and executed"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve action {action_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve action {action_id}"
        )


@ai_router.post("/orchestrator/actions/{action_id}/reject")
async def reject_action(action_id: str, reason: str = "") -> APIResponse:
    """Reject a pending AI action"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        success = await orchestrator.reject_action(action_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Action {action_id} not found"
            )
        
        return APIResponse(
            success=True,
            data={"message": f"Action {action_id} rejected"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject action {action_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject action {action_id}"
        )


@ai_router.get("/orchestrator/actions/{action_id}/status")
async def get_action_status(action_id: str) -> APIResponse:
    """Get status of a specific AI action"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        orchestrator = get_ai_orchestrator()
        status = orchestrator.get_action_status(action_id)
        
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Action {action_id} not found"
            )
        
        return APIResponse(
            success=True,
            data=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get action status {action_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get action status {action_id}"
        )


# MCP Tools Routes
mcp_tools_router = APIRouter(prefix="/mcp-tools", tags=["MCP Tools"])


@mcp_tools_router.get("/")
async def list_mcp_tools() -> APIResponse:
    """List all available MCP tools"""
    try:
        from ..services.mcp_tools import get_mcp_tool_registry
        
        registry = get_mcp_tool_registry()
        tools = registry.list_tools()
        
        return APIResponse(
            success=True,
            data=tools
        )
    except Exception as e:
        logger.error(f"Failed to list MCP tools: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to list MCP tools")


@mcp_tools_router.post("/execute/{tool_name}")
async def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> APIResponse:
    """Execute an MCP tool"""
    try:
        from ..services.mcp_tools import get_mcp_tool_registry
        
        registry = get_mcp_tool_registry()
        result = await registry.execute_tool(tool_name, arguments)
        
        return APIResponse(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Failed to execute MCP tool {tool_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to execute MCP tool {tool_name}")


@mcp_tools_router.get("/system-health")
async def get_system_health_via_mcp() -> APIResponse:
    """Get system health via MCP tool interface"""
    try:
        from ..services.mcp_tools import get_mcp_tool_registry
        
        registry = get_mcp_tool_registry()
        result = await registry.execute_tool("get_system_health", {
            "include_insights": True,
            "include_metrics": True
        })
        
        return APIResponse(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Failed to get system health via MCP: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get system health via MCP")


# Proactive Monitoring Routes
monitoring_router = APIRouter(prefix="/monitoring", tags=["Proactive Monitoring"])


@monitoring_router.get("/alerts")
async def get_active_alerts() -> APIResponse:
    """Get all active system alerts"""
    try:
        from ..services.proactive_monitor import get_proactive_monitor
        
        monitor = get_proactive_monitor()
        alerts = monitor.get_active_alerts()
        
        # Convert alerts to serializable format
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                "id": alert.id,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "source": alert.source,
                "metadata": alert.metadata,
                "suggested_actions": alert.suggested_actions,
                "acknowledged": alert.acknowledged,
                "resolved": alert.resolved,
                "auto_resolve": alert.auto_resolve
            })
        
        return APIResponse(
            success=True,
            data=alerts_data
        )
    except Exception as e:
        logger.error(f"Failed to get active alerts: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get active alerts")


@monitoring_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> APIResponse:
    """Acknowledge a system alert"""
    try:
        from ..services.proactive_monitor import get_proactive_monitor
        
        monitor = get_proactive_monitor()
        success = monitor.acknowledge_alert(alert_id)
        
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Alert {alert_id} not found")
        
        return APIResponse(
            success=True,
            data={"message": f"Alert {alert_id} acknowledged"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to acknowledge alert")


@monitoring_router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str) -> APIResponse:
    """Resolve a system alert"""
    try:
        from ..services.proactive_monitor import get_proactive_monitor
        
        monitor = get_proactive_monitor()
        success = monitor.resolve_alert(alert_id)
        
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Alert {alert_id} not found")
        
        return APIResponse(
            success=True,
            data={"message": f"Alert {alert_id} resolved"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to resolve alert")


@monitoring_router.get("/patterns")
async def get_detected_patterns() -> APIResponse:
    """Get detected health patterns"""
    try:
        from ..services.proactive_monitor import get_proactive_monitor
        
        monitor = get_proactive_monitor()
        patterns = monitor.get_detected_patterns()
        
        # Convert patterns to serializable format
        patterns_data = []
        for pattern in patterns:
            patterns_data.append({
                "pattern_type": pattern.pattern_type.value,
                "description": pattern.description,
                "confidence": pattern.confidence,
                "first_occurrence": pattern.first_occurrence.isoformat(),
                "last_occurrence": pattern.last_occurrence.isoformat(),
                "frequency": pattern.frequency,
                "affected_components": pattern.affected_components,
                "suggested_resolution": pattern.suggested_resolution,
                "metadata": pattern.metadata
            })
        
        return APIResponse(
            success=True,
            data=patterns_data
        )
    except Exception as e:
        logger.error(f"Failed to get detected patterns: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get detected patterns")


@monitoring_router.post("/analyze-connection-loss")
async def analyze_connection_loss(request: Dict[str, str]) -> APIResponse:
    """Analyze connection loss and get AI suggestions"""
    try:
        from ..services.proactive_monitor import get_proactive_monitor
        
        component = request.get("component", "unknown")
        error_details = request.get("error_details", "")
        
        if not component or not error_details:
            raise HTTPException(
                status_code=400, 
                detail="component and error_details are required")
        
        monitor = get_proactive_monitor()
        analysis = await monitor.analyze_connection_loss(component, error_details)
        
        return APIResponse(
            success=True,
            data=analysis
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze connection loss: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to analyze connection loss")


@monitoring_router.post("/start")
async def start_monitoring() -> APIResponse:
    """Start proactive monitoring"""
    try:
        from ..services.proactive_monitor import get_proactive_monitor
        
        monitor = get_proactive_monitor()
        await monitor.start_monitoring()
        
        return APIResponse(
            success=True,
            data={"message": "Proactive monitoring started"}
        )
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to start monitoring")


@monitoring_router.post("/stop")
async def stop_monitoring() -> APIResponse:
    """Stop proactive monitoring"""
    try:
        from ..services.proactive_monitor import get_proactive_monitor
        
        monitor = get_proactive_monitor()
        await monitor.stop_monitoring()
        
        return APIResponse(
            success=True,
            data={"message": "Proactive monitoring stopped"}
        )
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to stop monitoring")


# Include all routers
api_router.include_router(health_router)
api_router.include_router(ai_router)
api_router.include_router(orchestrator_router)
api_router.include_router(monitoring_router)
api_router.include_router(mcp_tools_router)
api_router.include_router(mcp_router)
api_router.include_router(config_router)
api_router.include_router(tools_router)
api_router.include_router(workflow_router)
api_router.include_router(research_router)
api_router.include_router(privacy_router)
api_router.include_router(network_router)
api_router.include_router(git_router)
api_router.include_router(security_router)

@orchestrator_router.get("/learning/insights")
async def get_learning_insights() -> APIResponse:
    """Get AI learning insights and statistics"""
    try:
        from ..services.ai_learning import get_ai_learning_database
        
        learning_db = get_ai_learning_database()
        insights = await learning_db.get_learning_insights()
        
        return APIResponse(
            success=True,
            data=insights
        )
        
    except Exception as e:
        logger.error(f"Failed to get learning insights: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get learning insights")


@orchestrator_router.post("/learning/feedback")
async def record_learning_feedback(request: Dict[str, Any]) -> APIResponse:
    """Record user feedback for AI actions"""
    try:
        from ..services.ai_orchestrator import get_ai_orchestrator
        
        action_id = request.get('action_id')
        user_rating = request.get('rating')
        user_comment = request.get('comment', '')
        resolution_helpful = request.get('resolution_helpful', True)
        
        if not action_id or user_rating is None:
            raise HTTPException(
                status_code=400, 
                detail="action_id and rating are required"
            )
        
        if not (1 <= user_rating <= 5):
            raise HTTPException(
                status_code=400,
                detail="rating must be between 1 and 5"
            )
        
        orchestrator = get_ai_orchestrator()
        success = await orchestrator.record_user_feedback(
            action_id=action_id,
            user_rating=user_rating,
            user_comment=user_comment,
            resolution_helpful=resolution_helpful
        )
        
        if success:
            return APIResponse(
                success=True,
                data={"message": "Feedback recorded successfully"}
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to record feedback"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record learning feedback: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to record learning feedback")


@orchestrator_router.get("/learning/recommendations/{issue_type}")
async def get_learning_recommendations(
    issue_type: str,
    context: Dict[str, Any] = None
) -> APIResponse:
    """Get AI learning-based recommendations for an issue type"""
    try:
        from ..services.ai_learning import get_ai_learning_database
        
        learning_db = get_ai_learning_database()
        recommendations = await learning_db.get_recommendations_for_issue(
            issue_type=issue_type,
            context=context or {}
        )
        
        return APIResponse(
            success=True,
            data={
                "issue_type": issue_type,
                "recommendations": recommendations,
                "total_recommendations": len(recommendations)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get learning recommendations: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get learning recommendations")