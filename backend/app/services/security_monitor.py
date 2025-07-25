"""
Security threat detection and monitoring service.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import re

from .mcp_client import MCPClient
from ..core.error_handling import get_error_handler, MCPError

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Security threat levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats."""
    MALWARE = "malware"
    PHISHING = "phishing"
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    VULNERABILITY = "vulnerability"
    API_ABUSE = "api_abuse"
    CREDENTIAL_EXPOSURE = "credential_exposure"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class SecurityThreat:
    """Security threat detection."""
    threat_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    title: str
    description: str
    source: str
    target: Optional[str] = None

    # Detection details
    indicators: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.5

    # Timing
    first_detected: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)

    # Response
    status: AlertStatus = AlertStatus.ACTIVE
    mitigation_steps: List[str] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    related_threats: List[str] = field(default_factory=list)


@dataclass
class SecurityIncident:
    """Security incident record."""
    incident_id: str
    title: str
    description: str
    severity: ThreatLevel
    threats: List[SecurityThreat]

    # Timeline
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    # Response
    status: AlertStatus = AlertStatus.ACTIVE
    assigned_to: Optional[str] = None
    response_actions: List[str] = field(default_factory=list)

    # Impact assessment
    affected_systems: List[str] = field(default_factory=list)
    estimated_impact: str = "unknown"


