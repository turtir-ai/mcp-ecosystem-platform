"""
Main FastAPI application for MCP Ecosystem Platform

This is the entry point for the FastAPI backend server.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
import logging
from contextlib import asynccontextmanager
import time
from datetime import datetime

from app.core.config import get_settings
from app.core.interfaces import APIResponse
from app.services.health_monitor import get_health_monitor
from app.services.config_manager import get_config_manager
from app.services.mcp_client import get_mcp_client_manager
from app.api.routes import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# Lifespan removed - using on_event instead


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Developer productivity suite with MCP servers",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("🚀 Starting MCP Ecosystem Platform...")
        
        # Initialize configuration manager
        config_manager = get_config_manager()
        await config_manager.load_configurations()
        logger.info("✅ Configuration manager initialized")

        # Start health monitoring and register servers
        health_monitor = get_health_monitor()
        
        # Register all configured servers with health monitor
        for config in config_manager.get_all_configs().values():
            await health_monitor.register_server(config)
        
        await health_monitor.start_monitoring()
        logger.info("✅ Health monitoring started")
        
        # Start AI Orchestrator
        from app.services.ai_orchestrator import get_ai_orchestrator
        orchestrator = get_ai_orchestrator()
        await orchestrator.start_orchestration()
        logger.info("✅ AI Orchestrator started")
        
        logger.info("🎉 MCP Ecosystem Platform started successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("🛑 Shutting down MCP Ecosystem Platform...")
        
        # Stop AI Orchestrator
        from app.services.ai_orchestrator import get_ai_orchestrator
        orchestrator = get_ai_orchestrator()
        await orchestrator.stop_orchestration()
        logger.info("✅ AI Orchestrator stopped")
        
        # Stop health monitoring
        health_monitor = get_health_monitor()
        await health_monitor.stop_monitoring()
        logger.info("✅ Health monitoring stopped")
        
        logger.info("🎉 MCP Ecosystem Platform shut down successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.security.allowed_hosts
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    return JSONResponse(
        status_code=422,
        content=APIResponse(
            success=False,
            error="Validation Error",
            data={"details": exc.errors()}
        ).model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            error=exc.detail
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            error="Internal Server Error"
        ).model_dump()
    )


# Dashboard redirect endpoint
@app.get("/dashboard")
async def dashboard_redirect():
    """Redirect to frontend dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:3000", status_code=302)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with detailed system status"""
    try:
        # Get health monitor instance
        health_monitor = get_health_monitor()
        
        # Get MCP server statuses
        mcp_statuses = {}
        try:
            mcp_statuses = await health_monitor.get_all_statuses()
        except Exception as e:
            logger.warning(f"Could not get MCP server statuses: {e}")
        
        # Determine overall system health
        overall_status = "healthy"
        unhealthy_services = []
        
        # Check MCP servers health
        for server_name, status in mcp_statuses.items():
            if status.status in ["unhealthy", "offline"]:
                overall_status = "degraded"
                unhealthy_services.append(f"mcp_server_{server_name}")
        
        # Get configuration manager status
        config_status = "connected"
        try:
            config_manager = get_config_manager()
            config_count = len(config_manager.get_all_configs())
        except Exception as e:
            config_status = "error"
            config_count = 0
            logger.warning(f"Config manager error: {e}")
        
        return APIResponse(
            success=True,
            data={
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "version": settings.app_version,
                "environment": settings.environment,
                "services": {
                    "database": "not_configured",  # Will be updated when DB is added
                    "mcp_servers": "active" if mcp_statuses else "no_servers",
                    "config_manager": config_status
                },
                "mcp_servers": {
                    "total": len(mcp_statuses),
                    "healthy": len([s for s in mcp_statuses.values() if s.status == "healthy"]),
                    "unhealthy": len([s for s in mcp_statuses.values() if s.status in ["unhealthy", "offline"]]),
                    "servers": {name: {
                        "status": status.status,
                        "response_time_ms": status.response_time_ms,
                        "uptime_percentage": status.uptime_percentage,
                        "last_check": status.last_check.isoformat() if status.last_check else None
                    } for name, status in mcp_statuses.items()}
                },
                "configuration": {
                    "total_servers": config_count
                },
                "unhealthy_services": unhealthy_services
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return APIResponse(
            success=False,
            error=f"Health check failed: {str(e)}",
            data={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "version": settings.app_version,
                "environment": settings.environment
            }
        )

# API health check endpoint
@app.get("/api/v1/health")
async def api_health_check():
    """API health check endpoint with system information"""
    try:
        # Get basic system info
        health_monitor = get_health_monitor()
        config_manager = get_config_manager()
        
        # Get MCP server count
        mcp_count = 0
        try:
            mcp_statuses = await health_monitor.get_all_statuses()
            mcp_count = len(mcp_statuses)
        except Exception:
            pass
        
        return APIResponse(
            success=True,
            data={
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": settings.app_version,
                "api_version": "v1",
                "system_info": {
                    "mcp_servers_configured": len(config_manager.get_all_configs()),
                    "mcp_servers_active": mcp_count,
                    "environment": settings.environment
                }
            }
        )
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return APIResponse(
            success=False,
            error=f"API health check failed: {str(e)}",
            data={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "version": settings.app_version,
                "api_version": "v1"
            }
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return APIResponse(
        success=True,
        data={
            "name": settings.app_name,
            "version": settings.app_version,
            "description": "Developer productivity suite with MCP servers",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "health_url": "/health"
        }
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
        workers=settings.api.workers if not settings.api.reload else 1
    )

# Test endpoint


@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return APIResponse(
        success=True,
        data={
            "message": "MCP Ecosystem Platform API is running!",
            "timestamp": datetime.now(),
            "version": settings.app_version
        }
    )
