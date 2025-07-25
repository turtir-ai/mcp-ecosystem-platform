"""
Workflow API routes for creating and managing workflows.
"""
from ..services.workflow_engine import create_workflow_engine, WorkflowEngine
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.workflow import WorkflowDefinition, WorkflowModel, WorkflowStatus
from ..services.workflow_service import WorkflowService, WorkflowTemplateService
from ..services.mcp_client import MCPClient
from ..core.auth import get_current_user


router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_service(db: Session = Depends(get_db)) -> WorkflowService:
    """Get workflow service instance."""
    from ..core.interfaces import MCPServerConfig
    
    # Create a dummy config for workflow service
    dummy_config = MCPServerConfig(
        name="workflow-service",
        command="echo",
        args=["dummy"],
        env={}
    )
    
    mcp_client = MCPClient(dummy_config)
    return WorkflowService(db, mcp_client)


def get_template_service() -> WorkflowTemplateService:
    """Get workflow template service instance."""
    return WorkflowTemplateService()


@router.post("/", response_model=dict)
async def create_workflow(
    workflow_def: WorkflowDefinition,
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """Create a new workflow."""
    try:
        db_workflow = await workflow_service.create_workflow(workflow_def, current_user.id)
        return {
            "id": db_workflow.id,
            "name": db_workflow.name,
            "status": db_workflow.status,
            "is_valid": db_workflow.is_valid,
            "validation_errors": db_workflow.validation_errors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/", response_model=List[dict])
def get_workflows(
    status_filter: Optional[WorkflowStatus] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """Get user's workflows with optional filtering."""
    workflows = workflow_service.get_workflows(
        user_id=current_user.id,
        status=status_filter,
        limit=limit,
        offset=offset
    )

    return [
        {
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "status": wf.status,
            "is_valid": wf.is_valid,
            "created_at": wf.created_at,
            "updated_at": wf.updated_at
        }
        for wf in workflows
    ]


@router.get("/{workflow_id}", response_model=dict)
def get_workflow(
    workflow_id: int,
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """Get a specific workflow."""
    workflow = workflow_service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # Check ownership
    if workflow.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "version": workflow.version,
        "definition": workflow.definition,
        "status": workflow.status,
        "is_valid": workflow.is_valid,
        "validation_errors": workflow.validation_errors,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at
    }


@router.post("/validate", response_model=dict)
async def validate_workflow(
    workflow_def: WorkflowDefinition,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """Validate a workflow definition without saving it."""
    try:
        is_valid, errors = await workflow_service.validate_workflow(workflow_def)
        return {
            "is_valid": is_valid,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/templates/", response_model=List[dict])
def get_workflow_templates(
    template_service: WorkflowTemplateService = Depends(get_template_service)
):
    """Get available workflow templates."""
    return template_service.list_templates()


@router.get("/templates/{template_id}", response_model=WorkflowDefinition)
def get_workflow_template(
    template_id: str,
    template_service: WorkflowTemplateService = Depends(get_template_service)
):
    """Get a specific workflow template."""
    template = template_service.get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template


@router.post("/from-template/{template_id}", response_model=dict)
async def create_workflow_from_template(
    template_id: str,
    name: str,
    parameters: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    template_service: WorkflowTemplateService = Depends(get_template_service)
):
    """Create a workflow from a template."""
    try:
        # Create workflow from template
        workflow_def = template_service.create_workflow_from_template(
            template_id, name, parameters or {}
        )

        if not workflow_def:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Save the workflow
        db_workflow = await workflow_service.create_workflow(workflow_def, current_user.id)

        return {
            "id": db_workflow.id,
            "name": db_workflow.name,
            "status": db_workflow.status,
            "is_valid": db_workflow.is_valid,
            "validation_errors": db_workflow.validation_errors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create workflow from template: {str(e)}"
        )


def get_workflow_engine() -> WorkflowEngine:
    """Get workflow engine instance."""
    return create_workflow_engine()


@router.post("/{workflow_id}/execute", response_model=dict)
async def execute_workflow(
    workflow_id: int,
    inputs: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Execute a workflow."""
    try:
        # Get workflow definition
        workflow_def = workflow_service.get_workflow_definition(workflow_id)
        if not workflow_def:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )

        # Check if workflow is valid
        if not workflow_def.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot execute invalid workflow"
            )

        # Start execution
        execution = await workflow_engine.execute_workflow(
            workflow=workflow_def,
            inputs=inputs or {}
        )

        return {
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "started_at": execution.started_at
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.get("/executions/{execution_id}/status", response_model=dict)
async def get_execution_status(
    execution_id: str,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get status of a workflow execution."""
    status_info = await workflow_engine.get_execution_status(execution_id)

    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return status_info


@router.post("/executions/{execution_id}/cancel", response_model=dict)
async def cancel_execution(
    execution_id: str,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Cancel a running workflow execution."""
    success = await workflow_engine.cancel_execution(execution_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return {"message": "Execution cancelled successfully"}
