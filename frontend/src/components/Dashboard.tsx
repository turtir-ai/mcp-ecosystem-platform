import {
    CheckCircle,
    Code,
    Error,
    Refresh,
    Security,
    Speed,
    Warning,
    Web
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Grid,
    LinearProgress,
    Paper,
    Typography
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import { SystemStatusCard } from './SystemStatus';
import MCPStatusTable from './MCPStatus/MCPStatusTable';
import SmartErrorTest from './SmartErrorTest';
import AIInsightsPanel from './AIInsights/AIInsightsPanel';
import AIActionInterface from './AIInsights/AIActionInterface';
import AIFeedbackSystem from './AIInsights/AIFeedbackSystem';
import { MCPServerStatus } from '../services/api';

interface MCPStatusData {
  [key: string]: {
    status: 'healthy' | 'degraded' | 'unhealthy' | 'offline';
    response_time_ms: number;
  };
}

const Dashboard: React.FC = () => {
  const [mcpStatus, setMcpStatus] = useState<MCPStatusData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMCPStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/mcp/status');
      const result = await response.json();
      
      if (result.success) {
        setMcpStatus(result.data);
        setError(null);
      } else {
        setError(result.error || 'Failed to fetch MCP status');
      }
    } catch (err) {
      setError('Network error: Unable to connect to backend');
      console.error('Error fetching MCP status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMCPStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchMCPStatus, 30000);
    return () => clearInterval(interval);
  }, []);



  const healthyServers = Object.values(mcpStatus).filter(s => s.status === 'healthy').length;
  const totalServers = Object.keys(mcpStatus).length;
  const overallHealth = totalServers > 0 ? (healthyServers / totalServers) * 100 : 0;

  if (loading && Object.keys(mcpStatus).length === 0) {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
          Loading MCP Ecosystem Platform...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          MCP Ecosystem Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchMCPStatus}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* AI Insights Panel */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <AIInsightsPanel />
        </Grid>
      </Grid>

      {/* AI Action Interface */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <AIActionInterface />
        </Grid>
      </Grid>

      {/* AI Feedback System */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <AIFeedbackSystem />
        </Grid>
      </Grid>

      {/* AI-Enhanced System Status */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} lg={8}>
          <SystemStatusCard onRefresh={fetchMCPStatus} loading={loading} />
        </Grid>
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Legacy Health Overview
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ flexGrow: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={overallHealth}
                  color={overallHealth > 80 ? 'success' : overallHealth > 50 ? 'warning' : 'error'}
                  sx={{ height: 10, borderRadius: 5 }}
                />
              </Box>
              <Typography variant="body1" fontWeight="bold">
                {healthyServers}/{totalServers} Healthy ({Math.round(overallHealth)}%)
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* MCP Servers Detailed Table */}
      <Paper sx={{ mb: 3 }}>
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            MCP Server Details
          </Typography>
        </Box>
        <MCPStatusTable
          servers={Object.entries(mcpStatus).map(([name, status]) => ({
            name,
            status: status.status,
            response_time_ms: status.response_time_ms,
            last_check: new Date().toISOString(),
            uptime_percentage: 95
          }))}
          onRefresh={fetchMCPStatus}
          loading={loading}
        />
      </Paper>

      {/* Smart Error Handler Test */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <SmartErrorTest />
      </Paper>

      {/* Quick Actions */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Grid container spacing={2}>
          <Grid item>
            <Button variant="contained" color="primary">
              Run Smart Git Review
            </Button>
          </Grid>
          <Grid item>
            <Button variant="outlined" color="secondary">
              Create Workflow
            </Button>
          </Grid>
          <Grid item>
            <Button variant="outlined">
              View Analytics
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default Dashboard;