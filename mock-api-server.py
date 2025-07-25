#!/usr/bin/env python3
"""
Mock API Server for MCP Ecosystem Platform Extension Testing
Bu server extension'ı test etmek için basit mock responses döner
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime
import random

app = FastAPI(
    title="MCP Ecosystem Platform - Mock API",
    description="Mock API server for testing MCP Platform Extension",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
MOCK_SERVERS = [
    {
        "name": "kiro-tools",
        "status": "healthy",
        "response_time_ms": 45,
        "last_check": datetime.now().isoformat(),
        "uptime_percentage": 99.5,
        "error_message": None
    },
    {
        "name": "groq-llm",
        "status": "healthy",
        "response_time_ms": 120,
        "last_check": datetime.now().isoformat(),
        "uptime_percentage": 98.2,
        "error_message": None
    },
    {
        "name": "browser-automation",
        "status": "healthy",
        "response_time_ms": 180,
        "last_check": datetime.now().isoformat(),
        "uptime_percentage": 97.8,
        "error_message": None
    },
    {
        "name": "api-key-sniffer",
        "status": "healthy",
        "response_time_ms": 80,
        "last_check": datetime.now().isoformat(),
        "uptime_percentage": 99.1,
        "error_message": None
    },
    {
        "name": "network-analysis",
        "status": "healthy",
        "response_time_ms": 85,
        "last_check": datetime.now().isoformat(),
        "uptime_percentage": 98.4,
        "error_message": None
    },
    {
        "name": "context7",
        "status": "healthy",
        "response_time_ms": 95,
        "last_check": datetime.now().isoformat(),
        "uptime_percentage": 98.7,
        "error_message": None
    },
    {
        "name": "huggingface",
        "status": "healthy",
        "response_time_ms": 120,
        "last_check": datetime.now().isoformat(),
        "uptime_percentage": 97.8,
        "error_message": None
    }
]

MOCK_TOOLS = {
    "kiro-tools": [
        {"name": "readFile", "description": "Read file contents"},
        {"name": "writeFile", "description": "Write file contents"},
        {"name": "listDirectory", "description": "List directory contents"}
    ],
    "groq-llm": [
        {"name": "groq_generate", "description": "Generate text using Groq"},
        {"name": "groq_chat", "description": "Chat with Groq models"}
    ],
    "browser-automation": [
        {"name": "launch_browser", "description": "Launch browser"},
        {"name": "navigate_to", "description": "Navigate to URL"},
        {"name": "take_screenshot", "description": "Take screenshot"}
    ],
    "context7": [
        {"name": "resolve-library-id",
            "description": "Resolve library ID for documentation"},
        {"name": "get-library-docs",
            "description": "Fetch up-to-date documentation"},
        {"name": "search-libraries", "description": "Search for libraries and packages"},
        {"name": "get-code-examples",
            "description": "Get code examples from documentation"},
        {"name": "get-api-reference", "description": "Get API reference documentation"}
    ],
    "huggingface": [
        {"name": "search_models", "description": "Search for AI models on Hugging Face"},
        {"name": "get_model_info", "description": "Get detailed model information"},
        {"name": "search_datasets", "description": "Search for datasets"},
        {"name": "get_dataset_info", "description": "Get detailed dataset information"},
        {"name": "inference_api", "description": "Run model inference"},
        {"name": "download_model", "description": "Download model for local use"}
    ]
}

MOCK_WORKFLOWS = [
    {
        "id": "wf-001",
        "name": "Code Review & Security Scan",
        "description": "AI-powered code review with security analysis",
        "status": "active",
        "is_valid": True,
        "created_at": "2024-01-20T10:00:00Z",
        "updated_at": "2024-01-20T10:00:00Z"
    },
    {
        "id": "wf-002",
        "name": "Market Research Analysis",
        "description": "Comprehensive market research using web scraping",
        "status": "active",
        "is_valid": True,
        "created_at": "2024-01-19T15:30:00Z",
        "updated_at": "2024-01-19T15:30:00Z"
    }
]


class APIResponse(BaseModel):
    success: bool
    data: Any
    message: Optional[str] = None

# Health check


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/status")
async def status_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# MCP Status endpoints


@app.get("/mcp/status")
async def get_mcp_status():
    # Randomly update some values for realism
    for server in MOCK_SERVERS:
        server["response_time_ms"] += random.randint(-10, 10)
        server["last_check"] = datetime.now().isoformat()

    return APIResponse(success=True, data=MOCK_SERVERS)


@app.get("/mcp/status/{server_name}")
async def get_server_status(server_name: str):
    server = next((s for s in MOCK_SERVERS if s["name"] == server_name), None)
    if not server:
        raise HTTPException(
            status_code=404, detail=f"Server {server_name} not found")

    return APIResponse(success=True, data=server)


@app.get("/mcp/tools/{server_name}")
async def get_server_tools(server_name: str):
    tools = MOCK_TOOLS.get(server_name, [])
    return APIResponse(success=True, data=tools)


@app.post("/mcp/restart/{server_name}")
async def restart_server(server_name: str):
    server = next((s for s in MOCK_SERVERS if s["name"] == server_name), None)
    if not server:
        raise HTTPException(
            status_code=404, detail=f"Server {server_name} not found")

    # Simulate restart
    server["status"] = "healthy"
    server["response_time_ms"] = random.randint(50, 150)
    server["last_check"] = datetime.now().isoformat()
    server["error_message"] = None

    return APIResponse(success=True, data={"message": f"Server {server_name} restarted successfully"})

# Git Review endpoints


@app.post("/git/review")
async def start_git_review(request: Dict[str, Any]):
    review_id = f"review-{random.randint(1000, 9999)}"
    return APIResponse(success=True, data={"reviewId": review_id})


@app.get("/git/review/{review_id}/results")
async def get_review_results(review_id: str):
    mock_result = {
        "id": review_id,
        "status": "completed",
        "securityScore": random.randint(7, 10),
        "qualityScore": random.randint(8, 10),
        "findings": [
            {
                "file": "src/main.py",
                "line": 42,
                "column": 10,
                "severity": "warning",
                "category": "code-quality",
                "message": "Consider using more descriptive variable names",
                "suggestion": "Use 'user_data' instead of 'data'"
            }
        ],
        "summary": "Code review completed successfully with minor suggestions",
        "recommendations": [
            "Consider adding more unit tests",
            "Update documentation for new functions"
        ]
    }
    return APIResponse(success=True, data=mock_result)

# Workflow endpoints


@app.get("/workflows/")
async def get_workflows():
    return MOCK_WORKFLOWS


@app.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, inputs: Optional[Dict] = None):
    execution_id = f"exec-{random.randint(1000, 9999)}"
    return {
        "execution_id": execution_id,
        "status": "running",
        "started_at": datetime.now().isoformat()
    }


@app.get("/workflows/executions/{execution_id}/status")
async def get_execution_status(execution_id: str):
    return {
        "execution_id": execution_id,
        "status": "completed",
        "progress": 100,
        "started_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import sys
    port = 8002 if len(sys.argv) > 1 and sys.argv[1] == "--port" else 8002

    print("🚀 MCP Platform Mock API Server Starting...")
    print("📍 URL: http://localhost:8002")
    print("📖 Docs: http://localhost:8002/docs")
    print("🧪 This is a MOCK server for testing the VS Code extension")
    print("💡 Use this URL in your extension settings: http://localhost:8002")
    print("🛑 Stop with Ctrl+C")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8009, log_level="info")
