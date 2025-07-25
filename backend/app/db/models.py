"""
SQLAlchemy models for MCP Ecosystem Platform
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, JSON, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime
import uuid

from .base import Base


class WorkflowStatus(str, enum.Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ServerStatus(str, enum.Enum):
    """MCP server status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    workflows = relationship("Workflow", back_populates="owner")
    workflow_executions = relationship(
        "WorkflowExecution", back_populates="user")
    usage_events = relationship("UsageEvent", back_populates="user")


class MCPServer(Base):
    """MCP Server configuration model"""
    __tablename__ = "mcp_servers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    command = Column(String(255), nullable=False)
    args = Column(JSON, default=list)
    env = Column(JSON, default=dict)
    timeout = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    health_check_interval = Column(Integer, default=60)
    auto_restart = Column(Boolean, default=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    health_checks = relationship("HealthCheck", back_populates="server")
    workflow_steps = relationship("WorkflowStep", back_populates="mcp_server")


class Workflow(Base):
    """Workflow definition model"""
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    definition = Column(JSON, nullable=False)
    timeout = Column(Integer, default=300)
    parallel_execution = Column(Boolean, default=False)
    on_failure = Column(String(50), default="stop")
    is_active = Column(Boolean, default=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="workflows")
    steps = relationship(
        "WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow")

    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'owner_id', name='uq_workflow_name_owner'),
    )


class WorkflowStep(Base):
    """Workflow step model"""
    __tablename__ = "workflow_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    name = Column(String(255), nullable=False)
    step_order = Column(Integer, nullable=False)
    mcp_server_id = Column(String, ForeignKey(
        "mcp_servers.id"), nullable=False)
    tool_name = Column(String(255), nullable=False)
    arguments = Column(JSON, default=dict)
    depends_on = Column(JSON, default=list)  # List of step names
    timeout = Column(Integer, default=60)
    retry_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    mcp_server = relationship("MCPServer", back_populates="workflow_steps")

    # Constraints
    __table_args__ = (
        UniqueConstraint('workflow_id', 'step_order',
                         name='uq_workflow_step_order'),
        UniqueConstraint('workflow_id', 'name', name='uq_workflow_step_name'),
    )


class WorkflowExecution(Base):
    """Workflow execution model"""
    __tablename__ = "workflow_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    inputs = Column(JSON, default=dict)
    outputs = Column(JSON, default=dict)
    current_step = Column(String(255))
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    execution_time_ms = Column(Float)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    user = relationship("User", back_populates="workflow_executions")
    step_executions = relationship(
        "StepExecution", back_populates="workflow_execution", cascade="all, delete-orphan")


class StepExecution(Base):
    """Individual step execution model"""
    __tablename__ = "step_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_execution_id = Column(String, ForeignKey(
        "workflow_executions.id"), nullable=False)
    step_name = Column(String(255), nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    inputs = Column(JSON, default=dict)
    outputs = Column(JSON, default=dict)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    execution_time_ms = Column(Float)
    retry_count = Column(Integer, default=0)

    # Relationships
    workflow_execution = relationship(
        "WorkflowExecution", back_populates="step_executions")


class HealthCheck(Base):
    """Health check results model"""
    __tablename__ = "health_checks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    server_id = Column(String, ForeignKey("mcp_servers.id"), nullable=False)
    status = Column(SQLEnum(ServerStatus), nullable=False)
    response_time_ms = Column(Float)
    error_message = Column(Text)
    uptime_percentage = Column(Float)
    version = Column(String(100))
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    server = relationship("MCPServer", back_populates="health_checks")

    # Index for performance
    __table_args__ = (
        {"extend_existing": True}
    )


class UsageEvent(Base):
    """Usage analytics events model"""
    __tablename__ = "usage_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, default=dict)
    session_id = Column(String(255))
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="usage_events")

    # Index for performance
    __table_args__ = (
        {"extend_existing": True}
    )


class APIKey(Base):
    """API keys for external services"""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    service = Column(String(100), nullable=False)  # groq, openrouter, etc.
    key_hash = Column(String(255), nullable=False)  # Hashed key for security
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)

    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'service', name='uq_api_key_name_service'),
    )


class ReviewResult(Base):
    """Code review results model"""
    __tablename__ = "review_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_path = Column(String(500), nullable=False)
    branch = Column(String(255), default="HEAD")
    commit_hash = Column(String(40))
    files_analyzed = Column(Integer, default=0)
    issues_found = Column(Integer, default=0)
    security_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    recommendations = Column(JSON, default=list)
    findings = Column(JSON, default=list)
    execution_time_ms = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    findings_detail = relationship(
        "ReviewFinding", back_populates="review", cascade="all, delete-orphan")


class ReviewFinding(Base):
    """Individual code review findings"""
    __tablename__ = "review_findings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id = Column(String, ForeignKey("review_results.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    line_number = Column(Integer, nullable=False)
    # low, medium, high, critical
    severity = Column(String(20), nullable=False)
    # security, quality, style, performance
    category = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    suggestion = Column(Text)
    confidence = Column(Float, default=1.0)
    rule_id = Column(String(100))

    # Relationships
    review = relationship("ReviewResult", back_populates="findings_detail")


class ResearchResult(Base):
    """Web research results model"""
    __tablename__ = "research_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(String(500), nullable=False)
    depth = Column(Integer, default=3)
    sources_count = Column(Integer, default=0)
    summary = Column(Text)
    insights = Column(JSON, default=list)
    sources = Column(JSON, default=list)
    execution_time_ms = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemMetrics(Base):
    """System performance metrics"""
    __tablename__ = "system_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # cpu, memory, disk, network
    metric_type = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))  # percent, bytes, ms, etc.
    labels = Column(JSON, default=dict)  # Additional metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Index for time-series queries
    __table_args__ = (
        {"extend_existing": True}
    )
