"""
Diagnostic and recommendation system for network and security optimization.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

from .network_monitor import NetworkMonitor, NetworkStatus, MetricType
from .security_monitor import SecurityMonitor, ThreatLevel
from .mcp_client import MCPClient
from ..core.error_handling import get_error_handler

logger = logging.getLogger(__name__)


class DiagnosticSeverity(str, Enum):
    """Diagnostic issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecommendationType(str, Enum):
    """Types of recommendations."""
    PERFORMANCE = "performance"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    MAINTENANCE = "maintenance"
    OPTIMIZATION = "optimization"
    MONITORING = "monitoring"


class Priority(str, Enum):
    """Recommendation priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class DiagnosticIssue:
    """Represents a diagnostic issue."""
    issue_id: str
    title: str
    description: str
    severity: DiagnosticSeverity
    category: str

    # Detection details
    detected_at: datetime
    source: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    # Impact assessment
    impact_description: str = ""
    affected_components: List[str] = field(default_factory=list)

    # Resolution
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class Recommendation:
    """System optimization recommendation."""
    recommendation_id: str
    title: str
    description: str
    recommendation_type: RecommendationType
    priority: Priority

    # Implementation details
    implementation_steps: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"  # low, medium, high
    estimated_impact: str = "medium"  # low, medium, high

    # Context
    related_issues: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)

    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, in_progress, completed, dismissed

    # Metadata
    tags: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


@dataclass
class DiagnosticReport:
    """Comprehensive diagnostic report."""
    report_id: str
    generated_at: datetime

    # System health overview
    overall_health_score: float  # 0-100
    network_status: NetworkStatus
    security_status: str

    # Issues and recommendations
    issues: List[DiagnosticIssue]
    recommendations: List[Recommendation]

    # Performance metrics
    performance_summary: Dict[str, Any]
    trend_analysis: Dict[str, Any]

    # Executive summary
    executive_summary: str
    key_findings: List[str]
    immediate_actions: List[str]


class DiagnosticService:
    """Diagnostic and recommendation system."""

    def __init__(self, network_monitor: NetworkMonitor, security_monitor: SecurityMonitor, mcp_client: MCPClient):
        self.network_monitor = network_monitor
        self.security_monitor = security_monitor
        self.mcp_client = mcp_client
        self.error_handler = get_error_handler()

        # Historical data for trend analysis
        self.diagnostic_history: List[DiagnosticReport] = []
        self.issue_patterns: Dict[str, List[datetime]] = {}

        # Recommendation templates
        self.recommendation_templates = self._load_recommendation_templates()

    async def generate_diagnostic_report(self) -> DiagnosticReport:
        """Generate comprehensive diagnostic report."""
        report_id = f"diagnostic_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        try:
            logger.info(f"Generating diagnostic report {report_id}")

            # Collect system data
            network_report = await self.network_monitor.get_network_status()
            security_summary = self.security_monitor.get_security_summary()

            # Analyze issues
            issues = await self._analyze_system_issues(network_report, security_summary)

            # Generate recommendations
            recommendations = await self._generate_recommendations(issues, network_report, security_summary)

            # Calculate health scores
            health_score = self._calculate_overall_health_score(
                network_report, security_summary, issues)

            # Perform trend analysis
            trend_analysis = await self._analyze_trends()

            # Generate executive summary
            executive_summary, key_findings, immediate_actions = self._generate_executive_summary(
                issues, recommendations, health_score, network_report, security_summary
            )

            report = DiagnosticReport(
                report_id=report_id,
                generated_at=datetime.utcnow(),
                overall_health_score=health_score,
                network_status=network_report.overall_status,
                security_status=self._get_security_status_summary(
                    security_summary),
                issues=issues,
                recommendations=recommendations,
                performance_summary=network_report.performance_summary,
                trend_analysis=trend_analysis,
                executive_summary=executive_summary,
                key_findings=key_findings,
                immediate_actions=immediate_actions
            )

            # Store in history
            self.diagnostic_history.append(report)
            if len(self.diagnostic_history) > 50:  # Keep last 50 reports
                self.diagnostic_history = self.diagnostic_history[-50:]

            logger.info(
                f"Diagnostic report {report_id} completed: {health_score:.1f}% health score")
            return report

        except Exception as e:
            self.error_handler.handle_workflow_error(
                error=e,
                workflow_id="diagnostic_system",
                execution_id=report_id,
                context={"operation": "generate_report"}
            )
            raise

    async def _analyze_system_issues(self, network_report, security_summary) -> List[DiagnosticIssue]:
        """Analyze system for issues."""
        issues = []

        # Network performance issues
        network_issues = self._analyze_network_issues(network_report)
        issues.extend(network_issues)

        # Security issues
        security_issues = self._analyze_security_issues(security_summary)
        issues.extend(security_issues)

        # System configuration issues
        config_issues = await self._analyze_configuration_issues()
        issues.extend(config_issues)

        # Resource utilization issues
        resource_issues = await self._analyze_resource_issues()
        issues.extend(resource_issues)

        return issues

    def _analyze_network_issues(self, network_report) -> List[DiagnosticIssue]:
        """Analyze network performance issues."""
        issues = []

        # High latency issue
        latency_data = network_report.performance_summary.get("latency", {})
        if latency_data.get("status") in [NetworkStatus.POOR, NetworkStatus.CRITICAL]:
            issue = DiagnosticIssue(
                issue_id=f"network_latency_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                title="High Network Latency",
                description=f"Network latency is {latency_data.get('avg', 0):.1f}ms, which is above acceptable thresholds",
                severity=DiagnosticSeverity.ERROR if latency_data.get(
                    "status") == NetworkStatus.CRITICAL else DiagnosticSeverity.WARNING,
                category="network_performance",
                detected_at=datetime.utcnow(),
                source="network_monitor",
                evidence={
                    "average_latency": latency_data.get("avg"),
                    "max_latency": latency_data.get("max"),
                    "status": latency_data.get("status")
                },
                impact_description="High latency can affect user experience and application performance",
                affected_components=["network", "applications"]
            )
            issues.append(issue)

        # Packet loss issue
        packet_loss_data = network_report.performance_summary.get(
            "packet_loss", {})
        if packet_loss_data.get("avg", 0) > 1.0:
            issue = DiagnosticIssue(
                issue_id=f"packet_loss_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                title="Network Packet Loss",
                description=f"Packet loss detected: {packet_loss_data.get('avg', 0):.1f}%",
                severity=DiagnosticSeverity.ERROR if packet_loss_data.get(
                    "avg", 0) > 3.0 else DiagnosticSeverity.WARNING,
                category="network_reliability",
                detected_at=datetime.utcnow(),
                source="network_monitor",
                evidence=packet_loss_data,
                impact_description="Packet loss can cause connection timeouts and data retransmission",
                affected_components=["network", "connectivity"]
            )
            issues.append(issue)

        # Interface errors
        for interface in network_report.interfaces:
            if interface.errors_in and interface.errors_in > 0:
                issue = DiagnosticIssue(
                    issue_id=f"interface_errors_{interface.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                    title=f"Network Interface Errors - {interface.name}",
                    description=f"Network interface {interface.name} has {interface.errors_in} input errors",
                    severity=DiagnosticSeverity.WARNING,
                    category="network_hardware",
                    detected_at=datetime.utcnow(),
                    source="network_monitor",
                    evidence={
                        "interface": interface.name,
                        "errors_in": interface.errors_in,
                        "errors_out": interface.errors_out
                    },
                    impact_description="Interface errors may indicate hardware problems or network congestion",
                    affected_components=[f"interface_{interface.name}"]
                )
                issues.append(issue)

        return issues

    def _analyze_security_issues(self, security_summary) -> List[DiagnosticIssue]:
        """Analyze security-related issues."""
        issues = []

        # Critical security threats
        if security_summary.get("critical_threats", 0) > 0:
            issue = DiagnosticIssue(
                issue_id=f"critical_threats_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                title="Critical Security Threats Detected",
                description=f"{security_summary['critical_threats']} critical security threats require immediate attention",
                severity=DiagnosticSeverity.CRITICAL,
                category="security_threats",
                detected_at=datetime.utcnow(),
                source="security_monitor",
                evidence=security_summary,
                impact_description="Critical threats pose immediate risk to system security",
                affected_components=["security", "system"]
            )
            issues.append(issue)

        # High number of security threats
        if security_summary.get("total_active_threats", 0) > 10:
            issue = DiagnosticIssue(
                issue_id=f"high_threat_count_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                title="High Number of Active Security Threats",
                description=f"{security_summary['total_active_threats']} active security threats detected",
                severity=DiagnosticSeverity.WARNING,
                category="security_monitoring",
                detected_at=datetime.utcnow(),
                source="security_monitor",
                evidence=security_summary,
                impact_description="High threat count may indicate systemic security issues",
                affected_components=["security"]
            )
            issues.append(issue)

        return issues

    async def _analyze_configuration_issues(self) -> List[DiagnosticIssue]:
        """Analyze system configuration issues."""
        issues = []

        # This would typically check system configurations
        # For demonstration, we'll check some basic configurations

        try:
            # Check MCP server configurations
            # This is a simplified check - real implementation would be more comprehensive
            config_checks = [
                {
                    "id": "mcp_server_health",
                    "title": "MCP Server Health Check",
                    "description": "Some MCP servers may not be responding properly",
                    "severity": DiagnosticSeverity.WARNING,
                    "category": "configuration"
                }
            ]

            # Convert to DiagnosticIssue objects
            for check in config_checks:
                issue = DiagnosticIssue(
                    issue_id=f"config_{check['id']}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                    title=check["title"],
                    description=check["description"],
                    severity=check["severity"],
                    category=check["category"],
                    detected_at=datetime.utcnow(),
                    source="configuration_analyzer",
                    impact_description="Configuration issues can affect system reliability",
                    affected_components=["configuration"]
                )
                issues.append(issue)

        except Exception as e:
            logger.warning(f"Configuration analysis failed: {e}")

        return issues

    async def _analyze_resource_issues(self) -> List[DiagnosticIssue]:
        """Analyze system resource utilization issues."""
        issues = []

        try:
            # This would typically check CPU, memory, disk usage, etc.
            # For demonstration, we'll simulate some resource checks

            resource_checks = []

            # Simulate high connection count as resource issue
            # In real implementation, this would check actual system resources

        except Exception as e:
            logger.warning(f"Resource analysis failed: {e}")

        return issues

    async def _generate_recommendations(self, issues: List[DiagnosticIssue],
                                        network_report, security_summary) -> List[Recommendation]:
        """Generate optimization recommendations."""
        recommendations = []

        # Generate recommendations based on issues
        for issue in issues:
            issue_recommendations = self._get_recommendations_for_issue(issue)
            recommendations.extend(issue_recommendations)

        # Generate proactive recommendations
        proactive_recommendations = await self._generate_proactive_recommendations(network_report, security_summary)
        recommendations.extend(proactive_recommendations)

        # Remove duplicates and prioritize
        recommendations = self._deduplicate_and_prioritize_recommendations(
            recommendations)

        return recommendations

    def _get_recommendations_for_issue(self, issue: DiagnosticIssue) -> List[Recommendation]:
        """Get recommendations for a specific issue."""
        recommendations = []

        if "latency" in issue.issue_id:
            rec = Recommendation(
                recommendation_id=f"fix_latency_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                title="Optimize Network Latency",
                description="Implement measures to reduce network latency",
                recommendation_type=RecommendationType.PERFORMANCE,
                priority=Priority.HIGH,
                implementation_steps=[
                    "Check network routing configuration",
                    "Consider using faster DNS servers (8.8.8.8, 1.1.1.1)",
                    "Optimize network hardware settings",
                    "Implement traffic shaping if necessary"
                ],
                estimated_effort="medium",
                estimated_impact="high",
                related_issues=[issue.issue_id],
                tags=["network", "latency", "performance"]
            )
            recommendations.append(rec)

        elif "packet_loss" in issue.issue_id:
            rec = Recommendation(
                recommendation_id=f"fix_packet_loss_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                title="Address Network Packet Loss",
                description="Investigate and resolve packet loss issues",
                recommendation_type=RecommendationType.MAINTENANCE,
                priority=Priority.HIGH,
                implementation_steps=[
                    "Check network cable connections",
                    "Inspect network hardware for faults",
                    "Review network switch/router logs",
                    "Consider network hardware replacement if necessary"
                ],
                estimated_effort="medium",
                estimated_impact="high",
                related_issues=[issue.issue_id],
                tags=["network", "packet-loss", "hardware"]
            )
            recommendations.append(rec)

        elif "critical_threats" in issue.issue_id:
            rec = Recommendation(
                recommendation_id=f"address_threats_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                title="Address Critical Security Threats",
                description="Immediately investigate and resolve critical security threats",
                recommendation_type=RecommendationType.SECURITY,
                priority=Priority.URGENT,
                implementation_steps=[
                    "Review all critical security alerts",
                    "Implement immediate containment measures",
                    "Investigate threat sources and vectors",
                    "Update security policies and procedures",
                    "Consider engaging security incident response team"
                ],
                estimated_effort="high",
                estimated_impact="critical",
                related_issues=[issue.issue_id],
                tags=["security", "threats", "incident-response"]
            )
            recommendations.append(rec)

        return recommendations

    async def _generate_proactive_recommendations(self, network_report, security_summary) -> List[Recommendation]:
        """Generate proactive optimization recommendations."""
        recommendations = []

        # Network optimization recommendations
        if network_report.overall_status == NetworkStatus.GOOD:
            rec = Recommendation(
                recommendation_id=f"proactive_monitoring_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                title="Enhance Network Monitoring",
                description="Implement additional network monitoring for proactive issue detection",
                recommendation_type=RecommendationType.MONITORING,
                priority=Priority.MEDIUM,
                implementation_steps=[
                    "Set up automated network performance alerts",
                    "Implement network baseline monitoring",
                    "Configure trend analysis for capacity planning",
                    "Add monitoring for additional network metrics"
                ],
                estimated_effort="medium",
                estimated_impact="medium",
                tags=["monitoring", "proactive", "network"]
            )
            recommendations.append(rec)

        # Security hardening recommendations
        if security_summary.get("total_active_threats", 0) < 5:
            rec = Recommendation(
                recommendation_id=f"security_hardening_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                title="Implement Security Hardening Measures",
                description="Proactively strengthen security posture",
                recommendation_type=RecommendationType.SECURITY,
                priority=Priority.MEDIUM,
                implementation_steps=[
                    "Review and update security policies",
                    "Implement additional access controls",
                    "Enable advanced threat detection",
                    "Conduct security awareness training",
                    "Perform regular security assessments"
                ],
                estimated_effort="high",
                estimated_impact="high",
                tags=["security", "hardening", "proactive"]
            )
            recommendations.append(rec)

        return recommendations

    def _deduplicate_and_prioritize_recommendations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Remove duplicate recommendations and prioritize."""
        # Simple deduplication by title
        seen_titles = set()
        unique_recommendations = []

        for rec in recommendations:
            if rec.title not in seen_titles:
                seen_titles.add(rec.title)
                unique_recommendations.append(rec)

        # Sort by priority
        priority_order = {
            Priority.URGENT: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }

        unique_recommendations.sort(
            key=lambda x: priority_order.get(x.priority, 3))

        return unique_recommendations

    def _calculate_overall_health_score(self, network_report, security_summary, issues: List[DiagnosticIssue]) -> float:
        """Calculate overall system health score (0-100)."""
        base_score = 100.0

        # Deduct points for network issues
        if network_report.overall_status == NetworkStatus.CRITICAL:
            base_score -= 30
        elif network_report.overall_status == NetworkStatus.POOR:
            base_score -= 20
        elif network_report.overall_status == NetworkStatus.FAIR:
            base_score -= 10

        # Deduct points for security threats
        critical_threats = security_summary.get("critical_threats", 0)
        high_threats = security_summary.get("high_threats", 0)

        base_score -= critical_threats * 15  # 15 points per critical threat
        base_score -= high_threats * 5       # 5 points per high threat

        # Deduct points for diagnostic issues
        for issue in issues:
            if issue.severity == DiagnosticSeverity.CRITICAL:
                base_score -= 10
            elif issue.severity == DiagnosticSeverity.ERROR:
                base_score -= 5
            elif issue.severity == DiagnosticSeverity.WARNING:
                base_score -= 2

        return max(0.0, min(100.0, base_score))

    async def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze performance and security trends."""
        trends = {}

        try:
            # Get network performance trends
            network_trends = self.network_monitor.get_performance_trends(
                hours=24)
            trends["network"] = network_trends

            # Analyze diagnostic history trends
            if len(self.diagnostic_history) >= 2:
                recent_scores = [
                    r.overall_health_score for r in self.diagnostic_history[-10:]]
                if len(recent_scores) >= 2:
                    trend_direction = "improving" if recent_scores[-1] > recent_scores[
                        0] else "declining" if recent_scores[-1] < recent_scores[0] else "stable"
                    trends["health_score"] = {
                        "trend_direction": trend_direction,
                        "current_score": recent_scores[-1],
                        "average_score": statistics.mean(recent_scores),
                        "score_change": recent_scores[-1] - recent_scores[0]
                    }

        except Exception as e:
            logger.warning(f"Trend analysis failed: {e}")

        return trends

    def _generate_executive_summary(self, issues: List[DiagnosticIssue],
                                    recommendations: List[Recommendation],
                                    health_score: float, network_report, security_summary) -> Tuple[str, List[str], List[str]]:
        """Generate executive summary and key findings."""

        # Executive summary
        summary_parts = [
            f"System health score: {health_score:.1f}/100",
            f"Network status: {network_report.overall_status.value}",
            f"Active security threats: {security_summary.get('total_active_threats', 0)}",
            f"Diagnostic issues found: {len(issues)}",
            f"Recommendations generated: {len(recommendations)}"
        ]

        executive_summary = "System Diagnostic Summary: " + \
            ". ".join(summary_parts) + "."

        # Key findings
        key_findings = []

        if health_score >= 90:
            key_findings.append(
                "System is operating at optimal performance levels")
        elif health_score >= 70:
            key_findings.append(
                "System performance is good with minor optimization opportunities")
        elif health_score >= 50:
            key_findings.append(
                "System has moderate performance issues requiring attention")
        else:
            key_findings.append(
                "System has significant performance and security issues requiring immediate action")

        # Add specific findings
        critical_issues = [i for i in issues if i.severity ==
                           DiagnosticSeverity.CRITICAL]
        if critical_issues:
            key_findings.append(
                f"{len(critical_issues)} critical issues require immediate attention")

        if security_summary.get("critical_threats", 0) > 0:
            key_findings.append(
                "Critical security threats detected - immediate response required")

        # Immediate actions
        immediate_actions = []

        urgent_recommendations = [
            r for r in recommendations if r.priority == Priority.URGENT]
        for rec in urgent_recommendations[:3]:  # Top 3 urgent actions
            immediate_actions.append(rec.title)

        if not immediate_actions:
            high_priority_recs = [
                r for r in recommendations if r.priority == Priority.HIGH]
            for rec in high_priority_recs[:3]:  # Top 3 high priority actions
                immediate_actions.append(rec.title)

        if not immediate_actions:
            immediate_actions.append(
                "Continue monitoring system performance and security")

        return executive_summary, key_findings, immediate_actions

    def _get_security_status_summary(self, security_summary: Dict[str, Any]) -> str:
        """Get security status summary."""
        critical_threats = security_summary.get("critical_threats", 0)
        high_threats = security_summary.get("high_threats", 0)
        total_threats = security_summary.get("total_active_threats", 0)

        if critical_threats > 0:
            return "critical"
        elif high_threats > 5:
            return "high_risk"
        elif total_threats > 10:
            return "moderate_risk"
        elif total_threats > 0:
            return "low_risk"
        else:
            return "secure"

    def _load_recommendation_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load recommendation templates."""
        # This would typically load from a configuration file or database
        return {
            "network_optimization": {
                "title": "Network Performance Optimization",
                "type": RecommendationType.PERFORMANCE,
                "priority": Priority.MEDIUM
            },
            "security_hardening": {
                "title": "Security Hardening",
                "type": RecommendationType.SECURITY,
                "priority": Priority.HIGH
            }
        }

    def get_diagnostic_history(self, days: int = 7) -> List[DiagnosticReport]:
        """Get diagnostic report history."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return [r for r in self.diagnostic_history if r.generated_at >= cutoff_date]

    def get_recommendation_status(self, recommendation_id: str) -> Optional[str]:
        """Get status of a specific recommendation."""
        # This would typically be stored in a database
        # For now, return default status
        return "pending"

    async def update_recommendation_status(self, recommendation_id: str, status: str, notes: str = "") -> bool:
        """Update recommendation status."""
        # This would typically update a database
        # For now, just log the update
        logger.info(
            f"Recommendation {recommendation_id} status updated to {status}: {notes}")
        return True


# Factory function
def create_diagnostic_service() -> DiagnosticService:
    """Create a diagnostic service instance."""
    from .network_monitor import create_network_monitor
    from .security_monitor import create_security_monitor

    network_monitor = create_network_monitor()
    security_monitor = create_security_monitor()
    
    # Create a dummy config for diagnostic service
    from ..core.interfaces import MCPServerConfig
    dummy_config = MCPServerConfig(
        name="diagnostic-service",
        command="echo",
        args=["dummy"],
        env={}
    )
    
    mcp_client = MCPClient(dummy_config)

    return DiagnosticService(network_monitor, security_monitor, mcp_client)
