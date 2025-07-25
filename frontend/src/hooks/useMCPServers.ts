import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../services/api';

interface MCPServer {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'offline';
  response_time_ms: number;
  last_check: string;
  error_message?: string;
  uptime_percentage?: number;
  tools?: any[];
  recent_activity?: any[];
  metrics?: {
    total_requests: number;
    successful_requests: number;
    average_response_time: number;
  };
}

interface MCPTool {
  name: string;
  description?: string;
  parameters?: any;
}

export const useMCPServers = () => {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [tools, setTools] = useState<Record<string, MCPTool[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshServers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.getMCPStatus();
      setServers(response);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch MCP servers');
      console.error('Failed to fetch MCP servers:', err);
      
      // Fallback to mock data for development
      const mockServers: MCPServer[] = [
        {
          name: 'kiro-tools',
          status: 'healthy',
          response_time_ms: 45,
          last_check: new Date().toISOString(),
          uptime_percentage: 99.5
        },
        {
          name: 'groq-llm',
          status: 'healthy',
          response_time_ms: 120,
          last_check: new Date().toISOString(),
          uptime_percentage: 98.2
        },
        {
          name: 'browser-automation',
          status: 'healthy',
          response_time_ms: 200,
          last_check: new Date().toISOString(),
          uptime_percentage: 97.8
        },
        {
          name: 'deep-research',
          status: 'healthy',
          response_time_ms: 300,
          last_check: new Date().toISOString(),
          uptime_percentage: 96.5
        },
        {
          name: 'api-key-sniffer',
          status: 'healthy',
          response_time_ms: 80,
          last_check: new Date().toISOString(),
          uptime_percentage: 99.1
        },
        {
          name: 'network-analysis',
          status: 'degraded',
          response_time_ms: 500,
          last_check: new Date().toISOString(),
          uptime_percentage: 94.2,
          error_message: 'High response time detected'
        },
        {
          name: 'enhanced-filesystem',
          status: 'healthy',
          response_time_ms: 60,
          last_check: new Date().toISOString(),
          uptime_percentage: 99.8
        },
        {
          name: 'enhanced-git',
          status: 'healthy',
          response_time_ms: 90,
          last_check: new Date().toISOString(),
          uptime_percentage: 98.9
        },
        {
          name: 'openrouter-llm',
          status: 'healthy',
          response_time_ms: 150,
          last_check: new Date().toISOString(),
          uptime_percentage: 97.3
        },
        {
          name: 'real-browser',
          status: 'healthy',
          response_time_ms: 250,
          last_check: new Date().toISOString(),
          uptime_percentage: 96.8
        },
        {
          name: 'simple-warp',
          status: 'offline',
          response_time_ms: 0,
          last_check: new Date(Date.now() - 300000).toISOString(),
          uptime_percentage: 85.4,
          error_message: 'Connection timeout'
        }
      ];
      setServers(mockServers);
    } finally {
      setLoading(false);
    }
  }, []);

  const getServerTools = useCallback(async (serverName: string) => {
    try {
      const response = await apiClient.getServerTools(serverName);
      return response;
    } catch (err: any) {
      console.error(`Failed to fetch tools for ${serverName}:`, err);
      
      // Fallback to mock data for development
      const mockTools: Record<string, MCPTool[]> = {
        'kiro-tools': [
          { name: 'readFile', description: 'Read file contents' },
          { name: 'writeFile', description: 'Write file contents' },
          { name: 'listDirectory', description: 'List directory contents' },
          { name: 'executeCommand', description: 'Execute shell command' }
        ],
        'groq-llm': [
          { name: 'groq_generate', description: 'Generate text using Groq models' },
          { name: 'groq_chat', description: 'Multi-turn chat conversation' },
          { name: 'groq_code_generation', description: 'Generate code' }
        ],
        'browser-automation': [
          { name: 'launch_browser', description: 'Launch browser instance' },
          { name: 'navigate_to', description: 'Navigate to URL' },
          { name: 'click_element', description: 'Click on element' },
          { name: 'type_text', description: 'Type text into element' },
          { name: 'take_screenshot', description: 'Take screenshot' }
        ],
        'deep-research': [
          { name: 'comprehensive_web_research', description: 'Comprehensive web research' },
          { name: 'analyze_research_content', description: 'Analyze research content' },
          { name: 'generate_research_report', description: 'Generate research report' }
        ],
        'api-key-sniffer': [
          { name: 'start_sniffer', description: 'Start API key sniffer' },
          { name: 'stop_sniffer', description: 'Stop API key sniffer' },
          { name: 'list_keys', description: 'List captured API keys' },
          { name: 'analyze_text', description: 'Analyze text for API keys' }
        ],
        'network-analysis': [
          { name: 'get_network_interfaces', description: 'Get network interfaces' },
          { name: 'ping_host', description: 'Ping a host' },
          { name: 'port_scan', description: 'Scan ports' },
          { name: 'traceroute', description: 'Trace route to destination' }
        ],
        'enhanced-filesystem': [
          { name: 'read_file', description: 'Read file contents' },
          { name: 'write_file', description: 'Write content to file' },
          { name: 'list_directory', description: 'List directory contents' },
          { name: 'search_files', description: 'Search for files by pattern' }
        ],
        'enhanced-git': [
          { name: 'git_status', description: 'Get git repository status' },
          { name: 'git_diff', description: 'Show git diff' },
          { name: 'git_log', description: 'Show git commit history' },
          { name: 'git_add', description: 'Add files to staging area' }
        ],
        'openrouter-llm': [
          { name: 'openrouter_generate', description: 'Generate text using OpenRouter' },
          { name: 'openrouter_chat', description: 'Multi-turn chat conversation' },
          { name: 'openrouter_list_models', description: 'List available models' }
        ],
        'real-browser': [
          { name: 'launch_real_browser', description: 'Launch real browser' },
          { name: 'real_navigate', description: 'Navigate to URL' },
          { name: 'real_click', description: 'Click on element' },
          { name: 'real_screenshot', description: 'Take screenshot' }
        ],
        'simple-warp': [
          { name: 'launch_warp', description: 'Launch Warp terminal' },
          { name: 'execute_command', description: 'Execute secure command' }
        ]
      };
      
      return mockTools[serverName] || [];
    }
  }, []);

  const loadAllTools = useCallback(async () => {
    const toolsData: Record<string, MCPTool[]> = {};
    
    for (const server of servers) {
      try {
        const serverTools = await getServerTools(server.name);
        toolsData[server.name] = serverTools;
      } catch (err) {
        console.error(`Failed to load tools for ${server.name}:`, err);
        toolsData[server.name] = [];
      }
    }
    
    setTools(toolsData);
  }, [servers, getServerTools]);

  const restartServer = useCallback(async (serverName: string) => {
    try {
      await apiClient.restartServer(serverName);
      await refreshServers(); // Refresh server status
      return true;
    } catch (err: any) {
      console.error(`Failed to restart ${serverName}:`, err);
      throw err;
    }
  }, [refreshServers]);

  const getServerMetrics = useCallback(async () => {
    try {
      const response = { data: { success: true, data: {} } }; // Mock for now
      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error('Failed to fetch server metrics');
      }
    } catch (err: any) {
      console.error('Failed to fetch server metrics:', err);
      throw err;
    }
  }, []);

  const executeTool = useCallback(async (serverName: string, toolName: string, args: any) => {
    try {
      const response = await apiClient.executeTool(serverName, toolName, args);
      return response;
    } catch (err: any) {
      console.error(`Failed to execute ${toolName} on ${serverName}:`, err);
      throw err;
    }
  }, []);

  // Load servers and tools on mount
  useEffect(() => {
    refreshServers();
  }, [refreshServers]);

  // Load tools when servers change
  useEffect(() => {
    if (servers.length > 0) {
      loadAllTools();
    }
  }, [servers, loadAllTools]);

  return {
    servers,
    tools,
    loading,
    error,
    refreshServers,
    getServerTools,
    loadAllTools,
    restartServer,
    getServerMetrics,
    executeTool
  };
};