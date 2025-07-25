"""
Git Analyzer Service

This service provides Git repository analysis functionality.
"""

import logging
from typing import Dict, Any, List
import os
import subprocess

logger = logging.getLogger(__name__)


class GitAnalyzer:
    """Git analyzer implementation"""

    def __init__(self):
        pass

    async def get_repositories(self) -> List[Dict[str, Any]]:
        """Get available Git repositories"""
        repositories = []
        
        # Mock repository data
        repositories.append({
            "id": "mcp-ecosystem-platform",
            "name": "MCP Ecosystem Platform",
            "path": os.getcwd(),
            "branch": "main",
            "status": "clean"
        })
        
        return repositories

    async def get_git_status(self) -> Dict[str, Any]:
        """Get Git status for current repository"""
        try:
            # Run git status command
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                return {"error": "Not a git repository or git not available"}
            
            # Parse git status output
            status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            modified_files = []
            staged_files = []
            untracked_files = []
            
            for line in status_lines:
                if len(line) >= 3:
                    status_code = line[:2]
                    filename = line[3:]
                    
                    if status_code[0] in ['M', 'A', 'D', 'R', 'C']:
                        staged_files.append(filename)
                    if status_code[1] in ['M', 'D']:
                        modified_files.append(filename)
                    if status_code == '??':
                        untracked_files.append(filename)
            
            return {
                "modified_files": modified_files,
                "staged_files": staged_files,
                "untracked_files": untracked_files,
                "is_clean": len(status_lines) == 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get git status: {e}")
            return {"error": str(e)}

    async def get_git_diff(self, staged: bool = False) -> Dict[str, Any]:
        """Get Git diff"""
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                return {"error": "Failed to get git diff"}
            
            return {
                "diff": result.stdout,
                "staged": staged
            }
            
        except Exception as e:
            logger.error(f"Failed to get git diff: {e}")
            return {"error": str(e)}