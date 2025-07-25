FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for MCP server management
RUN pip install uv

# Copy MCP server management scripts
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp \
    && chown -R mcp:mcp /app
USER mcp

# Expose port for health checks
EXPOSE 8080

# Run MCP server manager
CMD ["python", "manager.py"]