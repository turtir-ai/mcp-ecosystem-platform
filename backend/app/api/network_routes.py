"""
Network monitoring and security API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from ..services.network_monitor import NetworkMonitor, MetricType, create_network_monitor
from ..services.security_monitor import SecurityMonitor, ThreatLevel, create_security_monitor
from ..services.diagnostic_service import DiagnosticService, create_diagnostic_service
from ..core.auth import get_current_user

router = APIRouter(prefix="/network", tags=["network"])


def get_network_monitor() -> NetworkMonitor:
    """Get network monitor instance."""
    return create_network_monitor()


def get_security_monitor() -> SecurityMonitor:
    """Get security monitor instance."""
    return create_security_monitor()


def get_diagnostic_service() -> DiagnosticService:
    """Get diagnostic service instance."""
    return create_diagnostic_service()


@router.get("/status", response_model=dict)
async def get_network_status(
    current_user: dict = Depends(get_current_user),
    network_monitor: NetworkMonitor = Depends(get_network_monitor)
):
    """Get comprehensive network status."""
    try:
        report = await network_monitor.get_network_status()

        return {
            "report_id": report.report_id,
            "overall_status": report.overall_status.value,
            "interfaces": [
                {
                    "name": iface.name,
                    "ip_address": iface.ip_address,
                    "status": iface.status,
                    "bytes_sent": iface.bytes_sent,
                    "bytes_received": iface.bytes_received,
                    "errors_in": iface.errors_in,
                    "errors_out": iface.errors_out
                }
                for iface in report.interfaces
            ],
            "performance_summary": report.performance_summary,
            "recommendations": report.recommendations,
            "created_at": report.created_at.isoformat(),
            "monitoring_duration": report.monitoring_duration_seconds
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network status: {str(e)}"
        )


@router.get("/metrics/{metric_type}", response_model=dict)
async def get_metric_history(
    metric_type: MetricType,
    target: Optional[str] = None,
    hours: int = 24,
    current_user: dict = Depends(get_current_user),
    network_monitor: NetworkMonitor = Depends(get_network_monitor)
):
    """Get historical network metrics."""
    try:
        metrics = network_monitor.get_metric_history(
            metric_type, target, hours)

        return {
            "metric_type": metric_type.value,
            "target": target,
            "time_range_hours": hours,
            "data_points": len(metrics),
            "metrics": [
                {
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata
                }
                for m in metrics
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get metric history: {str(e)}"
        )


@router.get("/trends", response_model=dict)
async def get_performance_trends(
    hours: int = 24,
    current_user: dict = Depends(get_current_user),
    network_monitor: NetworkMonitor = Depends(get_network_monitor)
):
    """Get network performance trends."""
    try:
        trends = network_monitor.get_performance_trends(hours)
        return {
            "time_range_hours": hours,
            "trends": trends
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get performance trends: {str(e)}"
        )


@router.post("/monitoring/start", response_model=dict)
async def start_monitoring(
    interval_seconds: int = 300,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    network_monitor: NetworkMonitor = Depends(get_network_monitor)
):
    """Start continuous network monitoring."""
    try:
        monitoring_id = await network_monitor.start_continuous_monitoring(interval_seconds)

        return {
            "monitoring_id": monitoring_id,
            "interval_seconds": interval_seconds,
            "status": "started",
            "message": "Continuous network monitoring started"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/monitoring/stop", response_model=dict)
async def stop_monitoring(
    current_user: dict = Depends(get_current_user),
    network_monitor: NetworkMonitor = Depends(get_network_monitor)
):
    """Stop continuous network monitoring."""
    try:
        await network_monitor.stop_continuous_monitoring()

        return {
            "status": "stopped",
            "message": "Continuous network monitoring stopped"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.get("/security/threats", response_model=dict)
async def get_security_threats(
    threat_level: Optional[ThreatLevel] = None,
    current_user: dict = Depends(get_current_user),
    security_monitor: SecurityMonitor = Depends(get_security_monitor)
):
    """Get active security threats."""
    try:
        threats = security_monitor.get_active_threats(threat_level)

        return {
            "total_threats": len(threats),
            "threat_level_filter": threat_level.value if threat_level else None,
            "threats": [
                {
                    "threat_id": threat.threat_id,
                    "threat_type": threat.threat_type.value,
                    "threat_level": threat.threat_level.value,
                    "title": threat.title,
                    "description": threat.description,
                    "source": threat.source,
                    "target": threat.target,
                    "confidence_score": threat.confidence_score,
                    "first_detected": threat.first_detected.isoformat(),
                    "last_seen": threat.last_seen.isoformat(),
                    "status": threat.status.value,
                    # Limit for API response
                    "indicators": threat.indicators[:3],
                    "tags": threat.tags
                }
                for threat in threats
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security threats: {str(e)}"
        )


@router.post("/security/scan", response_model=dict)
async def scan_security_threats(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    security_monitor: SecurityMonitor = Depends(get_security_monitor)
):
    """Perform security threat scan."""
    try:
        threats = await security_monitor.scan_for_threats()

        return {
            "scan_completed": True,
            "threats_detected": len(threats),
            "scan_time": security_monitor.last_scan_time.isoformat(),
            "threat_summary": {
                threat_level.value: len(
                    [t for t in threats if t.threat_level == threat_level])
                for threat_level in ThreatLevel
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security scan failed: {str(e)}"
        )


@router.get("/security/summary", response_model=dict)
async def get_security_summary(
    current_user: dict = Depends(get_current_user),
    security_monitor: SecurityMonitor = Depends(get_security_monitor)
):
    """Get security monitoring summary."""
    try:
        summary = security_monitor.get_security_summary()
        return summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security summary: {str(e)}"
        )


@router.post("/security/threats/{threat_id}/resolve", response_model=dict)
async def resolve_threat(
    threat_id: str,
    resolution_notes: str = "",
    current_user: dict = Depends(get_current_user),
    security_monitor: SecurityMonitor = Depends(get_security_monitor)
):
    """Mark a security threat as resolved."""
    try:
        success = await security_monitor.resolve_threat(threat_id, resolution_notes)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Threat not found"
            )

        return {
            "threat_id": threat_id,
            "status": "resolved",
            "resolved_by": current_user.get("id"),
            "resolution_notes": resolution_notes,
            "resolved_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve threat: {str(e)}"
        )


@router.get("/diagnostics", response_model=dict)
async def get_diagnostic_report(
    current_user: dict = Depends(get_current_user),
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service)
):
    """Generate comprehensive diagnostic report."""
    try:
        report = await diagnostic_service.generate_diagnostic_report()

        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "overall_health_score": report.overall_health_score,
            "network_status": report.network_status.value,
            "security_status": report.security_status,
            "executive_summary": report.executive_summary,
            "key_findings": report.key_findings,
            "immediate_actions": report.immediate_actions,
            "issues": [
                {
                    "issue_id": issue.issue_id,
                    "title": issue.title,
                    "description": issue.description,
                    "severity": issue.severity.value,
                    "category": issue.category,
                    "detected_at": issue.detected_at.isoformat(),
                    "impact_description": issue.impact_description,
                    "affected_components": issue.affected_components,
                    "is_resolved": issue.is_resolved
                }
                for issue in report.issues
            ],
            "recommendations": [
                {
                    "recommendation_id": rec.recommendation_id,
                    "title": rec.title,
                    "description": rec.description,
                    "type": rec.recommendation_type.value,
                    "priority": rec.priority.value,
                    "implementation_steps": rec.implementation_steps,
                    "estimated_effort": rec.estimated_effort,
                    "estimated_impact": rec.estimated_impact,
                    "status": rec.status,
                    "tags": rec.tags
                }
                for rec in report.recommendations
            ],
            "trend_analysis": report.trend_analysis
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate diagnostic report: {str(e)}"
        )


@router.get("/diagnostics/history", response_model=dict)
async def get_diagnostic_history(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service)
):
    """Get diagnostic report history."""
    try:
        history = diagnostic_service.get_diagnostic_history(days)

        return {
            "time_range_days": days,
            "total_reports": len(history),
            "reports": [
                {
                    "report_id": report.report_id,
                    "generated_at": report.generated_at.isoformat(),
                    "health_score": report.overall_health_score,
                    "network_status": report.network_status.value,
                    "security_status": report.security_status,
                    "issues_count": len(report.issues),
                    "recommendations_count": len(report.recommendations)
                }
                for report in history
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get diagnostic history: {str(e)}"
        )


@router.post("/diagnostics/recommendations/{recommendation_id}/status", response_model=dict)
async def update_recommendation_status(
    recommendation_id: str,
    status: str,
    notes: str = "",
    current_user: dict = Depends(get_current_user),
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service)
):
    """Update recommendation status."""
    try:
        success = await diagnostic_service.update_recommendation_status(
            recommendation_id, status, notes
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )

        return {
            "recommendation_id": recommendation_id,
            "status": status,
            "updated_by": current_user.get("id"),
            "notes": notes,
            "updated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update recommendation status: {str(e)}"
        )
