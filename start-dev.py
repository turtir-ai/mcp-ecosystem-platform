#!/usr/bin/env python3
"""
Development startup script for MCP Ecosystem Platform

This script starts the development environment:
1. Checks prerequisites
2. Starts backend FastAPI server
3. Provides instructions for frontend
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.11+"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_node_version():
    """Check if Node.js is available"""
    try:
        result = subprocess.run(['node', '--version'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("❌ Node.js not found")
    return False


def install_backend_deps():
    """Install backend dependencies"""
    print("\n📦 Installing backend dependencies...")
    backend_dir = Path("backend")

    if not (backend_dir / "requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False

    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], cwd=backend_dir, check=True)
        print("✅ Backend dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install backend dependencies")
        return False


def install_frontend_deps():
    """Install frontend dependencies"""
    print("\n📦 Installing frontend dependencies...")
    frontend_dir = Path("frontend")

    if not (frontend_dir / "package.json").exists():
        print("❌ package.json not found")
        return False

    try:
        # Windows'ta npm.cmd kullan
        npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
        subprocess.run([npm_cmd, "install"], cwd=frontend_dir, check=True)
        print("✅ Frontend dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install frontend dependencies")
        return False


def start_backend():
    """Start FastAPI backend server"""
    print("\n🚀 Starting FastAPI backend...")
    backend_dir = Path("backend")

    try:
        # Start uvicorn server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload"
        ], cwd=backend_dir)

        print("✅ Backend started on http://localhost:8001")
        print("📖 API docs: http://localhost:8001/docs")
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None


def start_frontend():
    """Start React frontend server"""
    print("\n🌐 Starting React frontend...")
    frontend_dir = Path("frontend")

    try:
        # Start React development server
        npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
        process = subprocess.Popen([
            npm_cmd, "start"
        ], cwd=frontend_dir)

        print("✅ Frontend starting on http://localhost:3000")
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None


def start_mcp_manager():
    """Start MCP Manager (mock server for development)"""
    print("\n📡 Starting MCP Manager...")

    try:
        # Start mock API server
        process = subprocess.Popen([
            sys.executable, "mock-api-server.py"
        ])

        print("✅ MCP Manager started on http://localhost:8009")
        return process
    except Exception as e:
        print(f"❌ Failed to start MCP Manager: {e}")
        return None


def main():
    """Main startup function"""
    print("🚀 MCP Ecosystem Platform - Development Startup")
    print("=" * 50)
    print("🎯 Faz 0: Stabilizasyon - Tek Noktadan Kontrol")
    print("📍 Port Standardizasyonu:")
    print("   • Backend API: 8001")
    print("   • Frontend: 3000") 
    print("   • MCP Manager: 8009")
    print("=" * 50)

    # Check prerequisites
    if not check_python_version():
        sys.exit(1)

    node_available = check_node_version()

    # Install dependencies
    if not install_backend_deps():
        sys.exit(1)

    if node_available:
        install_frontend_deps()

    # Start all services
    processes = []
    
    print("\n🔄 Starting services in sequence...")
    
    # Start backend
    print("1️⃣ Starting Backend API...")
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    processes.append(("Backend", backend_process))
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start MCP Manager
    print("2️⃣ Starting MCP Manager...")
    mcp_process = start_mcp_manager()
    if mcp_process:
        processes.append(("MCP Manager", mcp_process))
        time.sleep(2)
    
    # Start frontend if Node.js is available
    frontend_process = None
    if node_available:
        print("3️⃣ Starting Frontend...")
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(("Frontend", frontend_process))
            time.sleep(3)

    print("\n" + "=" * 70)
    print("🎉 MCP Ecosystem Platform Started Successfully!")
    print("=" * 70)
    print("📊 Backend API: http://localhost:8001")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("🔍 Health Check: http://localhost:8001/health")
    print("📡 MCP Status: http://localhost:8001/api/v1/mcp/status")
    print("🛠️  MCP Manager: http://localhost:8009")
    
    if frontend_process:
        print("🌐 Frontend: http://localhost:3000")
        print("\n💡 All services are running! Open http://localhost:3000 to start.")
        print("🔧 VS Code Extension should now connect successfully!")
    else:
        print("\n⚠️  Frontend not started (Node.js required)")
        print("💡 Backend API is ready at http://localhost:8001")

    print("\n⏹️  Press Ctrl+C to stop all services")
    print("=" * 70)

    try:
        # Keep the script running and wait for any process to exit
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\n⚠️  {name} process has stopped")
                    break
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        
        # Terminate all processes
        for name, process in processes:
            try:
                process.terminate()
                print(f"✅ {name} stopped")
            except:
                pass
        
        # Wait for processes to terminate
        for name, process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("🎉 All services stopped successfully!")
        print("🔧 Faz 0: Stabilizasyon tamamlandı!")


if __name__ == "__main__":
    main()
