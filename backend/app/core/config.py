"""
Configuration fix for MCP Ecosystem Platform
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class MCPServerConfig:
    """Configuration for an MCP server"""

    def __init__(self, name: str, command: str, args: list = None, env: dict = None,
                 timeout: int = 30, retry_count: int = 3, health_check_interval: int = 60,
                 auto_restart: bool = True):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.timeout = timeout
        self.retry_count = retry_count
        self.health_check_interval = health_check_interval
        self.auto_restart = auto_restart


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    url: str = Field(
        default="postgresql://user:password@localhost:5432/mcp_platform")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)
    echo: bool = Field(default=False)

    class Config:
        env_prefix = "DATABASE_"


class RedisConfig(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379/0")
    max_connections: int = Field(default=10)
    socket_timeout: int = Field(default=5)
    socket_connect_timeout: int = Field(default=5)

    class Config:
        env_prefix = "REDIS_"


class AuthConfig(BaseSettings):
    """Authentication configuration"""
    secret_key: str = Field(default="your-secret-key-change-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    class Config:
        env_prefix = "AUTH_"


class MCPConfig(BaseSettings):
    """MCP servers configuration"""
    config_file: str = Field(default=".kiro/settings/mcp.json")
    health_check_interval: int = Field(default=60)
    default_timeout: int = Field(default=30)
    max_retry_count: int = Field(default=3)
    auto_restart: bool = Field(default=True)

    class Config:
        env_prefix = "MCP_"


class APIConfig(BaseSettings):
    """API configuration"""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)
    debug: bool = Field(default=False)
    reload: bool = Field(default=False)
    workers: int = Field(default=1)
    cors_origins: List[str] = Field(default=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8080",
        "http://localhost:5173",
        "vscode-webview://*",
        "https://vscode-webview.net",
        "*"
    ])
    api_prefix: str = Field(default="/api/v1")

    class Config:
        env_prefix = "API_"


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_path: Optional[str] = Field(default=None)
    max_file_size: int = Field(default=10485760)  # 10MB
    backup_count: int = Field(default=5)

    class Config:
        env_prefix = "LOG_"


class SecurityConfig(BaseSettings):
    """Security configuration"""
    rate_limit_per_minute: int = Field(default=60)
    max_request_size: int = Field(default=16777216)  # 16MB
    allowed_hosts: List[str] = Field(default=["*"])
    trust_proxy_headers: bool = Field(default=False)

    class Config:
        env_prefix = "SECURITY_"


class Settings(BaseSettings):
    """Main application settings"""

    # Application info
    app_name: str = Field(default="MCP Ecosystem Platform")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")

    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # External API keys
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    openrouter_api_key: Optional[str] = Field(
        default=None, env="OPENROUTER_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    brave_search_api_key: Optional[str] = Field(
        default=None, env="BRAVE_SEARCH_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v

    def is_development(self) -> bool:
        return self.environment == "development"

    def is_production(self) -> bool:
        return self.environment == "production"

    def is_testing(self) -> bool:
        return self.environment == "testing"


class MCPServerManager:
    """Manages MCP server configurations"""

    def __init__(self, config_file: str = ".kiro/settings/mcp.json"):
        self.config_file = Path(config_file)
        self._servers: Dict[str, MCPServerConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load MCP server configurations from file"""
        if not self.config_file.exists():
            # Create default config if file doesn't exist
            self._create_default_config()
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            mcp_servers = config_data.get("mcpServers", {})

            for name, server_config in mcp_servers.items():
                if server_config.get("disabled", False):
                    continue

                self._servers[name] = MCPServerConfig(
                    name=name,
                    command=server_config["command"],
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                    timeout=server_config.get("timeout", 30),
                    retry_count=server_config.get("retry_count", 3),
                    health_check_interval=server_config.get(
                        "health_check_interval", 60),
                    auto_restart=server_config.get("auto_restart", True)
                )

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in MCP config file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load MCP config: {e}")

    def _create_default_config(self) -> None:
        """Create default MCP configuration"""
        default_config = {
            "mcpServers": {
                "test-server": {
                    "command": "echo",
                    "args": ["MCP Test Server"],
                    "env": {},
                    "disabled": False
                }
            }
        }

        # Create directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write default config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)

        print(f"Created default MCP config at: {self.config_file}")

        # Load the default config
        self._load_config()

    def get_server_config(self, name: str) -> Optional[MCPServerConfig]:
        """Get configuration for a specific MCP server"""
        return self._servers.get(name)

    def get_all_servers(self) -> Dict[str, MCPServerConfig]:
        """Get all MCP server configurations"""
        return self._servers.copy()

    def get_server_names(self) -> List[str]:
        """Get list of all configured server names"""
        return list(self._servers.keys())

    def is_server_enabled(self, name: str) -> bool:
        """Check if a server is enabled"""
        return name in self._servers

    def reload_config(self) -> None:
        """Reload configuration from file"""
        self._servers.clear()
        self._load_config()


# Create settings with error handling
try:
    settings = Settings()
    mcp_manager = MCPServerManager(settings.mcp.config_file)
except Exception as e:
    print(f"Warning: Could not load full settings: {e}")
    # Create minimal settings for startup
    settings = Settings()
    mcp_manager = None


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def get_mcp_manager() -> Optional[MCPServerManager]:
    """Get MCP server manager"""
    return mcp_manager
