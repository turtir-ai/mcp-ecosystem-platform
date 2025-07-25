"""
Error handling utilities for MCP Ecosystem Platform
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    """Workflow execution error"""

    def __init__(self, message: str, step_id: str = None, context: Dict[str, Any] = None):
        self.message = message
        self.step_id = step_id
        self.context = context or {}
        super().__init__(self.message)


class MCPError(Exception):
    """MCP server error"""

    def __init__(self, message: str, server_name: str = None, error_code: str = None):
        self.message = message
        self.server_name = server_name
        self.error_code = error_code
        super().__init__(self.message)


class ErrorHandler:
    """Central error handler"""

    def __init__(self):
        self.error_count = 0

    def handle_workflow_error(self, error: WorkflowError, workflow_id: str,
                              execution_id: str, step_id: str = None):
        """Handle workflow errors"""
        self.error_count += 1
        logger.error(
            f"Workflow error in {workflow_id}/{execution_id}: {error.message}")

        if step_id:
            logger.error(f"Failed step: {step_id}")

        if error.context:
            logger.error(f"Error context: {error.context}")

    def handle_mcp_error(self, error: MCPError, server_name: str = None):
        """Handle MCP server errors"""
        self.error_count += 1
        logger.error(
            f"MCP error on {server_name or 'unknown'}: {error.message}")

        if error.error_code:
            logger.error(f"Error code: {error.error_code}")


# Singleton instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get error handler singleton"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