class SecurityMonitor:
    """Security threat detection and monitoring service."""

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.error_handler = get_error_handler()

        # Active threats and incidents
        self.active_threats: Dict[str, SecurityThreat] = {}
        self.incidents: Dict[str, SecurityIncident] = {}

        # Monitoring state
        self.monitoring_active = False
        self.last_scan_time = datetime.utcnow()

        # Threat detection patterns
        self.threat_patterns = {
            ThreatType.BRUTE_FORCE: [
                r'failed login.*(\d+) times',
                r'authentication failure.*repeated',
                r'multiple failed attempts'
            ],
            ThreatType.SUSPICIOUS_ACTIVITY: [
                r'unusual traffic pattern',
                r'anomalous behavior detected',
                r'suspicious user agent'
            ],
            ThreatType.API_ABUSE: [
                r'rate limit exceeded',
                r'api quota exceeded',
                r'excessive requests'
            ]
        }

        # Known malicious indicators
        self.malicious_indicators = {
            'ips': set(),
            'domains': set(),
            'hashes': set(),
            'patterns': []
        }

    async def scan_for_threats(self) -> List[SecurityThreat]:
        """Perform comprehensive security threat scan."""
        scan_id = f"security_scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        try:
            logger.info(f"Starting security threat scan {scan_id}")

            threats = []

            # 1. API key and credential exposure scan
            credential_threats = await self._scan_credential_exposure()
            threats.extend(credential_threats)

            # 2. Network-based threat detection
            network_threats = await self._scan_network_threats()
            threats.extend(network_threats)

            # 3. System vulnerability scan
            vulnerability_threats = await self._scan_vulnerabilities()
            threats.extend(vulnerability_threats)

            # 4. Behavioral analysis
            behavioral_threats = await self._analyze_suspicious_behavior()
            threats.extend(behavioral_threats)

            # Update active threats
            for threat in threats:
                self.active_threats[threat.threat_id] = threat

            # Create incidents for high-severity threats
            await self._create_incidents_from_threats(threats)

            self.last_scan_time = datetime.utcnow()
            logger.info(
                f"Security scan {scan_id} completed: {len(threats)} threats detected")

            return threats

        except Exception as e:
            self.error_handler.handle_workflow_error(
                error=e,
                workflow_id="security_monitoring",
                execution_id=scan_id,
                context={"operation": "threat_scan"}
            )
            raise

    async def _scan_credential_exposure(self) -> List[SecurityThreat]:
        """Scan for exposed credentials and API keys."""
        threats = []

        try:
            # Use API key sniffer to detect exposed credentials
            # This would typically scan logs, configuration files, etc.

            # For demonstration, we'll simulate scanning recent activity
            scan_result = await self.mcp_client.call_tool(
                server_name="api-key-sniffer",
                tool_name="list_keys",
                arguments={}
            )

            if isinstance(scan_result, dict) and scan_result.get("keys"):
                for key_info in scan_result["keys"]:
                    threat = SecurityThreat(
                        threat_id=f"cred_exposure_{hashlib.md5(key_info.get('pattern', '').encode()).hexdigest()[:8]}",
                        threat_type=ThreatType.CREDENTIAL_EXPOSURE,
                        threat_level=ThreatLevel.HIGH,
                        title="Exposed API Key Detected",
                        description=f"API key or credential detected in system: {key_info.get('type', 'unknown')}",
                        source="api-key-sniffer",
                        indicators=[key_info.get('pattern', '')[:20] + "..."],
                        evidence={
                            "detection_method": "pattern_matching",
                            "key_type": key_info.get('type'),
                            "confidence": key_info.get('confidence', 0.8)
                        },
                        confidence_score=key_info.get('confidence', 0.8),
                        mitigation_steps=[
                            "Immediately rotate the exposed credential",
                            "Review access logs for unauthorized usage",
                            "Implement proper secret management",
                            "Scan for additional exposures"
                        ],
                        tags=["credential", "exposure", "api-key"]
                    )
                    threats.append(threat)

        except Exception as e:
            logger.warning(f"Credential exposure scan failed: {e}")

        return threats

    async def _scan_network_threats(self) -> List[SecurityThreat]:
        """Scan for network-based security threats."""
        threats = []

        try:
            # Get network connections and analyze for suspicious activity
            connections_result = await self.mcp_client.call_tool(
                server_name="network-analysis",
                tool_name="get_active_connections",
                arguments={}
            )

            if isinstance(connections_result, dict) and "connections" in connections_result:
                connections = connections_result["connections"]

                # Analyze connection patterns
                connection_analysis = self._analyze_connections(connections)

                # Check for suspicious patterns
                if connection_analysis.get("suspicious_ips"):
                    for ip in connection_analysis["suspicious_ips"]:
                        threat = SecurityThreat(
                            threat_id=f"suspicious_ip_{hashlib.md5(ip.encode()).hexdigest()[:8]}",
                            threat_type=ThreatType.SUSPICIOUS_ACTIVITY,
                            threat_level=ThreatLevel.MEDIUM,
                            title="Suspicious IP Connection",
                            description=f"Connection detected from potentially suspicious IP: {ip}",
                            source="network-analysis",
                            target=ip,
                            indicators=[f"IP: {ip}"],
                            evidence=connection_analysis.get(
                                "ip_details", {}).get(ip, {}),
                            confidence_score=0.6,
                            mitigation_steps=[
                                "Investigate the source of the connection",
                                "Check firewall rules",
                                "Monitor for additional activity",
                                "Consider blocking if confirmed malicious"
                            ],
                            tags=["network", "suspicious-ip", "connection"]
                        )
                        threats.append(threat)

                # Check for potential DDoS patterns
                if connection_analysis.get("high_connection_count", 0) > 1000:
                    threat = SecurityThreat(
                        threat_id=f"potential_ddos_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                        threat_type=ThreatType.DDoS,
                        threat_level=ThreatLevel.HIGH,
                        title="Potential DDoS Attack",
                        description=f"Unusually high number of connections detected: {connection_analysis['high_connection_count']}",
                        source="network-analysis",
                        indicators=[
                            f"Connection count: {connection_analysis['high_connection_count']}"],
                        evidence={"connection_analysis": connection_analysis},
                        confidence_score=0.7,
                        mitigation_steps=[
                            "Enable DDoS protection",
                            "Implement rate limiting",
                            "Monitor traffic patterns",
                            "Contact ISP if necessary"
                        ],
                        tags=["network", "ddos", "high-traffic"]
                    )
                    threats.append(threat)

        except Exception as e:
            logger.warning(f"Network threat scan failed: {e}")

        return threats

    async def _scan_vulnerabilities(self) -> List[SecurityThreat]:
        """Scan for system vulnerabilities."""
        threats = []

        try:
            # Get system information for vulnerability assessment
            # This is a simplified example - real implementation would use vulnerability databases

            # Check for common security misconfigurations
            misconfigurations = await self._check_security_configurations()

            for config_issue in misconfigurations:
                threat = SecurityThreat(
                    threat_id=f"vuln_{hashlib.md5(config_issue['name'].encode()).hexdigest()[:8]}",
                    threat_type=ThreatType.VULNERABILITY,
                    threat_level=ThreatLevel(
                        config_issue.get('severity', 'medium')),
                    title=f"Security Misconfiguration: {config_issue['name']}",
                    description=config_issue['description'],
                    source="security-scanner",
                    indicators=[config_issue['indicator']],
                    evidence=config_issue.get('evidence', {}),
                    confidence_score=config_issue.get('confidence', 0.8),
                    mitigation_steps=config_issue.get('mitigation', []),
                    tags=["vulnerability", "misconfiguration"]
                )
                threats.append(threat)

        except Exception as e:
            logger.warning(f"Vulnerability scan failed: {e}")

        return threats

    async def _analyze_suspicious_behavior(self) -> List[SecurityThreat]:
        """Analyze system behavior for suspicious patterns."""
        threats = []

        try:
            # This would typically analyze logs, user behavior, etc.
            # For demonstration, we'll check for some basic patterns

            # Simulate behavioral analysis
            behavioral_indicators = await self._get_behavioral_indicators()

            for indicator in behavioral_indicators:
                if indicator['risk_score'] > 0.7:
                    threat = SecurityThreat(
                        threat_id=f"behavior_{hashlib.md5(indicator['pattern'].encode()).hexdigest()[:8]}",
                        threat_type=ThreatType.SUSPICIOUS_ACTIVITY,
                        threat_level=ThreatLevel.MEDIUM if indicator[
                            'risk_score'] < 0.9 else ThreatLevel.HIGH,
                        title=f"Suspicious Behavior: {indicator['type']}",
                        description=indicator['description'],
                        source="behavioral-analysis",
                        indicators=[indicator['pattern']],
                        evidence=indicator.get('evidence', {}),
                        confidence_score=indicator['risk_score'],
                        mitigation_steps=[
                            "Investigate the suspicious activity",
                            "Review user access patterns",
                            "Check for unauthorized changes",
                            "Implement additional monitoring"
                        ],
                        tags=["behavioral", "suspicious", indicator['type']]
                    )
                    threats.append(threat)

        except Exception as e:
            logger.warning(f"Behavioral analysis failed: {e}")

        return threats

    def _analyze_connections(self, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze network connections for suspicious patterns."""
        analysis = {
            "total_connections": len(connections),
            "unique_remote_ips": set(),
            "suspicious_ips": [],
            "high_connection_count": 0,
            "ip_details": {}
        }

        # Count connections per IP
        ip_counts = {}
        for conn in connections:
            remote_ip = conn.get("remote_address", "")
            if remote_ip:
                analysis["unique_remote_ips"].add(remote_ip)
                ip_counts[remote_ip] = ip_counts.get(remote_ip, 0) + 1

        analysis["high_connection_count"] = len(connections)

        # Identify suspicious IPs (high connection count, known bad IPs, etc.)
        for ip, count in ip_counts.items():
            if count > 50:  # Threshold for suspicious activity
                analysis["suspicious_ips"].append(ip)
                analysis["ip_details"][ip] = {
                    "connection_count": count,
                    "reason": "high_connection_count"
                }

            # Check against known malicious IPs (would be populated from threat intelligence)
            if ip in self.malicious_indicators['ips']:
                analysis["suspicious_ips"].append(ip)
                analysis["ip_details"][ip] = {
                    "connection_count": count,
                    "reason": "known_malicious"
                }

        return analysis

    async def _check_security_configurations(self) -> List[Dict[str, Any]]:
        """Check for common security misconfigurations."""
        misconfigurations = []

        # Example security checks
        checks = [
            {
                "name": "Default Credentials",
                "description": "System may be using default credentials",
                "severity": "high",
                "indicator": "default_creds_detected",
                "confidence": 0.6,
                "mitigation": [
                    "Change all default passwords",
                    "Implement strong password policies",
                    "Enable multi-factor authentication"
                ]
            },
            {
                "name": "Unencrypted Communications",
                "description": "Unencrypted network communications detected",
                "severity": "medium",
                "indicator": "unencrypted_traffic",
                "confidence": 0.7,
                "mitigation": [
                    "Enable TLS/SSL encryption",
                    "Update communication protocols",
                    "Implement certificate management"
                ]
            }
        ]

        # In a real implementation, these would be actual security checks
        # For now, we'll return a subset based on some conditions
        return checks[:1]  # Return first check as example

    async def _get_behavioral_indicators(self) -> List[Dict[str, Any]]:
        """Get behavioral indicators for analysis."""
        # This would typically analyze logs, user patterns, etc.
        # For demonstration, return some example indicators

        indicators = [
            {
                "type": "unusual_access_pattern",
                "pattern": "off_hours_access",
                "description": "User access detected during unusual hours",
                "risk_score": 0.6,
                "evidence": {
                    "access_time": "03:00 AM",
                    "user": "system_user",
                    "frequency": "rare"
                }
            }
        ]

        return indicators

    async def _create_incidents_from_threats(self, threats: List[SecurityThreat]):
        """Create security incidents from high-severity threats."""
        high_severity_threats = [t for t in threats if t.threat_level in [
            ThreatLevel.HIGH, ThreatLevel.CRITICAL]]

        if not high_severity_threats:
            return

        # Group related threats into incidents
        incident_groups = self._group_related_threats(high_severity_threats)

        for group in incident_groups:
            incident_id = f"incident_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.incidents)}"

            # Determine incident severity (highest threat level)
            max_severity = max(threat.threat_level for threat in group)

            incident = SecurityIncident(
                incident_id=incident_id,
                title=f"Security Incident - {group[0].threat_type.value.title()}",
                description=f"Multiple security threats detected: {', '.join(t.title for t in group)}",
                severity=max_severity,
                threats=group,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                affected_systems=[t.target for t in group if t.target],
                estimated_impact="under_investigation"
            )

            self.incidents[incident_id] = incident
            logger.warning(
                f"Security incident created: {incident_id} - {incident.title}")

    def _group_related_threats(self, threats: List[SecurityThreat]) -> List[List[SecurityThreat]]:
        """Group related threats together."""
        # Simple grouping by threat type and target
        groups = {}

        for threat in threats:
            key = f"{threat.threat_type.value}_{threat.target or 'global'}"
            if key not in groups:
                groups[key] = []
            groups[key].append(threat)

        return list(groups.values())

    async def start_continuous_monitoring(self, interval_seconds: int = 600) -> str:
        """Start continuous security monitoring."""
        if self.monitoring_active:
            raise ValueError("Security monitoring is already active")

        monitoring_id = f"security_monitor_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.monitoring_active = True

        logger.info(f"Starting continuous security monitoring {monitoring_id}")

        # Start monitoring task
        asyncio.create_task(self._monitoring_loop(interval_seconds))

        return monitoring_id

    async def stop_continuous_monitoring(self):
        """Stop continuous security monitoring."""
        self.monitoring_active = False
        logger.info("Continuous security monitoring stopped")

    async def _monitoring_loop(self, interval_seconds: int):
        """Continuous security monitoring loop."""
        while self.monitoring_active:
            try:
                await self.scan_for_threats()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in security monitoring loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    def get_active_threats(self, threat_level: Optional[ThreatLevel] = None) -> List[SecurityThreat]:
        """Get active security threats."""
        threats = list(self.active_threats.values())

        if threat_level:
            threats = [t for t in threats if t.threat_level == threat_level]

        return sorted(threats, key=lambda x: x.first_detected, reverse=True)

    def get_security_incidents(self, status: Optional[AlertStatus] = None) -> List[SecurityIncident]:
        """Get security incidents."""
        incidents = list(self.incidents.values())

        if status:
            incidents = [i for i in incidents if i.status == status]

        return sorted(incidents, key=lambda x: x.created_at, reverse=True)

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security monitoring summary."""
        active_threats = self.get_active_threats()
        active_incidents = self.get_security_incidents(AlertStatus.ACTIVE)

        threat_counts = {}
        for threat in active_threats:
            threat_counts[threat.threat_level.value] = threat_counts.get(
                threat.threat_level.value, 0) + 1

        return {
            "total_active_threats": len(active_threats),
            "total_active_incidents": len(active_incidents),
            "threat_level_breakdown": threat_counts,
            "last_scan_time": self.last_scan_time.isoformat(),
            "monitoring_active": self.monitoring_active,
            "critical_threats": len([t for t in active_threats if t.threat_level == ThreatLevel.CRITICAL]),
            "high_threats": len([t for t in active_threats if t.threat_level == ThreatLevel.HIGH])
        }

    async def resolve_threat(self, threat_id: str, resolution_notes: str = "") -> bool:
        """Mark a threat as resolved."""
        if threat_id not in self.active_threats:
            return False

        threat = self.active_threats[threat_id]
        threat.status = AlertStatus.RESOLVED

        # Update related incidents
        for incident in self.incidents.values():
            if any(t.threat_id == threat_id for t in incident.threats):
                # Check if all threats in incident are resolved
                all_resolved = all(
                    t.status == AlertStatus.RESOLVED for t in incident.threats)
                if all_resolved:
                    incident.status = AlertStatus.RESOLVED
                    incident.resolved_at = datetime.utcnow()

                incident.response_actions.append(
                    f"Threat {threat_id} resolved: {resolution_notes}")
                incident.updated_at = datetime.utcnow()

        logger.info(f"Threat {threat_id} marked as resolved")
        return True


# Factory function
def create_security_monitor() -> SecurityMonitor:
    """Create a security monitor instance."""
    from ..core.interfaces import MCPServerConfig
    
    # Create a dummy config for security monitoring
    dummy_config = MCPServerConfig(
        name="security-monitor",
        command="echo",
        args=["dummy"],
        env={}
    )
    
    mcp_client = MCPClient(dummy_config)
    return SecurityMonitor(mcp_client)
