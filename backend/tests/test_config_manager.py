"""
Tests for MCP Configuration Manager

This module contains unit tests for the configuration management functionality.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from app.services.config_manager import MCPConfigManager, ConfigurationError
from app.core.interfaces import MCPServerConfig


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_config():
    """Sample MCP server configuration"""
    return MCPServerConfig(
        name="test-server",
        command="uvx",
        args=["test-mcp-server"],
        env={"TEST_API_KEY": "test-key"},
        timeout=30,
        retry_count=3
    )


@pytest.fixture
def sample_json_config():
    """Sample JSON configuration data"""
    return {
        "mcpServers": {
            "groq-llm": {
                "command": "uvx",
                "args": ["mcp-server-groq"],
                "env": {"GROQ_API_KEY": "test-key"},
                "timeout": 30
            },
            "browser-automation": {
                "command": "uvx",
                "args": ["mcp-server-browser"],
                "env": {"BRAVE_SEARCH_API_KEY": "test-key"},
                "timeout": 60,
                "disabled": False
            }
        }
    }


class TestMCPConfigManager:
    """Test cases for MCPConfigManager class"""

    def test_initialization(self, temp_config_dir):
        """Test configuration manager initialization"""
        manager = MCPConfigManager(temp_config_dir)
        assert manager.config_dir == Path(temp_config_dir)
        assert len(manager.configs) == 0
        assert manager.config_dir.exists()

    @pytest.mark.asyncio
    async def test_load_from_json(self, temp_config_dir, sample_json_config):
        """Test loading configurations from JSON files"""
        manager = MCPConfigManager(temp_config_dir)

        # Create test JSON file
        json_file = Path(temp_config_dir) / "test_config.json"
        with open(json_file, 'w') as f:
            json.dump(sample_json_config, f)

        await manager.load_configurations()

        assert len(manager.configs) == 2
        assert "groq-llm" in manager.configs
        assert "browser-automation" in manager.configs

        groq_config = manager.configs["groq-llm"]
        assert groq_config.command == "uvx"
        assert groq_config.args == ["mcp-server-groq"]
        assert groq_config.env["GROQ_API_KEY"] == "test-key"

    @pytest.mark.asyncio
    async def test_load_from_yaml(self, temp_config_dir):
        """Test loading configurations from YAML files"""
        manager = MCPConfigManager(temp_config_dir)

        yaml_content = """
servers:
  - name: test-yaml-server
    command: uvx
    args: ["test-server"]
    env:
      TEST_KEY: "yaml-value"
    timeout: 45
