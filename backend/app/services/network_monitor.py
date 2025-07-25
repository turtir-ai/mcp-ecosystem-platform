"""
Network performance monitoring service using network-analysis MCP server.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import statistics

from .mcp_client import MCPClient
from ..core.error_handling import get_error_handler, MCPError

logger = logging.getLogger(__name__)


class NetworkStatus(str, Enum):
    """Network status levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"
    OFFLINE = "offline"


class MetricType(str, Enum):
    """Types of network metrics."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    PACKET_LOSS = "packet_loss"
    JITTER = "jitter"
    BANDWIDTH = "bandwidth"
    CONNECTION_COUNT = "connection_count"
    DNS_RESOLUTION = "dns_resolution"


@dataclass
class NetworkMetric:
    """Individual network metric measurement."""
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    target: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkInterface:
    """Network interface information."""
    name: str
    ip_address: str
    mac_address: str
    status: str
    speed: Optional[int] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    packets_sent: Optional[int] = None
    packets_received: Optional[int] = None
    errors_in: Optional[int] = None
    errors_out: Optional[int] = None


@dataclass
class NetworkConnection:
    """Active network connection information."""
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    status: str
    protocol: str
    process_id: Optional[int] = None
    process_name: Optional[str] = None


@dataclass
class NetworkReport:
    """Comprehensive network monitoring report."""
    report_id: str
    overall_status: NetworkStatus
    interfaces: List[NetworkInterface]
    connections: List[NetworkConnection]
    metrics: List[NetworkMetric]
    performance_summary: Dict[str, Any]
    recommendations: List[str]
    created_at: datetime
    monitoring_duration_seconds: float


class NetworkMonitor:
    """Network performance monitoring service."""

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.error_handler = get_error_handler()
        self.metric_history: Dict[str, List[NetworkMetric]] = {}
        self.monitoring_active = False

        # Performance thresholds
        self.thresholds = {
            MetricType.LATENCY: {
                "excellent": 20,    # ms
                "good": 50,
                "fair": 100,
                "poor": 200,
                "critical": 500
            },
            MetricType.PACKET_LOSS: {
                "excellent": 0.1,   # %
                "good": 0.5,
                "fair": 1.0,
                "poor": 2.0,
                "critical": 5.0
            },
            MetricType.JITTER: {
                "excellent": 5,     # ms
                "good": 15,
                "fair": 30,
                "poor": 50,
                "critical": 100
            }
        }

    async def get_network_status(self) -> NetworkReport:
        """Get comprehensive network status report."""
        report_id = f"network_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()

        try:
            logger.info(f"Generating network status report {report_id}")

            # Collect network information
            interfaces = await self._get_network_interfaces()
            connections = await self._get_active_connections()
            metrics = await self._collect_performance_metrics()

            # Analyze performance
            performance_summary = self._analyze_performance(metrics)
            overall_status = self._determine_overall_status(
                performance_summary)
            recommendations = self._generate_recommendations(
                performance_summary, interfaces, connections)

            # Calculate monitoring duration
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            report = NetworkReport(
                report_id=report_id,
                overall_status=overall_status,
                interfaces=interfaces,
                connections=connections,
                metrics=metrics,
                performance_summary=performance_summary,
                recommendations=recommendations,
                created_at=start_time,
                monitoring_duration_seconds=duration
            )

            logger.info(
                f"Network report {report_id} completed: {overall_status.value} status")
            return report

        except Exception as e:
            self.error_handler.handle_workflow_error(
                error=e,
                workflow_id="network_monitoring",
                execution_id=report_id,
                context={"operation": "status_report"}
            )
            raise

    async def _get_network_interfaces(self) -> List[NetworkInterface]:
        """Get network interface information."""
        try:
            result = await self.mcp_client.call_tool(
                tool_name="get_network_interfaces",
                arguments={}
            )

            interfaces = []
            if isinstance(result, dict) and "interfaces" in result:
                for iface_data in result["interfaces"]:
                    interface = NetworkInterface(
                        name=iface_data.get("name", ""),
                        ip_address=iface_data.get("ip_address", ""),
                        mac_address=iface_data.get("mac_address", ""),
                        status=iface_data.get("status", "unknown"),
                        speed=iface_data.get("speed"),
                        bytes_sent=iface_data.get("bytes_sent"),
                        bytes_received=iface_data.get("bytes_received"),
                        packets_sent=iface_data.get("packets_sent"),
                        packets_received=iface_data.get("packets_received"),
                        errors_in=iface_data.get("errors_in"),
                        errors_out=iface_data.get("errors_out")
                    )
                    interfaces.append(interface)

            return interfaces

        except Exception as e:
            logger.warning(f"Failed to get network interfaces: {e}")
            return []

    async def _get_active_connections(self) -> List[NetworkConnection]:
        """Get active network connections."""
        try:
            result = await self.mcp_client.call_tool(
                tool_name="get_active_connections",
                arguments={}
            )

            connections = []
            if isinstance(result, dict) and "connections" in result:
                for conn_data in result["connections"]:
                    connection = NetworkConnection(
                        local_address=conn_data.get("local_address", ""),
                        local_port=conn_data.get("local_port", 0),
                        remote_address=conn_data.get("remote_address", ""),
                        remote_port=conn_data.get("remote_port", 0),
                        status=conn_data.get("status", "unknown"),
                        protocol=conn_data.get("protocol", "tcp"),
                        process_id=conn_data.get("process_id"),
                        process_name=conn_data.get("process_name")
                    )
                    connections.append(connection)

            return connections

        except Exception as e:
            logger.warning(f"Failed to get active connections: {e}")
            return []

    async def _collect_performance_metrics(self) -> List[NetworkMetric]:
        """Collect network performance metrics."""
        metrics = []
        timestamp = datetime.utcnow()

        # Test common targets
        test_targets = [
            "8.8.8.8",      # Google DNS
            "1.1.1.1",      # Cloudflare DNS
            "google.com",   # Popular website
            "github.com"    # Development platform
        ]

        for target in test_targets:
            try:
                # Ping test for latency
                ping_result = await self.mcp_client.call_tool(
                    tool_name="ping_host",
                    arguments={"host": target, "count": 4}
                )

                if isinstance(ping_result, dict):
                    # Extract latency metrics
                    if "avg_time" in ping_result:
                        metrics.append(NetworkMetric(
                            metric_type=MetricType.LATENCY,
                            value=ping_result["avg_time"],
                            unit="ms",
                            timestamp=timestamp,
                            target=target,
                            metadata={
                                "min_time": ping_result.get("min_time"),
                                "max_time": ping_result.get("max_time"),
                                "packets_sent": ping_result.get("packets_sent"),
                                "packets_received": ping_result.get("packets_received")
                            }
                        ))

                    # Calculate packet loss
                    if "packets_sent" in ping_result and "packets_received" in ping_result:
                        sent = ping_result["packets_sent"]
                        received = ping_result["packets_received"]
                        loss_percent = ((sent - received) /
                                        sent * 100) if sent > 0 else 0

                        metrics.append(NetworkMetric(
                            metric_type=MetricType.PACKET_LOSS,
                            value=loss_percent,
                            unit="%",
                            timestamp=timestamp,
                            target=target
                        ))

                    # Calculate jitter if available
                    if "times" in ping_result and len(ping_result["times"]) > 1:
                        times = ping_result["times"]
                        jitter = statistics.stdev(
                            times) if len(times) > 1 else 0

                        metrics.append(NetworkMetric(
                            metric_type=MetricType.JITTER,
                            value=jitter,
                            unit="ms",
                            timestamp=timestamp,
                            target=target
                        ))

            except Exception as e:
                logger.warning(f"Failed to ping {target}: {e}")

        # DNS resolution test
        try:
            dns_result = await self.mcp_client.call_tool(
                tool_name="dns_lookup",
                arguments={"hostname": "google.com"}
            )

            if isinstance(dns_result, dict) and "resolution_time" in dns_result:
                metrics.append(NetworkMetric(
                    metric_type=MetricType.DNS_RESOLUTION,
                    value=dns_result["resolution_time"],
                    unit="ms",
                    timestamp=timestamp,
                    target="google.com",
                    metadata={"addresses": dns_result.get("addresses", [])}
                ))

        except Exception as e:
            logger.warning(f"DNS resolution test failed: {e}")

        # Get network statistics
        try:
            stats_result = await self.mcp_client.call_tool(
                tool_name="get_network_stats",
                arguments={}
            )

            if isinstance(stats_result, dict):
                # Add connection count metric
                if "active_connections" in stats_result:
                    metrics.append(NetworkMetric(
                        metric_type=MetricType.CONNECTION_COUNT,
                        value=stats_result["active_connections"],
                        unit="connections",
                        timestamp=timestamp
                    ))

                # Add bandwidth metrics if available
                if "bandwidth_usage" in stats_result:
                    bandwidth = stats_result["bandwidth_usage"]
                    metrics.append(NetworkMetric(
                        metric_type=MetricType.BANDWIDTH,
                        value=bandwidth,
                        unit="Mbps",
                        timestamp=timestamp
                    ))

        except Exception as e:
            logger.warning(f"Failed to get network stats: {e}")

        # Store metrics in history
        for metric in metrics:
            key = f"{metric.metric_type.value}_{metric.target or 'global'}"
            if key not in self.metric_history:
                self.metric_history[key] = []

            self.metric_history[key].append(metric)

            # Keep only last 100 measurements
            if len(self.metric_history[key]) > 100:
                self.metric_history[key] = self.metric_history[key][-100:]

        return metrics

    def _analyze_performance(self, metrics: List[NetworkMetric]) -> Dict[str, Any]:
        """Analyze network performance metrics."""
        analysis = {
            "latency": {"values": [], "avg": 0, "status": NetworkStatus.GOOD},
            "packet_loss": {"values": [], "avg": 0, "status": NetworkStatus.GOOD},
            "jitter": {"values": [], "avg": 0, "status": NetworkStatus.GOOD},
            "dns_resolution": {"values": [], "avg": 0, "status": NetworkStatus.GOOD},
            "connection_count": 0,
            "bandwidth_usage": 0
        }

        # Group metrics by type
        for metric in metrics:
            if metric.metric_type == MetricType.LATENCY:
                analysis["latency"]["values"].append(metric.value)
            elif metric.metric_type == MetricType.PACKET_LOSS:
                analysis["packet_loss"]["values"].append(metric.value)
            elif metric.metric_type == MetricType.JITTER:
                analysis["jitter"]["values"].append(metric.value)
            elif metric.metric_type == MetricType.DNS_RESOLUTION:
                analysis["dns_resolution"]["values"].append(metric.value)
            elif metric.metric_type == MetricType.CONNECTION_COUNT:
                analysis["connection_count"] = metric.value
            elif metric.metric_type == MetricType.BANDWIDTH:
                analysis["bandwidth_usage"] = metric.value

        # Calculate averages and determine status
        for metric_name in ["latency", "packet_loss", "jitter", "dns_resolution"]:
            values = analysis[metric_name]["values"]
            if values:
                analysis[metric_name]["avg"] = statistics.mean(values)
                analysis[metric_name]["min"] = min(values)
                analysis[metric_name]["max"] = max(values)
                analysis[metric_name]["status"] = self._get_metric_status(
                    MetricType(metric_name.replace("_", "")),
                    analysis[metric_name]["avg"]
                )

        return analysis

    def _get_metric_status(self, metric_type: MetricType, value: float) -> NetworkStatus:
        """Determine status based on metric value and thresholds."""
        if metric_type not in self.thresholds:
            return NetworkStatus.GOOD

        thresholds = self.thresholds[metric_type]

        if value <= thresholds["excellent"]:
            return NetworkStatus.EXCELLENT
        elif value <= thresholds["good"]:
            return NetworkStatus.GOOD
        elif value <= thresholds["fair"]:
            return NetworkStatus.FAIR
        elif value <= thresholds["poor"]:
            return NetworkStatus.POOR
        else:
            return NetworkStatus.CRITICAL

    def _determine_overall_status(self, performance_summary: Dict[str, Any]) -> NetworkStatus:
        """Determine overall network status."""
        statuses = []

        for metric_name in ["latency", "packet_loss", "jitter", "dns_resolution"]:
            if "status" in performance_summary.get(metric_name, {}):
                statuses.append(performance_summary[metric_name]["status"])

        if not statuses:
            return NetworkStatus.GOOD

        # Find worst status
        status_order = [
            NetworkStatus.EXCELLENT,
            NetworkStatus.GOOD,
            NetworkStatus.FAIR,
            NetworkStatus.POOR,
            NetworkStatus.CRITICAL,
            NetworkStatus.OFFLINE
        ]

        worst_status = NetworkStatus.EXCELLENT
        for status in statuses:
            if status_order.index(status) > status_order.index(worst_status):
                worst_status = status

        return worst_status

    def _generate_recommendations(self, performance_summary: Dict[str, Any],
                                  interfaces: List[NetworkInterface],
                                  connections: List[NetworkConnection]) -> List[str]:
        """Generate network optimization recommendations."""
        recommendations = []

        # Latency recommendations
        latency_status = performance_summary.get("latency", {}).get("status")
        if latency_status in [NetworkStatus.POOR, NetworkStatus.CRITICAL]:
            recommendations.append(
                "High latency detected. Consider using a closer DNS server or checking for network congestion."
            )

        # Packet loss recommendations
        packet_loss = performance_summary.get("packet_loss", {}).get("avg", 0)
        if packet_loss > 1.0:
            recommendations.append(
                f"Packet loss detected ({packet_loss:.1f}%). Check network hardware and connections."
            )

        # Jitter recommendations
        jitter_status = performance_summary.get("jitter", {}).get("status")
        if jitter_status in [NetworkStatus.POOR, NetworkStatus.CRITICAL]:
            recommendations.append(
                "High jitter detected. This may affect real-time applications like video calls."
            )

        # Connection count recommendations
        connection_count = performance_summary.get("connection_count", 0)
        if connection_count > 1000:
            recommendations.append(
                f"High number of active connections ({connection_count}). Monitor for potential security issues."
            )

        # Interface-specific recommendations
        for interface in interfaces:
            if interface.errors_in and interface.errors_in > 0:
                recommendations.append(
                    f"Network errors detected on interface {interface.name}. Check cable connections."
                )

        # DNS recommendations
        dns_avg = performance_summary.get("dns_resolution", {}).get("avg", 0)
        if dns_avg > 100:
            recommendations.append(
                "Slow DNS resolution detected. Consider using faster DNS servers (8.8.8.8, 1.1.1.1)."
            )

        # General recommendations
        if not recommendations:
            recommendations.append(
                "Network performance is good. Continue monitoring for optimal performance.")

        return recommendations

    async def start_continuous_monitoring(self, interval_seconds: int = 300) -> str:
        """Start continuous network monitoring."""
        if self.monitoring_active:
            raise ValueError("Monitoring is already active")

        monitoring_id = f"monitor_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.monitoring_active = True

        logger.info(f"Starting continuous network monitoring {monitoring_id}")

        # Start monitoring task
        asyncio.create_task(self._monitoring_loop(interval_seconds))

        return monitoring_id

    async def stop_continuous_monitoring(self):
        """Stop continuous network monitoring."""
        self.monitoring_active = False
        logger.info("Continuous network monitoring stopped")

    async def _monitoring_loop(self, interval_seconds: int):
        """Continuous monitoring loop."""
        while self.monitoring_active:
            try:
                await self._collect_performance_metrics()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    def get_metric_history(self, metric_type: MetricType, target: Optional[str] = None,
                           hours: int = 24) -> List[NetworkMetric]:
        """Get historical metrics."""
        key = f"{metric_type.value}_{target or 'global'}"

        if key not in self.metric_history:
            return []

        # Filter by time range
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [m for m in self.metric_history[key] if m.timestamp >= cutoff_time]

    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time."""
        trends = {}

        for metric_type in [MetricType.LATENCY, MetricType.PACKET_LOSS, MetricType.JITTER]:
            history = self.get_metric_history(metric_type, hours=hours)

            if len(history) >= 2:
                values = [m.value for m in history]
                recent_avg = statistics.mean(
                    values[-10:]) if len(values) >= 10 else statistics.mean(values)
                overall_avg = statistics.mean(values)

                trend_direction = "improving" if recent_avg < overall_avg else "degrading" if recent_avg > overall_avg else "stable"

                trends[metric_type.value] = {
                    "trend_direction": trend_direction,
                    "recent_average": recent_avg,
                    "overall_average": overall_avg,
                    "data_points": len(values),
                    "time_span_hours": hours
                }

        return trends


# Factory function
def create_network_monitor() -> NetworkMonitor:
    """Create a network monitor instance."""
    from ..core.interfaces import MCPServerConfig
    
    # Create a dummy config for network monitoring
    dummy_config = MCPServerConfig(
        name="network-analysis",
        command="echo",
        args=["dummy"],
        env={}
    )
    
    mcp_client = MCPClient(dummy_config)
    return NetworkMonitor(mcp_client)
