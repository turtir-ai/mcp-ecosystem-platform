"""
Workflow execution engine for orchestrating multi-step workflows across MCP servers.
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import logging

from ..models.workflow import (
    WorkflowDefinition, WorkflowModel, WorkflowExecutionModel,
    WorkflowStatus, StepType, WorkflowStepDefinition
)
from .mcp_client import MCPClient, get_mcp_client_manager
from ..core.interfaces import MCPServerConfig
from ..core.error_handling import get_error_handler, WorkflowError, MCPError

logger = logging.getLogger(__name__)


class ExecutionContext:
    """Context for workflow execution containing step results and variables."""

    def __init__(self):
        self.step_results: Dict[str, Any] = {}
        self.variables: Dict[str, Any] = {}
        self.execution_start_time = datetime.utcnow()
        self.current_step: Optional[str] = None


class WorkflowEngine:
    """Main workflow execution engine"""

    def __init__(self):
        self.executions: Dict[str, WorkflowExecutionModel] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.client_manager = get_mcp_client_manager()
        self.error_handler = get_error_handler()

    async def create_workflow(self, definition: WorkflowDefinition) -> str:
        """Create a new workflow from definition"""
        workflow_id = str(uuid.uuid4())
        definition.id = workflow_id
        self.workflows[workflow_id] = definition
        logger.info(f"Created workflow: {workflow_id}")
        return workflow_id

    async def execute_workflow(self, workflow_id: str, inputs: Dict[str, Any]) -> str:
        """Execute a workflow with given inputs, returns execution_id"""
        if workflow_id not in self.workflows:
            raise WorkflowError(f"Workflow not found: {workflow_id}")

        execution_id = str(uuid.uuid4())
        workflow = self.workflows[workflow_id]

        execution = WorkflowExecutionModel(
            id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            inputs=inputs,
            started_at=datetime.utcnow()
        )

        self.executions[execution_id] = execution

        # Start execution in background
        asyncio.create_task(self._execute_workflow_async(execution_id))

        return execution_id

    async def get_execution_status(self, execution_id: str) -> WorkflowExecutionModel:
        """Get current status of workflow execution"""
        if execution_id not in self.executions:
            raise WorkflowError(f"Execution not found: {execution_id}")
        return self.executions[execution_id]

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        if execution_id not in self.executions:
            return False

        execution = self.executions[execution_id]
        if execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            logger.info(f"Cancelled execution: {execution_id}")
            return True
        return False

    async def list_workflows(self) -> List[WorkflowDefinition]:
        """List all available workflows"""
        return list(self.workflows.values())

    async def _execute_workflow_async(self, execution_id: str):
        """Execute workflow asynchronously"""
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]

        try:
            execution.status = WorkflowStatus.RUNNING
            context = ExecutionContext()
            context.variables.update(execution.inputs)

            # Execute steps
            for step in workflow.steps:
                if execution.status == WorkflowStatus.CANCELLED:
                    break

                execution.current_step = step.id
                await self._execute_step(step, context, execution_id)

            # Mark as completed
            execution.status = WorkflowStatus.COMPLETED
            execution.outputs = context.step_results
            execution.completed_at = datetime.utcnow()

            logger.info(f"Workflow execution completed: {execution_id}")

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()

            self.error_handler.handle_workflow_error(
                error=WorkflowError(str(e)),
                workflow_id=execution.workflow_id,
                execution_id=execution_id
            )

            logger.error(f"Workflow execution failed: {execution_id} - {e}")

    async def _execute_step(self, step: WorkflowStepDefinition, context: ExecutionContext, execution_id: str):
        """Execute a single workflow step"""
        logger.info(f"Executing step: {step.id}")

        try:
            if step.type == StepType.MCP_TOOL:
                await self._execute_mcp_tool_step(step, context)
            elif step.type == StepType.CONDITION:
                await self._execute_condition_step(step, context)
            else:
                logger.warning(f"Unsupported step type: {step.type}")

            # Store step result
            context.step_results[step.id] = {
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Step {step.id} failed: {e}")
            raise WorkflowError(
                f"Step {step.id} failed: {str(e)}", step_id=step.id)

    async def _execute_mcp_tool_step(self, step: WorkflowStepDefinition, context: ExecutionContext):
        """Execute an MCP tool step"""
        if not step.mcp_server or not step.tool_name:
            raise WorkflowError(
                "MCP tool step requires server and tool name", step_id=step.id)

        client = await self.client_manager.get_client(step.mcp_server)
        if not client:
            raise WorkflowError(
                f"MCP client not found: {step.mcp_server}", step_id=step.id)

        # Execute tool with timeout
        try:
            result = await asyncio.wait_for(
                client.call_tool(step.tool_name, step.arguments),
                timeout=step.timeout
            )
            context.step_results[step.id] = result

        except asyncio.TimeoutError:
            raise WorkflowError(
                f"Step {step.id} timed out after {step.timeout}s", step_id=step.id)

    async def _execute_condition_step(self, step: WorkflowStepDefinition, context: ExecutionContext):
        """Execute a condition step"""
        # Simple condition evaluation - in real implementation this would be more sophisticated
        if step.condition:
            # Mock condition evaluation
            result = True  # Always true for now
            context.step_results[step.id] = {"condition_result": result}


# Singleton instance
_workflow_engine = None


def create_workflow_engine() -> WorkflowEngine:
    """Create workflow engine singleton"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine


def get_workflow_engine() -> WorkflowEngine:
    """Get workflow engine singleton"""
    return create_workflow_engine()
