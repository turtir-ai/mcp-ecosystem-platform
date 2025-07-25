"""
Workflow management service for creating, storing, and validating workflows.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.workflow import (
    WorkflowDefinition, WorkflowModel, WorkflowExecutionModel,
    WorkflowStatus, WorkflowValidator
)
from ..core.interfaces import MCPServerConfig
from .mcp_client import MCPClient


class WorkflowService:
    """Service for managing workflows."""

    def __init__(self, db: Session, mcp_client: MCPClient):
        self.db = db
        self.mcp_client = mcp_client

    async def create_workflow(self, workflow_def: WorkflowDefinition, user_id: str) -> WorkflowModel:
        """Create a new workflow."""
        # Generate ID if not provided
        if not workflow_def.id:
            workflow_def.id = str(uuid.uuid4())

        # Set metadata
        workflow_def.created_by = user_id
        workflow_def.created_at = datetime.utcnow()

        # Validate workflow
        is_valid, errors = await self._validate_workflow_with_mcp(workflow_def)
        workflow_def.is_valid = is_valid
        workflow_def.validation_errors = errors

        # Create database record
        db_workflow = WorkflowModel(
            name=workflow_def.name,
            description=workflow_def.description,
            version=workflow_def.version,
            definition=workflow_def.dict(),
            status=WorkflowStatus.DRAFT if not is_valid else WorkflowStatus.ACTIVE,
            created_by=user_id,
            is_valid=is_valid,
            validation_errors=errors
        )

        self.db.add(db_workflow)
        self.db.commit()
        self.db.refresh(db_workflow)

        return db_workflow

    async def validate_workflow(self, workflow_def: WorkflowDefinition) -> tuple[bool, List[str]]:
        """Validate a workflow definition."""
        return await self._validate_workflow_with_mcp(workflow_def)

    async def _validate_workflow_with_mcp(self, workflow_def: WorkflowDefinition) -> tuple[bool, List[str]]:
        """Comprehensive workflow validation including MCP server compatibility."""
        # Basic validation
        is_valid, errors = workflow_def.validate_workflow()

        if not is_valid:
            return False, errors

        try:
            # Get available MCP servers
            available_servers = await self.mcp_client.get_available_servers()
            server_names = [server.name for server in available_servers]

            # Validate MCP server compatibility
            mcp_errors = WorkflowValidator.validate_mcp_server_compatibility(
                workflow_def, server_names)
            errors.extend(mcp_errors)

        except Exception as e:
            errors.append(f"MCP validation failed: {str(e)}")

        return len(errors) == 0, errors

    def get_workflow(self, workflow_id: int) -> Optional[WorkflowModel]:
        """Get a workflow by ID."""
        return self.db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()

    def get_workflows(self, user_id: Optional[str] = None, status: Optional[WorkflowStatus] = None,
                      limit: int = 100, offset: int = 0) -> List[WorkflowModel]:
        """Get workflows with optional filtering."""
        # Mock implementation - return empty list for now
        return []

        if user_id:
            query = query.filter(WorkflowModel.created_by == user_id)

        if status:
            query = query.filter(WorkflowModel.status == status)

        return query.offset(offset).limit(limit).all()

    def get_workflow_definition(self, workflow_id: int) -> Optional[WorkflowDefinition]:
        """Get workflow definition as Pydantic model."""
        db_workflow = self.get_workflow(workflow_id)
        if not db_workflow:
            return None

        return WorkflowDefinition(**db_workflow.definition)


class WorkflowTemplateService:
    """Service for managing workflow templates."""

    def __init__(self):
        self.templates = self._load_default_templates()

    def _load_default_templates(self) -> Dict[str, WorkflowDefinition]:
        """Load default workflow templates."""
        templates = {}

        # Smart Git Review Template
        git_review_template = WorkflowDefinition(
            name="Smart Git Review",
            description="Automated code review using AI analysis",
            steps=[
                {
                    "id": "git_diff",
                    "name": "Extract Git Changes",
                    "type": "mcp_call",
                    "mcp_server": "enhanced-git",
                    "tool_name": "git_diff",
                    "parameters": {"staged": False},
                    "description": "Get uncommitted changes from repository"
                },
                {
                    "id": "code_analysis",
                    "name": "AI Code Analysis",
                    "type": "mcp_call",
                    "mcp_server": "groq-llm",
                    "tool_name": "groq_generate",
                    "parameters": {
                        "prompt": "Analyze this code diff for quality, security, and best practices",
                        "model": "llama-3.1-70b-versatile"
                    },
                    "depends_on": ["git_diff"],
                    "description": "Analyze code changes with AI"
                }
            ],
            tags=["git", "code-review", "ai", "security"]
        )
        templates["smart_git_review"] = git_review_template

        return templates

    def get_template(self, template_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow template by ID."""
        return self.templates.get(template_id)

    def list_templates(self) -> List[Dict[str, Any]]:
        """List available workflow templates."""
        return [
            {
                "id": template_id,
                "name": template.name,
                "description": template.description,
                "tags": template.tags,
                "step_count": len(template.steps)
            }
            for template_id, template in self.templates.items()
        ]
