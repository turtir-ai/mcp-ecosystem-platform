"""
Core interfaces for MCP Ecosystem Platform

This module defines the fundamental interfaces and abstract base classes
that establish the contracts between different components of the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MCPServerStatus(str, Enum):
    """Status enumeration for MCP servers"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"


class HealthStatus(BaseModel):
    """Health status information for MCP servers"""
    status: MCPServerStatus
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None
    uptime_percentage: float
    version: Optional[str] = None


class ToolDefinition(BaseModel):
    """Definition of an MCP tool"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required_parameters: List[str] = []
    examples: List[Dict[str, Any]] = []


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] = {}
    port: Optional[int] = None
    timeout: int = 30
    retry_count: int = 3
    health_check_interval: int = 60
    auto_restart: bool = True


class WorkflowStep(BaseModel):
    """Single step in a workflow"""
    name: str
    mcp_server: str
    tool_name: str
    arguments: Dict[str, Any]
    depends_on: List[str] = []
    timeout: int = 60
    retry_count: int = 1


class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    name: str
    description: str
    steps: List[WorkflowStep]
    timeout: int = 300
    parallel_execution: bool = False
    on_failure: str = "stop"  # stop, continue, retry


class WorkflowExecution(BaseModel):
    """Runtime workflow execution state"""
    id: str
    workflow_id: str
    status: str  # pending, running, completed, failed, cancelled
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] = {}
    current_step: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ReviewFinding(BaseModel):
    """Code review finding"""
    file_path: str
    line_number: int
    severity: str  # low, medium, high, critical
    category: str  # security, quality, style, performance
    message: str
    suggestion: Optional[str] = None
    confidence: float = 1.0


class ReviewResult(BaseModel):
    """Complete code review result"""
    repository_path: str
    timestamp: datetime
    files_analyzed: int
    issues_found: int
    security_score: float  # 0-10
    quality_score: float   # 0-10
    overall_score: float   # 0-10
    recommendations: List[str]
    findings: List[ReviewFinding]
    execution_time_ms: float


# Abstract Interfaces

class IMCPClient(ABC):
    """Interface for MCP server communication"""

    @abstractmethod
    async def initialize(self, config: MCPServerConfig) -> bool:
        """Initialize connection to MCP server"""
        pass

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the MCP server"""
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Check server health and response time"""
        pass

    @abstractmethod
    async def list_tools(self) -> List[ToolDefinition]:
        """Get available tools from server"""
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """Gracefully shutdown the MCP server connection"""
        pass


class IWorkflowEngine(ABC):
    """Interface for workflow orchestration"""

    @abstractmethod
    async def create_workflow(self, definition: WorkflowDefinition) -> str:
        """Create a new workflow from definition"""
        pass

    @abstractmethod
    async def execute_workflow(self, workflow_id: str, inputs: Dict[str, Any]) -> str:
        """Execute a workflow with given inputs, returns execution_id"""
        pass

    @abstractmethod
    async def get_execution_status(self, execution_id: str) -> WorkflowExecution:
        """Get current status of workflow execution"""
        pass

    @abstractmethod
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        pass

    @abstractmethod
    async def list_workflows(self) -> List[WorkflowDefinition]:
        """List all available workflows"""
        pass


class IHealthMonitor(ABC):
    """Interface for MCP server health monitoring"""

    @abstractmethod
    async def start_monitoring(self) -> None:
        """Start the health monitoring service"""
        pass

    @abstractmethod
    async def stop_monitoring(self) -> None:
        """Stop the health monitoring service"""
        pass

    @abstractmethod
    async def get_server_status(self, server_name: str) -> HealthStatus:
        """Get current health status of a specific server"""
        pass

    @abstractmethod
    async def get_all_statuses(self) -> Dict[str, HealthStatus]:
        """Get health status of all monitored servers"""
        pass

    @abstractmethod
    async def register_server(self, config: MCPServerConfig) -> bool:
        """Register a new server for monitoring"""
        pass


class IGitReviewer(ABC):
    """Interface for AI-powered Git code review"""

    @abstractmethod
    async def analyze_repository(self, repo_path: str, branch: str = "HEAD") -> ReviewResult:
        """Analyze Git repository for code quality and security"""
        pass

    @abstractmethod
    async def analyze_diff(self, diff_content: str) -> ReviewResult:
        """Analyze specific diff content"""
        pass

    @abstractmethod
    async def analyze_pull_request(self, repo_path: str, pr_number: int) -> ReviewResult:
        """Analyze a specific pull request"""
        pass


class IResearchService(ABC):
    """Interface for web research and competitive analysis"""

    @abstractmethod
    async def conduct_research(self, query: str, depth: int = 3) -> Dict[str, Any]:
        """Conduct comprehensive web research on a topic"""
        pass

    @abstractmethod
    async def analyze_competitor(self, competitor_url: str) -> Dict[str, Any]:
        """Analyze competitor website and extract insights"""
        pass

    @abstractmethod
    async def monitor_trends(self, keywords: List[str]) -> Dict[str, Any]:
        """Monitor trends and changes for given keywords"""
        pass


class ISecurityScanner(ABC):
    """Interface for security scanning and monitoring"""

    @abstractmethod
    async def scan_code(self, code_content: str) -> List[ReviewFinding]:
        """Scan code for security vulnerabilities"""
        pass

    @abstractmethod
    async def scan_network_traffic(self, traffic_data: bytes) -> List[Dict[str, Any]]:
        """Scan network traffic for security threats"""
        pass

    @abstractmethod
    async def detect_secrets(self, content: str) -> List[Dict[str, Any]]:
        """Detect API keys, passwords, and other secrets"""
        pass


class IAnalyticsService(ABC):
    """Interface for usage analytics and reporting"""

    @abstractmethod
    async def track_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Track a user interaction event"""
        pass

    @abstractmethod
    async def generate_usage_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate usage analytics report"""
        pass

    @abstractmethod
    async def calculate_roi_metrics(self, user_id: str) -> Dict[str, Any]:
        """Calculate ROI metrics for a user"""
        pass


# Exception Classes

class MCPError(Exception):
    """Base exception for MCP-related errors"""

    def __init__(self, message: str, server_name: str = None, error_code: str = None):
        self.message = message
        self.server_name = server_name
        self.error_code = error_code
        super().__init__(self.message)


class MCPConnectionError(MCPError):
    """Exception for MCP server connection issues"""
    pass


class MCPTimeoutError(MCPError):
    """Exception for MCP server timeout issues"""
    pass


class WorkflowError(Exception):
    """Base exception for workflow-related errors"""

    def __init__(self, message: str, workflow_id: str = None, step_name: str = None):
        self.message = message
        self.workflow_id = workflow_id
        self.step_name = step_name
        super().__init__(self.message)


class WorkflowExecutionError(WorkflowError):
    """Exception for workflow execution failures"""
    pass


class WorkflowValidationError(WorkflowError):
    """Exception for workflow validation failures"""
    pass


# Utility Types

class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PaginatedResponse(BaseModel):
    """Paginated API response format"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
