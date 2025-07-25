/**
 * MCP Servers status dashboard page
 */
import {
    Error as ErrorIcon,
    CheckCircle as HealthyIcon,
    Info as InfoIcon,
    OfflineBolt as OfflineIcon,
    Refresh as RefreshIcon,
    Warning as WarningIcon
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Grid,
    List,
    ListItem,
    ListItemText,
    Typography
} from '@mui/material';
import React, { useState } from 'react';
import useSWR from 'swr';

import MCPStatusTable from '../../components/MCPStatus/MCPStatusTable';

import ServerDetailDialog from '../../components/MCPStatus/ServerDetailDialog';
import apiClient from '../../services/api';
import { getStatusColor } from '../../theme/theme';

const MCPServers: React.FC = () => {
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [toolsDialogOpen, setToolsDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  // Fetch MCP servers status
  const {
    data: servers = [],
    error,
    isLoading,
    mutate: refetch,
  } = useSWR('/mcp-status', () => apiClient.getMCPStatus(), {
    refreshInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch tools for selected server
  const {
    data: serverTools = [],
    isLoading: toolsLoading,
  } = useSWR(
    selectedServer ? `/mcp-tools/${selectedServer}` : null,
    () => selectedServer ? apiClient.getServerTools(selectedServer) : Promise.resolve([]),
    {
      revalidateOnFocus: false,
    }
  );

  // Restart server function
  const handleRestartServer = async (serverName: string) => {
    if (window.confirm(`Are you sure you want to restart ${serverName}?`)) {
      try {
        await apiClient.restartServer(serverName);
        console.log(`Server ${serverName} restarted successfully`);
        refetch(); // Refresh the server list
      } catch (error: any) {
        console.error(`Failed to restart ${serverName}:`, error.message);
      }
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <HealthyIcon sx={{ color: getStatusColor('healthy') }} />;
      case 'degraded':
        return <WarningIcon sx={{ color: getStatusColor('degraded') }} />;
      case 'unhealthy':
        return <ErrorIcon sx={{ color: getStatusColor('unhealthy') }} />;
      case 'offline':
        return <OfflineIcon sx={{ color: getStatusColor('offline') }} />;
      default:
        return <InfoIcon />;
    }
  };

  const getStatusChipColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
      case 'offline':
        return 'error';
      default:
        return 'default';
    }
  };



  const handleViewTools = (serverName: string) => {
    setSelectedServer(serverName);
    setToolsDialogOpen(true);
  };

  const handleCloseToolsDialog = () => {
    setToolsDialogOpen(false);
    setSelectedServer(null);
  };

  const handleViewDetails = (serverName: string) => {
    setSelectedServer(serverName);
    setDetailDialogOpen(true);
  };

  const handleCloseDetailDialog = () => {
    setDetailDialogOpen(false);
    setSelectedServer(null);
  };

  // Calculate summary statistics
  const healthyCount = servers.filter(s => s.status === 'healthy').length;
  const degradedCount = servers.filter(s => s.status === 'degraded').length;
  const unhealthyCount = servers.filter(s => s.status === 'unhealthy').length;
  const offlineCount = servers.filter(s => s.status === 'offline').length;
  const totalCount = servers.length;

  const averageResponseTime = servers.length > 0 
    ? servers.reduce((sum, server) => sum + (server.response_time_ms || 0), 0) / servers.length
    : 0;

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load MCP servers: {(error as Error).message}
        <Button onClick={() => refetch()} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          MCP Servers
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="overline">
                    Total Servers
                  </Typography>
                  <Typography variant="h4">
                    {totalCount}
                  </Typography>
                </Box>
                <HealthyIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="overline">
                    Healthy
                  </Typography>
                  <Typography variant="h4" sx={{ color: getStatusColor('healthy') }}>
                    {healthyCount}
                  </Typography>
                </Box>
                <HealthyIcon sx={{ fontSize: 40, color: getStatusColor('healthy') }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="overline">
                    Issues
                  </Typography>
                  <Typography variant="h4" sx={{ color: getStatusColor('unhealthy') }}>
                    {degradedCount + unhealthyCount + offlineCount}
                  </Typography>
                </Box>
                <ErrorIcon sx={{ fontSize: 40, color: getStatusColor('unhealthy') }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="overline">
                    Avg Response Time
                  </Typography>
                  <Typography variant="h4">
                    {averageResponseTime.toFixed(0)}ms
                  </Typography>
                </Box>
                <InfoIcon sx={{ fontSize: 40, color: 'info.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Health Alert */}
      {servers && (
        <Alert 
          severity={healthyCount === totalCount && totalCount > 0 ? 'success' : 'warning'} 
          sx={{ mb: 3 }}
        >
          {healthyCount === totalCount && totalCount > 0
            ? `System Healthy - All ${totalCount} MCP servers are running normally.`
            : `System Issues Detected - ${totalCount - healthyCount} of ${totalCount} servers need attention.`
          }
        </Alert>
      )}

      {/* MCP Status Table */}
      <Card>
        <CardContent>
          <MCPStatusTable 
            onServerClick={handleViewDetails}
            onRefresh={() => refetch()}
          />
        </CardContent>
      </Card>

      {/* Tools Dialog */}
      <Dialog
        open={toolsDialogOpen}
        onClose={handleCloseToolsDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Available Tools - {selectedServer}
        </DialogTitle>
        <DialogContent>
          {toolsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <List>
              {serverTools.map((tool, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={tool.name || `Tool ${index + 1}`}
                    secondary={tool.description || 'No description available'}
                  />
                </ListItem>
              ))}
              {serverTools.length === 0 && (
                <ListItem>
                  <ListItemText
                    primary="No tools available"
                    secondary="This server doesn't expose any tools"
                  />
                </ListItem>
              )}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseToolsDialog}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Server Detail Dialog */}
      <ServerDetailDialog
        serverName={selectedServer}
        open={detailDialogOpen}
        onClose={handleCloseDetailDialog}
      />
    </Box>
  );
};

export default MCPServers;