"""

        # Create test YAML file
        yaml_file = Path(temp_config_dir) / "test_config.yaml"
        with open(yaml_file, 'w') as f:
            f.write(yaml_content)

        await manager.load_configurations()

        assert len(manager.configs) == 1
        assert "test-yaml-server" in manager.configs

        config = manager.configs["test-yaml-server"]
        assert config.command == "uvx"
        assert config.env["TEST_KEY"] == "yaml-value"
        assert config.timeout == 45

    @pytest.mark.asyncio
    async def test_load_from_env(self, temp_config_dir):
        """Test loading configurations from environment variables"""
        manager = MCPConfigManager(temp_config_dir)

        env_config = {
            "command": "python",
            "args": ["test_server.py"],
            "env": {"API_KEY": "env-key"},
            "timeout": 20
        }

        with patch.dict(os.environ, {
            "MCP_SERVER_ENVTEST_CONFIG": json.dumps(env_config)
        }):
            await manager.load_configurations()

        assert len(manager.configs) == 1
        assert "envtest" in manager.configs

        config = manager.configs["envtest"]
        assert config.command == "python"
        assert config.args == ["test_server.py"]
        assert config.env["API_KEY"] == "env-key"

    @pytest.mark.asyncio
    async def test_save_configuration(self, temp_config_dir, sample_config):
        """Test saving a configuration to file"""
        manager = MCPConfigManager(temp_config_dir)

        await manager.save_configuration(sample_config)

        # Check if file was created
        config_file = Path(temp_config_dir) / f"{sample_config.name}.json"
        assert config_file.exists()

        # Verify file content
        with open(config_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["name"] == sample_config.name
        assert saved_data["command"] == sample_config.command
        assert saved_data["args"] == sample_config.args

        # Check in-memory storage
        assert sample_config.name in manager.configs

    @pytest.mark.asyncio
    async def test_update_configuration(self, temp_config_dir, sample_config):
        """Test updating an existing configuration"""
        manager = MCPConfigManager(temp_config_dir)
        manager.configs[sample_config.name] = sample_config

        updates = {
            "timeout": 60,
            "retry_count": 5,
            "env": {"NEW_KEY": "new-value"}
        }

        with patch.object(manager, 'save_configuration') as mock_save:
            updated_config = await manager.update_configuration(sample_config.name, updates)

        assert updated_config.timeout == 60
        assert updated_config.retry_count == 5
        assert updated_config.env["NEW_KEY"] == "new-value"
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_configuration(self, temp_config_dir):
        """Test updating a configuration that doesn't exist"""
        manager = MCPConfigManager(temp_config_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            await manager.update_configuration("nonexistent", {"timeout": 60})

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_configuration(self, temp_config_dir, sample_config):
        """Test deleting a configuration"""
        manager = MCPConfigManager(temp_config_dir)
        manager.configs[sample_config.name] = sample_config

        # Create config file
        config_file = Path(temp_config_dir) / f"{sample_config.name}.json"
        config_file.touch()

        result = await manager.delete_configuration(sample_config.name)

        assert result is True
        assert sample_config.name not in manager.configs
        assert not config_file.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_configuration(self, temp_config_dir):
        """Test deleting a configuration that doesn't exist"""
        manager = MCPConfigManager(temp_config_dir)

        result = await manager.delete_configuration("nonexistent")
        assert result is False

    def test_get_configuration(self, temp_config_dir, sample_config):
        """Test getting a specific configuration"""
        manager = MCPConfigManager(temp_config_dir)
        manager.configs[sample_config.name] = sample_config

        retrieved_config = manager.get_configuration(sample_config.name)
        assert retrieved_config == sample_config

        nonexistent_config = manager.get_configuration("nonexistent")
        assert nonexistent_config is None

    def test_list_configurations(self, temp_config_dir, sample_config):
        """Test listing all configurations"""
        manager = MCPConfigManager(temp_config_dir)

        # Empty list initially
        configs = manager.list_configurations()
        assert len(configs) == 0

        # Add configuration
        manager.configs[sample_config.name] = sample_config
        configs = manager.list_configurations()
        assert len(configs) == 1
        assert configs[0] == sample_config

    @pytest.mark.asyncio
    async def test_validate_server_startup_success(self, temp_config_dir, sample_config):
        """Test successful server startup validation"""
        manager = MCPConfigManager(temp_config_dir)

        with patch('shutil.which', return_value='/usr/bin/uvx'), \
                patch('subprocess.run') as mock_run:

            mock_run.return_value.returncode = 0
            mock_run.return_value.stderr = b""

            result = await manager.validate_server_startup(sample_config)
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_server_startup_command_not_found(self, temp_config_dir, sample_config):
        """Test server startup validation with missing command"""
        manager = MCPConfigManager(temp_config_dir)

        with patch('shutil.which', return_value=None):
            result = await manager.validate_server_startup(sample_config)
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_server_startup_command_fails(self, temp_config_dir, sample_config):
        """Test server startup validation with failing command"""
        manager = MCPConfigManager(temp_config_dir)

        with patch('shutil.which', return_value='/usr/bin/uvx'), \
                patch('subprocess.run') as mock_run:

            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = b"Command failed"

            result = await manager.validate_server_startup(sample_config)
            assert result is False

    def test_create_default_configurations(self, temp_config_dir):
        """Test creating default configurations"""
        manager = MCPConfigManager(temp_config_dir)

        manager.create_default_configurations()

        assert len(manager.configs) > 0
        assert "groq-llm" in manager.configs
        assert "browser-automation" in manager.configs
        assert "enhanced-git" in manager.configs

        groq_config = manager.configs["groq-llm"]
        assert groq_config.command == "uvx"
        assert "mcp-server-groq" in groq_config.args

    @pytest.mark.asyncio
    async def test_configuration_validation_invalid_timeout(self, temp_config_dir):
        """Test configuration validation with invalid timeout"""
        manager = MCPConfigManager(temp_config_dir)

        invalid_config = {
            "mcpServers": {
                "invalid-server": {
                    "command": "uvx",
                    "args": ["test"],
                    "timeout": -1  # Invalid timeout
                }
            }
        }

        # Create test JSON file with invalid config
        json_file = Path(temp_config_dir) / "invalid_config.json"
        with open(json_file, 'w') as f:
            json.dump(invalid_config, f)

        await manager.load_configurations()

        # Invalid configuration should be filtered out
        assert "invalid-server" not in manager.configs

    @pytest.mark.asyncio
    async def test_reload_configurations(self, temp_config_dir, sample_json_config):
        """Test reloading configurations"""
        manager = MCPConfigManager(temp_config_dir)

        # Add initial config
        manager.configs["existing"] = MCPServerConfig(
            name="existing", command="test", args=[])

        # Create new config file
        json_file = Path(temp_config_dir) / "new_config.json"
        with open(json_file, 'w') as f:
            json.dump(sample_json_config, f)

        reloaded_configs = await manager.reload_configurations()

        # Old config should be gone, new configs should be loaded
        assert "existing" not in manager.configs
        assert len(reloaded_configs) == 2
        assert "groq-llm" in reloaded_configs
        assert "browser-automation" in reloaded_configs

    def test_parse_server_config_with_disabled_flag(self, temp_config_dir):
        """Test parsing server configuration with disabled flag"""
        manager = MCPConfigManager(temp_config_dir)

        config_data = {
            "command": "uvx",
            "args": ["test-server"],
            "disabled": True,
            "auto_restart": True
        }

        config = manager._parse_server_config("test-server", config_data)

        assert config.name == "test-server"
        assert config.auto_restart is False  # Should be overridden by disabled flag

    @pytest.mark.asyncio
    async def test_load_configurations_with_file_errors(self, temp_config_dir):
        """Test loading configurations with file read errors"""
        manager = MCPConfigManager(temp_config_dir)

        # Create invalid JSON file
        invalid_json_file = Path(temp_config_dir) / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write("{ invalid json }")

        # Should not raise exception, just log warning
        configs = await manager.load_configurations()
        assert isinstance(configs, dict)
