import {
    CheckCircle,
    Error,
    Info,
    Refresh,
    Warning
} from '@mui/icons-material';
import {
    Box,
    Chip,
    IconButton,
    LinearProgress,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Tooltip,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';

interface MCPServerStatus {
  status: string;
  response_time_ms: number;
}

interface MCPStatusData {
  [key: string]: MCPServerStatus;
}

const MCPStatus: React.FC = () => {
  const [mcpStatus, setMcpStatus] = useState<MCPStatusData>({});
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchMCPStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/mcp/status');
      const result = await response.json();
      
      if (result.success) {
        setMcpStatus(result.data);
        setLastUpdated(new Date());
      }
    } catch (err) {
      console.error('Error fetching MCP status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMCPStatus();
    const interval = setInterval(fetchMCPStatus, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle color="success" fontSize="small" />;
      case 'degraded':
        return <Warning color="warning" fontSize="small" />;
      case 'unhealthy':
        return <Error color="error" fontSize="small" />;
      default:
        return <Error color="disabled" fontSize="small" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
        return 'error';
      default:
        return 'default';
    }
  };

  const getResponseTimeColor = (responseTime: number) => {
    if (responseTime < 100) return 'success';
    if (responseTime < 300) return 'warning';
    return 'error';
  };

  const serverDescriptions: { [key: string]: string } = {
    'kiro-tools': 'Kiro IDE integrated tools (filesystem, git, database)',
    'groq-llm': 'Ultra-fast Llama 3.1 8B (30k tokens/minute free)',
    'openrouter-llm': 'Multi-model LLM access (GPT-4, Claude, Llama)',
    'browser-automation': 'Real browser automation (Gemini + Brave)',
    'real-browser': 'No simulation, real browser operations only',
    'deep-research': 'Comprehensive research (Brave Search + Gemini AI)',
    'api-key-sniffer': 'Secure API key detection and masking',
    'network-analysis': 'Real network analysis (ping, port scan, DNS)',
    'enhanced-filesystem': 'Secure file operations',
    'enhanced-git': 'Advanced Git operations',
    'simple-warp': 'Warp terminal integration'
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          MCP Server Status
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {lastUpdated && (
            <Typography variant="body2" color="text.secondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <IconButton onClick={fetchMCPStatus} disabled={loading}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Server Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Response Time</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(mcpStatus).map(([serverName, status]) => (
              <TableRow key={serverName} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStatusIcon(status.status)}
                    <Typography variant="body1" fontWeight="medium">
                      {serverName}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={status.status.toUpperCase()}
                    color={getStatusColor(status.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography
                      variant="body2"
                      color={getResponseTimeColor(status.response_time_ms)}
                    >
                      {status.response_time_ms.toFixed(1)}ms
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min((status.response_time_ms / 500) * 100, 100)}
                      color={getResponseTimeColor(status.response_time_ms) as any}
                      sx={{ width: 60, height: 4 }}
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {serverDescriptions[serverName] || 'MCP Server'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Tooltip title="Server Details">
                    <IconButton size="small">
                      <Info fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {Object.keys(mcpStatus).length === 0 && !loading && (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 2 }}>
          <Typography variant="h6" color="text.secondary">
            No MCP servers found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Make sure the MCP servers are configured and running
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default MCPStatus;