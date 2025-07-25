"""
Configuration manager for MCP servers
"""

import json
import logging
from typing import Dict, List, Any
from pathlib import Path

from ..core.interfaces import MCPServerConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration management for MCP servers"""

    def __init__(self):
        self.configs: Dict[str, MCPServerConfig] = {}
        self.config_file = Path("mcp_config.json")

    async def load_configurations(self) -> None:
        """Load MCP server configurations from Kiro settings"""
        # Try to load from Kiro MCP settings first
        kiro_mcp_path = Path("C:/Users/TT/.kiro/settings/mcp.json")
        
        if kiro_mcp_path.exists():
            try:
                with open(kiro_mcp_path, 'r', encoding='utf-8') as f:
                    kiro_data = json.load(f)
                    
                # Convert Kiro MCP config to our format
                for server_name, server_config in kiro_data.get('mcpServers', {}).items():
                    if not server_config.get('disabled', False):
                        config = MCPServerConfig(
                            name=server_name,
                            command=server_config.get('command', 'python'),
                            args=server_config.get('args', []),
                            env=server_config.get('env', {}),
                            timeout=30,
                            health_check_interval=60
                        )
                        self.configs[server_name] = config
                        
                logger.info(f"Loaded {len(self.configs)} configurations from Kiro MCP settings")
                return
                
            except Exception as e:
                logger.error(f"Error loading Kiro MCP config: {e}")
        
        # Fallback to default configurations for development
        default_configs = [
            MCPServerConfig(
                name="kiro-tools",
                command="uvx",
                args=["kiro-tools"],
                env={},
                timeout=30,
                health_check_interval=60
            ),
            MCPServerConfig(
                name="groq-llm",
                command="uvx",
                args=["groq-llm"],
                env={},
                timeout=30,
                health_check_interval=60
            ),
            MCPServerConfig(
                name="browser-automation",
                command="uvx",
                args=["browser-automation"],
                env={},
                timeout=30,
                health_check_interval=60
            ),
            MCPServerConfig(
                name="api-key-sniffer",
                command="uvx",
                args=["api-key-sniffer"],
                env={},
                timeout=30,
                health_check_interval=60
            ),
            MCPServerConfig(
                name="network-analysis",
                command="uvx",
                args=["network-analysis"],
                env={},
                timeout=30,
                health_check_interval=60
            )
        ]

        # Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for config_data in data.get('servers', []):
                        config = MCPServerConfig(**config_data)
                        self.configs[config.name] = config
                logger.info(
                    f"Loaded {len(self.configs)} configurations from file")
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                # Fall back to defaults
                for config in default_configs:
                    self.configs[config.name] = config
        else:
            # Use defaults
            for config in default_configs:
                self.configs[config.name] = config
            logger.info(f"Using {len(self.configs)} default configurations")

    async def save_configurations(self) -> None:
        """Save current configurations to file"""
        try:
            data = {
                'servers': [config.model_dump() for config in self.configs.values()]
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info("Configurations saved to file")
        except Exception as e:
            logger.error(f"Error saving configurations: {e}")

    def get_config(self, server_name: str) -> MCPServerConfig:
        """Get configuration for a specific server"""
        return self.configs.get(server_name)

    def get_all_configs(self) -> Dict[str, MCPServerConfig]:
        """Get all server configurations"""
        return self.configs.copy()

    def add_config(self, config: MCPServerConfig) -> None:
        """Add a new server configuration"""
        self.configs[config.name] = config
        logger.info(f"Added configuration for: {config.name}")

    def remove_config(self, server_name: str) -> bool:
        """Remove a server configuration"""
        if server_name in self.configs:
            del self.configs[server_name]
            logger.info(f"Removed configuration for: {server_name}")
            return True
        return False

    def list_configurations(self) -> Dict[str, MCPServerConfig]:
        """List all configurations"""
        return self.configs.copy()

    def get_configuration(self, server_name: str) -> MCPServerConfig:
        """Get configuration for a specific server"""
        return self.configs.get(server_name)

    async def update_configuration(self, server_name: str, updates: Dict[str, Any]) -> MCPServerConfig:
        """Update configuration for a specific server"""
        if server_name not in self.configs:
            raise ValueError(f"Configuration for {server_name} not found")
        
        config = self.configs[server_name]
        
        # Update configuration fields
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        await self.save_configurations()
        return config

    async def save_configuration(self, config: MCPServerConfig) -> None:
        """Save a single configuration"""
        self.configs[config.name] = config
        await self.save_configurations()

    async def delete_configuration(self, server_name: str) -> bool:
        """Delete a server configuration"""
        if server_name in self.configs:
            del self.configs[server_name]
            await self.save_configurations()
            return True
        return False


# Singleton instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get config manager singleton"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
