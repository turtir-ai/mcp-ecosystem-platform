"""
Tests for MCP Tools
"""

import pytest
import asyncio
from backend.app.services.mcp_tools import (
    SystemHealthMCPTool, 
    MCPServerControlTool, 
    MCPToolRegistry,
    get_mcp_tool_registry
)


class TestSystemHealthMCPTool:
    
    def setup_method(self):
        """Setup test tool"""
        self.tool = SystemHealthMCPTool()
    
    def test_tool_properties(self):
        """Test tool basic properties"""
        assert self.tool.name == "get_system_health"
        assert "system health" in self.tool.description.lower()
        assert "type" in self.tool.input_schema
        assert "properties" in self.tool.input_schema
    
    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """Test basic execution"""
        result = await self.tool.execute({})
        
        assert "success" in result
        if result["success"]:
            assert "data" in result
            data = result["data"]
            assert "timestamp" in data
            assert "overall_status" in data
            assert "mcp_servers" in data
    
    @pytest.mark.asyncio
    async def test_execute_with_filters(self):
        """Test execution with server filter"""
        result = await self.tool.execute({
            "server_filter": ["groq-llm", "kiro-tools"],
            "include_insights": False,
            "include_metrics": False
        })
        
        assert "success" in result
        if result["success"]:
            data = result["data"]
            assert "mcp_servers" in data
            # Should only include filtered servers or be empty if they don't exist
            server_details = data["mcp_servers"].get("server_details", {})
            for server_name in server_details.keys():
                assert server_name in ["groq-llm", "kiro-tools"]


class TestMCPServerControlTool:
    
    def setup_method(self):
        """Setup test tool"""
        self.tool = MCPServerControlTool()
    
    def test_tool_properties(self):
        """Test tool basic properties"""
        assert self.tool.name == "restart_mcp_server"
        assert "restart" in self.tool.description.lower()
        assert "server_name" in self.tool.input_schema["properties"]
        assert "server_name" in self.tool.input_schema["required"]
    
    @pytest.mark.asyncio
    async def test_execute_missing_server_name(self):
        """Test execution without server name"""
        with pytest.raises(KeyError):
            await self.tool.execute({})
    
    @pytest.mark.asyncio
    async def test_execute_restricted_server(self):
        """Test execution with restricted server"""
        result = await self.tool.execute({
            "server_name": "kiro-tools",
            "reasoning": "Test restart"
        })
        
        assert "success" in result
        # Should fail due to security restrictions
        assert result["success"] is False
        assert "requires_approval" in result or "not allowed" in result.get("error", "").lower()
    
    @pytest.mark.asyncio
    async def test_execute_allowed_server(self):
        """Test execution with allowed server"""
        result = await self.tool.execute({
            "server_name": "groq-llm",
            "reasoning": "Test restart"
        })
        
        assert "success" in result
        # May succeed or require approval depending on security settings


class TestMCPToolRegistry:
    
    def setup_method(self):
        """Setup test registry"""
        self.registry = MCPToolRegistry()
    
    def test_list_tools(self):
        """Test listing tools"""
        tools = self.registry.list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) >= 2  # Should have at least system health and server control
        
        tool_names = [tool["name"] for tool in tools]
        assert "get_system_health" in tool_names
        assert "restart_mcp_server" in tool_names
        
        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
    
    def test_get_tool(self):
        """Test getting specific tool"""
        health_tool = self.registry.get_tool("get_system_health")
        assert health_tool is not None
        assert health_tool.name == "get_system_health"
        
        nonexistent_tool = self.registry.get_tool("nonexistent")
        assert nonexistent_tool is None
    
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing tool via registry"""
        result = await self.registry.execute_tool("get_system_health", {})
        
        assert "success" in result
        # Should either succeed or fail gracefully
        
        # Test nonexistent tool
        result = await self.registry.execute_tool("nonexistent", {})
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestMCPToolsIntegration:
    
    def test_global_registry(self):
        """Test global registry access"""
        registry = get_mcp_tool_registry()
        assert registry is not None
        assert isinstance(registry, MCPToolRegistry)
        
        # Should be singleton
        registry2 = get_mcp_tool_registry()
        assert registry is registry2
    
    @pytest.mark.asyncio
    async def test_cross_server_health_query(self):
        """Test that other MCP servers can query system health"""
        registry = get_mcp_tool_registry()
        
        # Simulate another MCP server querying system health
        result = await registry.execute_tool("get_system_health", {
            "include_insights": True,
            "include_metrics": True,
            "server_filter": []  # Get all servers
        })
        
        assert "success" in result
        if result["success"]:
            data = result["data"]
            assert "overall_status" in data
            assert "mcp_servers" in data
            assert "timestamp" in data
            
            # Should include insights and metrics
            if "actionable_insights" in data:
                assert isinstance(data["actionable_insights"], list)
            if "resource_usage" in data:
                assert isinstance(data["resource_usage"], dict)


if __name__ == '__main__':
    pytest.main([__file__])