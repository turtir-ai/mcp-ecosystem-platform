"""
Workflow models for MCP Ecosystem Platform
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Workflow step types"""
    MCP_TOOL = "mcp_tool"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"


class WorkflowStepDefinition(BaseModel):
    """Definition of a workflow step"""
    id: str
    name: str
    type: StepType
    mcp_server: Optional[str] = None
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = {}
    depends_on: List[str] = []
    timeout: int = 60
    retry_count: int = 1
    condition: Optional[str] = None


class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    id: Optional[str] = None
    name: str
    description: str
    steps: List[WorkflowStepDefinition]
    timeout: int = 300
    parallel_execution: bool = False
    on_failure: str = "stop"  # stop, continue, retry


class WorkflowModel(BaseModel):
    """Workflow model for database storage"""
    id: str
    name: str
    description: str
    definition: WorkflowDefinition
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class WorkflowExecutionModel(BaseModel):
    """Workflow execution model"""
    id: str
    workflow_id: str
    status: WorkflowStatus
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] = {}
    current_step: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_log: List[Dict[str, Any]] = []


class WorkflowValidator:
    """Workflow validation utilities"""

    @staticmethod
    def validate_definition(definition: WorkflowDefinition) -> List[str]:
        """Validate workflow definition and return list of errors"""
        errors = []

        if not definition.name:
            errors.append("Workflow name is required")

        if not definition.steps:
            errors.append("Workflow must have at least one step")

        # Check for circular dependencies
        step_ids = {step.id for step in definition.steps}
        for step in definition.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(
                        f"Step {step.id} depends on non-existent step {dep}")

        return errors

    @staticmethod
    def validate_execution_inputs(definition: WorkflowDefinition, inputs: Dict[str, Any]) -> List[str]:
        """Validate execution inputs"""
        errors = []

        # Basic validation - in real implementation this would be more sophisticated
        if not isinstance(inputs, dict):
            errors.append("Inputs must be a dictionary")

        return errors
