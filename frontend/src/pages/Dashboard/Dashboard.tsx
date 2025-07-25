/**
 * Main dashboard page with system overview
 */
import {
    CheckCircle as CheckCircleIcon,
    NetworkCheck as NetworkIcon,
    Security as SecurityIcon,
    Storage as StorageIcon
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Grid,
    LinearProgress,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Typography
} from '@mui/material';
import React from 'react';
import { CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import useSWR from 'swr';

import apiClient, { MCPServerStatus } from '../../services/api';
import { getStatusColor } from '../../theme/theme';

const Dashboard: React.FC = () => {
  // Fetch dashboard data
  const { data: mcpServers = [], isLoading: mcpLoading } = useSWR(
    '/mcp-status',
    () => apiClient.getMCPStatus(),
    { refreshInterval: 30000 }
  );

  const { data: networkStatus, isLoading: networkLoading } = useSWR(
    '/network-status',
    () => apiClient.getNetworkStatus(),
    { refreshInterval: 60000 }
  );

  const { data: securitySummary, isLoading: securityLoading } = useSWR(
    '/security-summary',
    () => apiClient.getSecuritySummary(),
    { refreshInterval: 60000 }
  );

  const { data: diagnosticReport, isLoading: diagnosticLoading } = useSWR(
    '/diagnostic-report',
    () => apiClient.getDiagnosticReport(),
    { refreshInterval: 300000 } // 5 minutes
  );

  // Calculate MCP server statistics
  const mcpStats = {
    total: Array.isArray(mcpServers) ? mcpServers.length : 0,
    healthy: Array.isArray(mcpServers) ? mcpServers.filter((s: MCPServerStatus) => s.status === 'healthy').length : 0,
    degraded: Array.isArray(mcpServers) ? mcpServers.filter((s: MCPServerStatus) => s.status === 'degraded').length : 0,
    unhealthy: Array.isArray(mcpServers) ? mcpServers.filter((s: MCPServerStatus) => s.status === 'unhealthy').length : 0,
    offline: Array.isArray(mcpServers) ? mcpServers.filter((s: MCPServerStatus) => s.status === 'offline').length : 0,
  };

  // Mock data for charts (in real app, this would come from API)
  const performanceData = [
    { time: '00:00', latency: 45, throughput: 85 },
    { time: '04:00', latency: 52, throughput: 78 },
    { time: '08:00', latency: 38, throughput: 92 },
    { time: '12:00', latency: 41, throughput: 88 },
    { time: '16:00', latency: 47, throughput: 85 },
    { time: '20:00', latency: 43, throughput: 90 },
  ];

  const serverStatusData = [
    { name: 'Healthy', value: mcpStats.healthy, color: getStatusColor('healthy') },
    { name: 'Degraded', value: mcpStats.degraded, color: getStatusColor('degraded') },
    { name: 'Unhealthy', value: mcpStats.unhealthy, color: getStatusColor('unhealthy') },
    { name: 'Offline', value: mcpStats.offline, color: getStatusColor('offline') },
  ].filter(item => item.value > 0);

  const getHealthScoreColor = (score: number) => {
    if (score >= 90) return 'success.main';
    if (score >= 70) return 'warning.main';
    return 'error.main';
  };

  const getHealthScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    return 'Poor';
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        System Dashboard
      </Typography>

      {/* System Health Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health Score
              </Typography>
              {diagnosticLoading ? (
                <LinearProgress />
              ) : diagnosticReport ? (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h3" sx={{ color: getHealthScoreColor(diagnosticReport.overall_health_score) }}>
                      {diagnosticReport.overall_health_score.toFixed(0)}
                    </Typography>
                    <Typography variant="h5" sx={{ ml: 1, color: 'text.secondary' }}>
                      / 100
                    </Typography>
                    <Chip
                      label={getHealthScoreLabel(diagnosticReport.overall_health_score)}
                      color={diagnosticReport.overall_health_score >= 70 ? 'success' : 'warning'}
                      sx={{ ml: 2 }}
                    />
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={diagnosticReport.overall_health_score}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getHealthScoreColor(diagnosticReport.overall_health_score),
                      },
                    }}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {diagnosticReport.executive_summary}
                  </Typography>
                </Box>
              ) : (
                <Alert severity="warning">Unable to load system health data</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Stats
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <StorageIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="MCP Servers"
                    secondary={`${mcpStats.healthy}/${mcpStats.total} healthy`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <NetworkIcon color={networkStatus?.overall_status === 'excellent' ? 'success' : 'warning'} />
                  </ListItemIcon>
                  <ListItemText
                    primary="Network Status"
                    secondary={networkStatus?.overall_status || 'Loading...'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <SecurityIcon color={securitySummary?.critical_threats > 0 ? 'error' : 'success'} />
                  </ListItemIcon>
                  <ListItemText
                    primary="Security Threats"
                    secondary={`${securitySummary?.total_active_threats || 0} active`}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Network Performance (24h)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="latency"
                    stroke="#f44336"
                    strokeWidth={2}
                    name="Latency (ms)"
                  />
                  <Line
                    type="monotone"
                    dataKey="throughput"
                    stroke="#4caf50"
                    strokeWidth={2}
                    name="Throughput (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Server Status Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={serverStatusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {serverStatusData.map((entry: { name: string; value: number; color: string }, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <Box sx={{ mt: 2 }}>
                {serverStatusData.map((item: { name: string; value: number; color: string }, index: number) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        backgroundColor: item.color,
                        borderRadius: '50%',
                        mr: 1,
                      }}
                    />
                    <Typography variant="body2">
                      {item.name}: {item.value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts and Recommendations */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Alerts
              </Typography>
              {securitySummary?.critical_threats > 0 && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    {securitySummary.critical_threats} critical security threats detected
                  </Typography>
                </Alert>
              )}
              {mcpStats.offline > 0 && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    {mcpStats.offline} MCP servers are offline
                  </Typography>
                </Alert>
              )}
              {networkStatus?.overall_status === 'poor' && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    Network performance is degraded
                  </Typography>
                </Alert>
              )}
              {!securitySummary?.critical_threats && !mcpStats.offline && networkStatus?.overall_status !== 'poor' && (
                <Alert severity="success">
                  <Typography variant="body2">
                    All systems are operating normally
                  </Typography>
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recommendations
              </Typography>
              {diagnosticReport?.immediate_actions ? (
                <List dense>
                  {diagnosticReport.immediate_actions.slice(0, 3).map((action: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckCircleIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={action}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No immediate actions required
                </Typography>
              )}
              <Button variant="outlined" size="small" sx={{ mt: 2 }}>
                View All Recommendations
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;