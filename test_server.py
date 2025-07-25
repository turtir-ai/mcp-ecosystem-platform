#!/usr/bin/env python3
"""
Simple test server for MCP Ecosystem Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="MCP Ecosystem Platform - Test",
    description="Test server for MCP Ecosystem Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MCP Ecosystem Platform Test Server",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/mcp/status")
async def mcp_status():
    """Mock MCP status endpoint"""
    return {
        "success": True,
        "data": {
            "kiro-tools": {"status": "healthy", "response_time_ms": 45.2},
            "groq-llm": {"status": "healthy", "response_time_ms": 123.5},
            "openrouter-llm": {"status": "healthy", "response_time_ms": 89.1},
            "browser-automation": {"status": "healthy", "response_time_ms": 234.7},
            "real-browser": {"status": "healthy", "response_time_ms": 156.3},
            "deep-research": {"status": "healthy", "response_time_ms": 298.4},
            "api-key-sniffer": {"status": "healthy", "response_time_ms": 67.8},
            "network-analysis": {"status": "healthy", "response_time_ms": 112.9},
            "enhanced-filesystem": {"status": "healthy", "response_time_ms": 34.6},
            "enhanced-git": {"status": "healthy", "response_time_ms": 78.2},
            "simple-warp": {"status": "healthy", "response_time_ms": 56.4}
        }
    }

if __name__ == "__main__":
    print("🚀 Starting MCP Ecosystem Platform Test Server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )