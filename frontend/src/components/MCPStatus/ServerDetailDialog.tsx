import {
    Build,
    CheckCircle,
    Error,
    OfflinePin,
    Schedule,
    Speed,
    Warning,
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    Grid,
    LinearProgress,
    List,
    ListItem,
    ListItemText,
    Typography,
} from '@mui/material';
import { format } from 'date-fns';
import React from 'react';
import useSWR from 'swr';

import apiClient from '../../services/api';

interface ServerTool {
  name: string;
  description: string;
  parameters?: Record<string, any>;
}

interface ServerActivity {
  timestamp: string;
  tool_name: string;
  duration_ms: number;
  status: 'success' | 'error';
  error_message?: string;
}

interface ServerDetails {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'offline';
  response_time_ms: number;
  last_check: string;
  error_message?: string;
  uptime_percentage: number;
  tools: ServerTool[];
  recent_activity: ServerActivity[];
  config: {
    command: string;
    args: string[];
    timeout: number;
    retry_count: number;
  };
  metrics: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    average_response_time: number;
  };
}

interface ServerDetailDialogProps {
  serverName: string | null;
  open: boolean;
  onClose: () => void;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'healthy':
      return <CheckCircle color="success" />;
    case 'degraded':
      return <Warning color="warning" />;
    case 'unhealthy':
      return <Error color="error" />;
    case 'offline':
      return <OfflinePin color="disabled" />;
    default:
      return null;
  }
};

const getStatusChipColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'success';
    case 'degraded':
      return 'warning';
    case 'unhealthy':
      return 'error';
    case 'offline':
      return 'default';
    default:
      return 'info';
  }
};

const ServerDetailDialog: React.FC<ServerDetailDialogProps> = ({
  serverName,
  open,
  onClose,
}) => {
  const { data: serverDetails, error, isLoading } = useSWR(
    serverName ? `/mcp-servers/${serverName}` : null,
    () => serverName ? apiClient.getServerStatus(serverName) : null,
    {
      revalidateOnFocus: false,
    }
  );

  if (!serverName) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {serverDetails && getStatusIcon(serverDetails.status)}
          <Typography variant="h6">{serverName}</Typography>
          {serverDetails && (
            <Chip
              label={serverDetails.status.toUpperCase()}
              color={getStatusChipColor(serverDetails.status) as any}
              size="small"
              variant="outlined"
            />
          )}
        </Box>
      </DialogTitle>

      <DialogContent>
        {isLoading && (
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress />
            <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
              Loading server details...
            </Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load server details: {error.message}
          </Alert>
        )}

        {serverDetails && (
          <Box>
            {/* Server Status Overview */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Speed color="primary" sx={{ fontSize: 32, mb: 1 }} />
                    <Typography variant="h6">
                      {serverDetails.response_time_ms.toFixed(0)}ms
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Response Time
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <CheckCircle color="success" sx={{ fontSize: 32, mb: 1 }} />
                    <Typography variant="h6">
                      {serverDetails.uptime_percentage?.toFixed(1) || '0'}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Uptime
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Build color="info" sx={{ fontSize: 32, mb: 1 }} />
                    <Typography variant="h6">
                      {serverDetails.tools?.length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Available Tools
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Schedule color="warning" sx={{ fontSize: 32, mb: 1 }} />
                    <Typography variant="h6">
                      {format(new Date(serverDetails.last_check), 'HH:mm')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Last Check
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Error Message */}
            {serverDetails.error_message && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {serverDetails.error_message}
              </Alert>
            )}

            {/* Performance Metrics */}
            <Typography variant="h6" sx={{ mb: 2 }}>
              Performance Metrics
            </Typography>
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Total Requests
                </Typography>
                <Typography variant="h6">
                  {serverDetails.metrics?.total_requests?.toLocaleString() || '0'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Success Rate
                </Typography>
                <Typography variant="h6" color="success.main">
                  {(serverDetails.metrics?.total_requests || 0) > 0 
                    ? (((serverDetails.metrics?.successful_requests || 0) / (serverDetails.metrics?.total_requests || 1)) * 100).toFixed(1)
                    : '0'}%
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Avg Response Time
                </Typography>
                <Typography variant="h6">
                  {serverDetails.metrics?.average_response_time?.toFixed(0) || '0'}ms
                </Typography>
              </Grid>
            </Grid>

            <Divider sx={{ my: 2 }} />

            {/* Available Tools */}
            <Typography variant="h6" sx={{ mb: 2 }}>
              Available Tools ({serverDetails.tools?.length || 0})
            </Typography>
            <List dense>
              {(serverDetails.tools || []).map((tool: any, index: number) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={tool.name}
                    secondary={tool.description}
                  />
                </ListItem>
              ))}
            </List>

            <Divider sx={{ my: 2 }} />

            {/* Recent Activity */}
            <Typography variant="h6" sx={{ mb: 2 }}>
              Recent Activity
            </Typography>
            <List dense>
              {(serverDetails.recent_activity || []).slice(0, 5).map((activity: any, index: number) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2">
                          {activity.tool_name}
                        </Typography>
                        <Chip
                          label={activity.status}
                          color={activity.status === 'success' ? 'success' : 'error'}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {format(new Date(activity.timestamp), 'MMM dd, HH:mm:ss')} • {activity.duration_ms}ms
                        </Typography>
                        {activity.error_message && (
                          <Typography variant="caption" color="error" display="block">
                            {activity.error_message}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              )) || []}
            </List>

            {(!serverDetails.recent_activity || serverDetails.recent_activity.length === 0) && (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                No recent activity
              </Typography>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ServerDetailDialog;