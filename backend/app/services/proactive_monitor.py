"""
Proactive Error Management and AI Analysis Service

This service monitors system health proactively and uses AI to analyze
issues and suggest solutions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

from .health_monitor import get_health_monitor
from .security_manager import get_security_manager, RiskLevel
from .ai_diagnostics import get_ai_diagnostics_engine, SystemContext, DiagnosisResult
from ..core.interfaces import MCPServerStatus


logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PatternType(Enum):
    RECURRING_FAILURE = "recurring_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CASCADE_FAILURE = "cascade_failure"
    RECOVERY_PATTERN = "recovery_pattern"


@dataclass
class SystemAlert:
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any]
    suggested_actions: List[str]
    auto_resolve: bool = False
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class HealthPattern:
    pattern_type: PatternType
    description: str
    confidence: float
    first_occurrence: datetime
    last_occurrence: datetime
    frequency: int
    affected_components: List[str]
    suggested_resolution: str
    metadata: Dict[str, Any]


class ProactiveMonitor:
    """Proactive system monitoring with AI-powered analysis"""
    
    def __init__(self):
        self.alerts: Dict[str, SystemAlert] = {}
        self.patterns: List[HealthPattern] = []
        self.monitoring_active = False
        self.health_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # Pattern detection thresholds
        self.failure_threshold = 3  # Consecutive failures to trigger pattern
        self.performance_threshold = 0.3  # 30% performance degradation
        self.resource_threshold = 0.85  # 85% resource usage
        
    async def start_monitoring(self):
        """Start proactive monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        logger.info("Starting proactive monitoring")
        
        # Start monitoring tasks
        asyncio.create_task(self._health_monitoring_loop())
        asyncio.create_task(self._pattern_analysis_loop())
        asyncio.create_task(self._alert_cleanup_loop())
    
    async def stop_monitoring(self):
        """Stop proactive monitoring"""
        self.monitoring_active = False
        logger.info("Stopping proactive monitoring")
    
    async def _health_monitoring_loop(self):
        """Main health monitoring loop"""
        while self.monitoring_active:
            try:
                await self._collect_health_data()
                await self._analyze_current_state()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _pattern_analysis_loop(self):
        """Pattern analysis loop"""
        while self.monitoring_active:
            try:
                await self._detect_patterns()
                await asyncio.sleep(300)  # Analyze patterns every 5 minutes
            except Exception as e:
                logger.error(f"Error in pattern analysis loop: {e}")
                await asyncio.sleep(300)
    
    async def _alert_cleanup_loop(self):
        """Clean up old alerts"""
        while self.monitoring_active:
            try:
                await self._cleanup_old_alerts()
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Error in alert cleanup loop: {e}")
                await asyncio.sleep(3600)
    
    async def _collect_health_data(self):
        """Collect current health data"""
        try:
            health_monitor = get_health_monitor()
            
            # Get MCP server statuses
            mcp_statuses = await health_monitor.get_all_statuses()
            
            # Get system resources
            import psutil
            system_resources = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids())
            }
            
            # Create health snapshot
            health_snapshot = {
                "timestamp": datetime.now(),
                "mcp_servers": {
                    name: {
                        "status": status.status.value,
                        "response_time_ms": status.response_time_ms,
                        "uptime_percentage": status.uptime_percentage,
                        "error_message": status.error_message
                    }
                    for name, status in mcp_statuses.items()
                },
                "system_resources": system_resources
            }
            
            # Add to history
            self.health_history.append(health_snapshot)
            
            # Limit history size
            if len(self.health_history) > self.max_history_size:
                self.health_history = self.health_history[-self.max_history_size:]
                
        except Exception as e:
            logger.error(f"Failed to collect health data: {e}")
    
    async def _analyze_current_state(self):
        """Analyze current system state for immediate issues"""
        if not self.health_history:
            return
            
        current_snapshot = self.health_history[-1]
        
        # Check MCP servers
        for server_name, server_data in current_snapshot["mcp_servers"].items():
            await self._analyze_server_health(server_name, server_data)
        
        # Check system resources
        await self._analyze_system_resources(current_snapshot["system_resources"])
    
    async def _analyze_server_health(self, server_name: str, server_data: Dict[str, Any]):
        """Analyze individual server health"""
        status = server_data["status"]
        response_time = server_data["response_time_ms"]
        error_message = server_data.get("error_message")
        
        # Check for offline servers
        if status == MCPServerStatus.OFFLINE.value:
            await self._create_alert(
                severity=AlertSeverity.ERROR,
                title=f"MCP Server {server_name} is Offline",
                message=f"Server {server_name} is not responding. Error: {error_message or 'Unknown'}",
                source=f"mcp_server_{server_name}",
                metadata={
                    "server_name": server_name,
                    "status": status,
                    "error_message": error_message
                },
                suggested_actions=[
                    "mcp_server_restart",
                    "investigate_processes",
                    "check_server_logs"
                ]
            )
        
        # Check for degraded performance
        elif status == MCPServerStatus.DEGRADED.value or response_time > 500:
            await self._create_alert(
                severity=AlertSeverity.WARNING,
                title=f"MCP Server {server_name} Performance Degraded",
                message=f"Server {server_name} is showing degraded performance. Response time: {response_time}ms",
                source=f"mcp_server_{server_name}",
                metadata={
                    "server_name": server_name,
                    "status": status,
                    "response_time_ms": response_time
                },
                suggested_actions=[
                    "investigate_processes",
                    "check_server_logs",
                    "resource_optimization"
                ]
            )
    
    async def _analyze_system_resources(self, resources: Dict[str, Any]):
        """Analyze system resource usage"""
        cpu_percent = resources["cpu_percent"]
        memory_percent = resources["memory_percent"]
        disk_percent = resources["disk_percent"]
        
        # High CPU usage
        if cpu_percent > 85:
            await self._create_alert(
                severity=AlertSeverity.WARNING,
                title="High CPU Usage Detected",
                message=f"System CPU usage is at {cpu_percent:.1f}%",
                source="system_resources",
                metadata={"cpu_percent": cpu_percent},
                suggested_actions=[
                    "investigate_processes",
                    "restart_services",
                    "resource_optimization"
                ]
            )
        
        # High memory usage
        if memory_percent > 90:
            await self._create_alert(
                severity=AlertSeverity.ERROR,
                title="High Memory Usage Detected",
                message=f"System memory usage is at {memory_percent:.1f}%",
                source="system_resources",
                metadata={"memory_percent": memory_percent},
                suggested_actions=[
                    "restart_services",
                    "investigate_processes",
                    "memory_cleanup"
                ]
            )
        
        # High disk usage
        if disk_percent > 95:
            await self._create_alert(
                severity=AlertSeverity.CRITICAL,
                title="Critical Disk Space",
                message=f"Disk usage is at {disk_percent:.1f}%",
                source="system_resources",
                metadata={"disk_percent": disk_percent},
                suggested_actions=[
                    "cleanup_logs",
                    "cleanup_temp_files",
                    "disk_maintenance"
                ]
            )
    
    async def _detect_patterns(self):
        """Detect patterns in health history"""
        if len(self.health_history) < 10:  # Need minimum history
            return
        
        # Detect recurring failures
        await self._detect_recurring_failures()
        
        # Detect performance degradation trends
        await self._detect_performance_trends()
        
        # Detect resource exhaustion patterns
        await self._detect_resource_patterns()
        
        # Detect cascade failures
        await self._detect_cascade_failures()
    
    async def _detect_recurring_failures(self):
        """Detect recurring failure patterns"""
        server_failures = {}
        
        # Analyze last 50 snapshots
        recent_history = self.health_history[-50:]
        
        for snapshot in recent_history:
            for server_name, server_data in snapshot["mcp_servers"].items():
                if server_data["status"] in [MCPServerStatus.OFFLINE.value, MCPServerStatus.DEGRADED.value]:
                    if server_name not in server_failures:
                        server_failures[server_name] = []
                    server_failures[server_name].append(snapshot["timestamp"])
        
        # Check for recurring patterns
        for server_name, failure_times in server_failures.items():
            if len(failure_times) >= self.failure_threshold:
                # Calculate failure frequency
                time_span = failure_times[-1] - failure_times[0]
                frequency = len(failure_times) / max(time_span.total_seconds() / 3600, 1)  # failures per hour
                
                pattern = HealthPattern(
                    pattern_type=PatternType.RECURRING_FAILURE,
                    description=f"Server {server_name} has recurring failures",
                    confidence=min(0.9, len(failure_times) / 10),
                    first_occurrence=failure_times[0],
                    last_occurrence=failure_times[-1],
                    frequency=len(failure_times),
                    affected_components=[server_name],
                    suggested_resolution="Investigate root cause and consider server replacement or configuration changes",
                    metadata={
                        "server_name": server_name,
                        "failure_frequency": frequency,
                        "failure_count": len(failure_times)
                    }
                )
                
                await self._add_pattern(pattern)
    
    async def _detect_performance_trends(self):
        """Detect performance degradation trends"""
        if len(self.health_history) < 20:
            return
        
        recent_history = self.health_history[-20:]
        
        for server_name in recent_history[0]["mcp_servers"].keys():
            response_times = []
            
            for snapshot in recent_history:
                server_data = snapshot["mcp_servers"].get(server_name, {})
                if server_data.get("response_time_ms", 0) > 0:
                    response_times.append(server_data["response_time_ms"])
            
            if len(response_times) >= 10:
                # Calculate trend
                early_avg = sum(response_times[:5]) / 5
                recent_avg = sum(response_times[-5:]) / 5
                
                if recent_avg > early_avg * (1 + self.performance_threshold):
                    pattern = HealthPattern(
                        pattern_type=PatternType.PERFORMANCE_DEGRADATION,
                        description=f"Server {server_name} showing performance degradation trend",
                        confidence=0.8,
                        first_occurrence=recent_history[0]["timestamp"],
                        last_occurrence=recent_history[-1]["timestamp"],
                        frequency=1,
                        affected_components=[server_name],
                        suggested_resolution="Monitor server resources and consider optimization or restart",
                        metadata={
                            "server_name": server_name,
                            "early_avg_response": early_avg,
                            "recent_avg_response": recent_avg,
                            "degradation_percent": ((recent_avg - early_avg) / early_avg) * 100
                        }
                    )
                    
                    await self._add_pattern(pattern)
    
    async def _detect_resource_patterns(self):
        """Detect resource exhaustion patterns"""
        if len(self.health_history) < 10:
            return
        
        recent_history = self.health_history[-10:]
        
        # Check for sustained high resource usage
        high_cpu_count = sum(1 for h in recent_history if h["system_resources"]["cpu_percent"] > 80)
        high_memory_count = sum(1 for h in recent_history if h["system_resources"]["memory_percent"] > 80)
        
        if high_cpu_count >= 7:  # 70% of recent samples
            pattern = HealthPattern(
                pattern_type=PatternType.RESOURCE_EXHAUSTION,
                description="Sustained high CPU usage pattern detected",
                confidence=0.9,
                first_occurrence=recent_history[0]["timestamp"],
                last_occurrence=recent_history[-1]["timestamp"],
                frequency=high_cpu_count,
                affected_components=["system_cpu"],
                suggested_resolution="Investigate CPU-intensive processes and consider resource optimization",
                metadata={
                    "resource_type": "cpu",
                    "high_usage_frequency": high_cpu_count,
                    "avg_cpu_usage": sum(h["system_resources"]["cpu_percent"] for h in recent_history) / len(recent_history)
                }
            )
            
            await self._add_pattern(pattern)
        
        if high_memory_count >= 7:
            pattern = HealthPattern(
                pattern_type=PatternType.RESOURCE_EXHAUSTION,
                description="Sustained high memory usage pattern detected",
                confidence=0.9,
                first_occurrence=recent_history[0]["timestamp"],
                last_occurrence=recent_history[-1]["timestamp"],
                frequency=high_memory_count,
                affected_components=["system_memory"],
                suggested_resolution="Investigate memory leaks and consider service restarts",
                metadata={
                    "resource_type": "memory",
                    "high_usage_frequency": high_memory_count,
                    "avg_memory_usage": sum(h["system_resources"]["memory_percent"] for h in recent_history) / len(recent_history)
                }
            )
            
            await self._add_pattern(pattern)
    
    async def _detect_cascade_failures(self):
        """Detect cascade failure patterns"""
        if len(self.health_history) < 5:
            return
        
        recent_history = self.health_history[-5:]
        
        # Look for multiple servers failing in sequence
        failure_sequence = []
        
        for i, snapshot in enumerate(recent_history):
            failed_servers = [
                name for name, data in snapshot["mcp_servers"].items()
                if data["status"] == MCPServerStatus.OFFLINE.value
            ]
            
            if failed_servers:
                failure_sequence.append({
                    "timestamp": snapshot["timestamp"],
                    "failed_servers": failed_servers,
                    "index": i
                })
        
        # Check for cascade pattern (multiple failures in short time)
        if len(failure_sequence) >= 2:
            all_failed_servers = set()
            for failure in failure_sequence:
                all_failed_servers.update(failure["failed_servers"])
            
            if len(all_failed_servers) >= 2:
                pattern = HealthPattern(
                    pattern_type=PatternType.CASCADE_FAILURE,
                    description=f"Cascade failure detected affecting {len(all_failed_servers)} servers",
                    confidence=0.85,
                    first_occurrence=failure_sequence[0]["timestamp"],
                    last_occurrence=failure_sequence[-1]["timestamp"],
                    frequency=len(failure_sequence),
                    affected_components=list(all_failed_servers),
                    suggested_resolution="Investigate common cause (network, resources, dependencies)",
                    metadata={
                        "failed_servers": list(all_failed_servers),
                        "failure_sequence": failure_sequence
                    }
                )
                
                await self._add_pattern(pattern)
    
    async def _create_alert(self, severity: AlertSeverity, title: str, message: str,
                          source: str, metadata: Dict[str, Any], suggested_actions: List[str]):
        """Create a new system alert"""
        import uuid
        
        alert_id = str(uuid.uuid4())
        
        # Check if similar alert already exists
        existing_alert = self._find_similar_alert(source, title)
        if existing_alert and not existing_alert.resolved:
            # Update existing alert instead of creating duplicate
            existing_alert.message = message
            existing_alert.timestamp = datetime.now()
            existing_alert.metadata.update(metadata)
            return
        
        alert = SystemAlert(
            id=alert_id,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            metadata=metadata,
            suggested_actions=suggested_actions,
            auto_resolve=(severity == AlertSeverity.INFO)
        )
        
        self.alerts[alert_id] = alert
        logger.info(f"Created alert: {title} ({severity.value})")
        
        # Trigger webhook notification
        await self._trigger_webhook(alert)
    
    async def _add_pattern(self, pattern: HealthPattern):
        """Add a detected pattern"""
        # Check if pattern already exists
        existing_pattern = self._find_similar_pattern(pattern)
        if existing_pattern:
            # Update existing pattern
            existing_pattern.last_occurrence = pattern.last_occurrence
            existing_pattern.frequency += 1
            existing_pattern.confidence = min(0.95, existing_pattern.confidence + 0.05)
        else:
            self.patterns.append(pattern)
            logger.info(f"Detected new pattern: {pattern.description}")
            
            # Create alert for significant patterns
            if pattern.confidence > 0.7:
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    title=f"Pattern Detected: {pattern.pattern_type.value}",
                    message=pattern.description,
                    source="pattern_detection",
                    metadata={
                        "pattern_type": pattern.pattern_type.value,
                        "confidence": pattern.confidence,
                        "affected_components": pattern.affected_components
                    },
                    suggested_actions=["investigate_pattern", "apply_pattern_resolution"]
                )
    
    def _find_similar_alert(self, source: str, title: str) -> Optional[SystemAlert]:
        """Find similar existing alert"""
        for alert in self.alerts.values():
            if alert.source == source and alert.title == title:
                return alert
        return None
    
    def _find_similar_pattern(self, new_pattern: HealthPattern) -> Optional[HealthPattern]:
        """Find similar existing pattern"""
        for pattern in self.patterns:
            if (pattern.pattern_type == new_pattern.pattern_type and
                set(pattern.affected_components) == set(new_pattern.affected_components)):
                return pattern
        return None
    
    async def _trigger_webhook(self, alert: SystemAlert):
        """Trigger webhook notification for alert"""
        try:
            # In a real implementation, this would send to configured webhooks
            webhook_data = {
                "event_type": "system_alert",
                "alert": {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "source": alert.source,
                    "suggested_actions": alert.suggested_actions,
                    "metadata": alert.metadata
                }
            }
            
            logger.info(f"Webhook triggered for alert: {alert.title}")
            # TODO: Implement actual webhook sending
            
        except Exception as e:
            logger.error(f"Failed to trigger webhook: {e}")
    
    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        alerts_to_remove = []
        for alert_id, alert in self.alerts.items():
            if alert.resolved and alert.timestamp < cutoff_time:
                alerts_to_remove.append(alert_id)
        
        for alert_id in alerts_to_remove:
            del self.alerts[alert_id]
        
        if alerts_to_remove:
            logger.info(f"Cleaned up {len(alerts_to_remove)} old alerts")
    
    # Public API methods
    
    def get_active_alerts(self) -> List[SystemAlert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert(self, alert_id: str) -> Optional[SystemAlert]:
        """Get specific alert by ID"""
        return self.alerts.get(alert_id)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.acknowledged = True
            logger.info(f"Alert acknowledged: {alert.title}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.resolved = True
            logger.info(f"Alert resolved: {alert.title}")
            return True
        return False
    
    def get_detected_patterns(self) -> List[HealthPattern]:
        """Get all detected patterns"""
        return self.patterns.copy()
    
    async def analyze_connection_loss(self, component: str, error_details: str) -> Dict[str, Any]:
        """Analyze connection loss and suggest solutions"""
        security_manager = get_security_manager()
        
        # AI analysis of connection loss
        analysis = {
            "component": component,
            "error_details": error_details,
            "timestamp": datetime.now().isoformat(),
            "possible_causes": [],
            "suggested_solutions": [],
            "confidence": 0.0
        }
        
        # Pattern matching for common issues
        if "connection refused" in error_details.lower():
            analysis["possible_causes"].append("Service is not running")
            analysis["possible_causes"].append("Port is blocked or changed")
            analysis["suggested_solutions"].append("restart_service")
            analysis["suggested_solutions"].append("check_port_configuration")
            analysis["confidence"] = 0.8
        
        elif "timeout" in error_details.lower():
            analysis["possible_causes"].append("Network latency issues")
            analysis["possible_causes"].append("Service overload")
            analysis["suggested_solutions"].append("check_network_connectivity")
            analysis["suggested_solutions"].append("investigate_service_performance")
            analysis["confidence"] = 0.7
        
        elif "authentication" in error_details.lower():
            analysis["possible_causes"].append("Invalid credentials")
            analysis["possible_causes"].append("Token expired")
            analysis["suggested_solutions"].append("refresh_credentials")
            analysis["suggested_solutions"].append("check_authentication_config")
            analysis["confidence"] = 0.9
        
        else:
            analysis["possible_causes"].append("Unknown connection issue")
            analysis["suggested_solutions"].append("check_logs")
            analysis["suggested_solutions"].append("restart_component")
            analysis["confidence"] = 0.5
        
        # Create alert for connection loss
        await self._create_alert(
            severity=AlertSeverity.ERROR,
            title=f"Connection Lost: {component}",
            message=f"Lost connection to {component}. Error: {error_details}",
            source=f"connection_{component}",
            metadata={
                "component": component,
                "error_details": error_details,
                "analysis": analysis
            },
            suggested_actions=analysis["suggested_solutions"]
        )
        
        return analysis

    # AI-Enhanced Methods
    
    async def ai_analyze_system_state(self, current_data: Dict[str, Any]):
        """AI-powered system state analysis"""
        try:
            ai_engine = get_ai_diagnostics_engine()
            
            # Build system context for AI
            system_context = SystemContext(
                current_health=current_data,
                recent_errors=self._get_recent_errors(),
                resource_usage=current_data.get('system_resources', {}),
                mcp_server_status={
                    name: status.status for name, status in current_data.get('mcp_statuses', {}).items()
                },
                user_activity=[],  # TODO: Implement user activity tracking
                timestamp=datetime.now()
            )
            
            # Check if performance analysis is needed
            resources = current_data.get('system_resources', {})
            if (resources.get('cpu_percent', 0) > 70 or 
                resources.get('memory_percent', 0) > 75):
                
                # Get historical data for trend analysis
                historical_data = self.health_history[-10:] if len(self.health_history) >= 10 else self.health_history
                
                # AI performance analysis
                diagnosis = await ai_engine.analyze_performance_issue(
                    metrics=resources,
                    historical_data=historical_data
                )
                
                # Create proactive alert based on AI analysis
                await self._create_ai_alert(diagnosis, 'performance_analysis')
            
            # Check for pattern-based issues
            await self._ai_pattern_detection(system_context)
            
        except Exception as e:
            logger.error(f"AI system state analysis failed: {e}")
    
    async def _ai_pattern_detection(self, system_context: SystemContext):
        """AI-powered pattern detection"""
        try:
            # Analyze recent health history for patterns
            if len(self.health_history) < 5:
                return
            
            # Look for recurring issues
            recent_errors = self._get_recent_errors()
            if len(recent_errors) >= 3:
                # Use AI to analyze error patterns
                ai_engine = get_ai_diagnostics_engine()
                
                # Create a synthetic error for pattern analysis
                pattern_analysis_request = {
                    'error_type': 'pattern_analysis',
                    'error_message': f'Detected {len(recent_errors)} recent errors',
                    'request_context': {
                        'url': 'system_pattern_analysis',
                        'method': 'ANALYSIS'
                    }
                }
                
                diagnosis = await ai_engine.analyze_connection_error(
                    error_details=pattern_analysis_request,
                    system_context=system_context
                )
                
                # Create pattern-based alert
                await self._create_ai_alert(diagnosis, 'pattern_detection')
        
        except Exception as e:
            logger.error(f"AI pattern detection failed: {e}")
    
    async def _create_ai_alert(self, diagnosis: DiagnosisResult, analysis_type: str):
        """Create alert based on AI diagnosis"""
        try:
            alert_id = f"ai_{analysis_type}_{datetime.now().timestamp()}"
            
            # Map AI severity to alert severity
            severity_mapping = {
                'low': AlertSeverity.INFO,
                'medium': AlertSeverity.WARNING,
                'high': AlertSeverity.ERROR,
                'critical': AlertSeverity.CRITICAL
            }
            
            alert = SystemAlert(
                id=alert_id,
                severity=severity_mapping.get(diagnosis.severity.value, AlertSeverity.WARNING),
                title=f"AI Analysis: {diagnosis.issue_type.replace('_', ' ').title()}",
                message=diagnosis.user_friendly_explanation,
                timestamp=datetime.now(),
                source="ai_proactive_monitor",
                metadata={
                    'ai_analysis': {
                        'root_cause': diagnosis.root_cause_analysis,
                        'confidence': diagnosis.confidence_score,
                        'analysis_type': analysis_type
                    },
                    'suggested_actions': [
                        {
                            'title': action.title,
                            'description': action.description,
                            'risk_level': action.risk_level,
                            'estimated_duration': action.estimated_duration
                        }
                        for action in diagnosis.suggested_actions
                    ]
                },
                suggested_actions=[action.title for action in diagnosis.suggested_actions],
                auto_resolve=diagnosis.confidence_score > 0.8 and diagnosis.severity.value == 'low'
            )
            
            self.alerts[alert_id] = alert
            
            # Log AI alert creation
            logger.info(f"AI Alert created: {alert.title} (confidence: {diagnosis.confidence_score:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to create AI alert: {e}")
    
    def _get_recent_errors(self) -> List[Dict[str, Any]]:
        """Get recent errors from health history"""
        recent_errors = []
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        for health_data in reversed(self.health_history):
            if health_data.get('timestamp', datetime.min) < cutoff_time:
                break
                
            # Check for errors in MCP server statuses
            mcp_statuses = health_data.get('mcp_statuses', {})
            for server_name, status in mcp_statuses.items():
                if hasattr(status, 'status') and status.status in ['OFFLINE', 'DEGRADED']:
                    recent_errors.append({
                        'type': 'mcp_server_error',
                        'server': server_name,
                        'status': status.status,
                        'error_message': getattr(status, 'error_message', ''),
                        'timestamp': health_data.get('timestamp', datetime.now())
                    })
            
            # Check for resource issues
            resources = health_data.get('system_resources', {})
            if resources.get('cpu_percent', 0) > 90:
                recent_errors.append({
                    'type': 'high_cpu_usage',
                    'value': resources.get('cpu_percent'),
                    'timestamp': health_data.get('timestamp', datetime.now())
                })
            
            if resources.get('memory_percent', 0) > 90:
                recent_errors.append({
                    'type': 'high_memory_usage',
                    'value': resources.get('memory_percent'),
                    'timestamp': health_data.get('timestamp', datetime.now())
                })
        
        return recent_errors
    
    async def get_ai_insights(self) -> List[Dict[str, Any]]:
        """Get AI-generated insights about system health"""
        try:
            insights = []
            
            # Get AI alerts
            ai_alerts = [alert for alert in self.alerts.values() 
                        if alert.source == "ai_proactive_monitor" and not alert.resolved]
            
            for alert in ai_alerts:
                ai_metadata = alert.metadata.get('ai_analysis', {})
                insights.append({
                    'id': alert.id,
                    'type': 'ai_alert',
                    'title': alert.title,
                    'message': alert.message,
                    'severity': alert.severity.value,
                    'confidence': ai_metadata.get('confidence', 0.0),
                    'root_cause': ai_metadata.get('root_cause', ''),
                    'suggested_actions': alert.metadata.get('suggested_actions', []),
                    'timestamp': alert.timestamp.isoformat(),
                    'auto_resolve': alert.auto_resolve
                })
            
            # Get pattern insights
            pattern_insights = await self._get_pattern_insights()
            insights.extend(pattern_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get AI insights: {e}")
            return []
    
    async def _get_pattern_insights(self) -> List[Dict[str, Any]]:
        """Get insights from detected patterns"""
        insights = []
        
        try:
            # Analyze health history for patterns
            if len(self.health_history) < 10:
                return insights
            
            # CPU usage pattern
            cpu_values = [h.get('system_resources', {}).get('cpu_percent', 0) 
                         for h in self.health_history[-20:]]
            if cpu_values:
                avg_cpu = sum(cpu_values) / len(cpu_values)
                if avg_cpu > 60:
                    insights.append({
                        'id': f'pattern_cpu_{datetime.now().timestamp()}',
                        'type': 'pattern_insight',
                        'title': 'High CPU Usage Pattern Detected',
                        'message': f'Average CPU usage over last 20 checks: {avg_cpu:.1f}%',
                        'severity': 'warning' if avg_cpu > 70 else 'info',
                        'confidence': 0.8,
                        'pattern_type': 'resource_usage',
                        'suggested_actions': [
                            'Monitor CPU-intensive processes',
                            'Consider scaling resources',
                            'Review MCP server performance'
                        ]
                    })
            
            # MCP server failure pattern
            server_failures = {}
            for health_data in self.health_history[-10:]:
                mcp_statuses = health_data.get('mcp_statuses', {})
                for server_name, status in mcp_statuses.items():
                    if hasattr(status, 'status') and status.status != 'HEALTHY':
                        server_failures[server_name] = server_failures.get(server_name, 0) + 1
            
            for server_name, failure_count in server_failures.items():
                if failure_count >= 3:
                    insights.append({
                        'id': f'pattern_server_{server_name}_{datetime.now().timestamp()}',
                        'type': 'pattern_insight',
                        'title': f'Recurring Issues: {server_name}',
                        'message': f'Server {server_name} has been unhealthy in {failure_count}/10 recent checks',
                        'severity': 'error' if failure_count >= 5 else 'warning',
                        'confidence': 0.9,
                        'pattern_type': 'recurring_failure',
                        'server_name': server_name,
                        'suggested_actions': [
                            f'Restart {server_name} server',
                            'Check server logs for errors',
                            'Review server configuration'
                        ]
                    })
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get pattern insights: {e}")
            return []


# Singleton instance
_proactive_monitor = None


def get_proactive_monitor() -> ProactiveMonitor:
    """Get proactive monitor singleton"""
    global _proactive_monitor
    if _proactive_monitor is None:
        _proactive_monitor = ProactiveMonitor()
    return _proactive_monitor