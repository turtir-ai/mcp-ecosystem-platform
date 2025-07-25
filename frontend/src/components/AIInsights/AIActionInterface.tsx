/**
 * AI Action Interface - Handles AI action approval, execution and tracking
 * 
 * Bu component, AI'ın önerdiği eylemlerin onaylanması, yürütülmesi ve takip edilmesi için kullanılır.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  TextField,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  PlayArrow as ExecuteIcon,
  Pause as PauseIcon,
  CheckCircle as CompleteIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Schedule as PendingIcon,
  ExpandMore as ExpandMoreIcon,
  Security as SecurityIcon,
  Speed as PerformanceIcon,
  Build as MaintenanceIcon,
  Analytics as DiagnosticsIcon
} from '@mui/icons-material';
import apiService from '../../services/api';

interface PendingAction {
  id: string;
  title: string;
  description: string;
  action_type: string;
  risk_level: string;
  estimated_duration: string;
  created_at: string;
  parameters: Record<string, any>;
}

interface ActionStatus {
  id: string;
  status: 'pending' | 'executing' | 'completed' | 'failed' | 'cancelled';
  title?: string;
  started_at?: string;
  completed_at?: string;
  result?: Record<string, any>;
  validation?: Record<string, any>;
}

interface AIActionInterfaceProps {
  onActionUpdate?: (actionId: string, status: string) => void;
}

export const AIActionInterface: React.FC<AIActionInterfaceProps> = ({ onActionUpdate }) => {
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([]);
  const [actionStatuses, setActionStatuses] = useState<Record<string, ActionStatus>>({});
  const [selectedAction, setSelectedAction] = useState<PendingAction | null>(null);
  const [approvalDialog, setApprovalDialog] = useState(false);
  const [approvalReason, setApprovalReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPendingActions = async () => {
    try {
      const response = await apiService.get<PendingAction[]>('/orchestrator/actions/pending');
      setPendingActions(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pending actions');
    }
  };

  const fetchActionStatus = async (actionId: string) => {
    try {
      const response = await apiService.get<ActionStatus>(`/orchestrator/actions/${actionId}/status`);
      setActionStatuses(prev => ({
        ...prev,
        [actionId]: response
      }));
      
      if (onActionUpdate) {
        onActionUpdate(actionId, response.status);
      }
    } catch (err) {
      console.error(`Failed to fetch status for action ${actionId}:`, err);
    }
  };

  useEffect(() => {
    fetchPendingActions();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchPendingActions, 30000);
    return () => clearInterval(interval);
  }, []);

  // Poll action statuses for executing actions
  useEffect(() => {
    const executingActions = Object.entries(actionStatuses)
      .filter(([_, status]) => status.status === 'executing')
      .map(([id]) => id);

    if (executingActions.length > 0) {
      const statusInterval = setInterval(() => {
        executingActions.forEach(fetchActionStatus);
      }, 5000);
      
      return () => clearInterval(statusInterval);
    }
  }, [actionStatuses]);

  const handleApproveAction = async (action: PendingAction) => {
    setSelectedAction(action);
    setApprovalDialog(true);
  };

  const confirmApproval = async () => {
    if (!selectedAction) return;

    try {
      setLoading(true);
      await apiService.post(`/orchestrator/actions/${selectedAction.id}/approve`, {
        user_id: 'user',
        reason: approvalReason
      });
      
      // Start tracking this action
      setActionStatuses(prev => ({
        ...prev,
        [selectedAction.id]: {
          id: selectedAction.id,
          status: 'executing',
          title: selectedAction.title
        }
      }));
      
      // Remove from pending actions
      setPendingActions(prev => prev.filter(a => a.id !== selectedAction.id));
      
      setApprovalDialog(false);
      setSelectedAction(null);
      setApprovalReason('');
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve action');
    } finally {
      setLoading(false);
    }
  };

  const handleRejectAction = async (actionId: string, reason: string = '') => {
    try {
      setLoading(true);
      await apiService.post(`/orchestrator/actions/${actionId}/reject`, {
        reason
      });
      
      setPendingActions(prev => prev.filter(a => a.id !== actionId));
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject action');
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'mcp_server_restart':
        return <MaintenanceIcon />;
      case 'performance_optimization':
        return <PerformanceIcon />;
      case 'diagnostic_analysis':
        return <DiagnosticsIcon />;
      case 'system_cleanup':
        return <MaintenanceIcon />;
      default:
        return <ExecuteIcon />;
    }
  };

  const getRiskColor = (riskLevel: string): 'success' | 'warning' | 'error' => {
    switch (riskLevel.toLowerCase()) {
      case 'low':
      case 'safe':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
      case 'critical':
        return 'error';
      default:
        return 'warning';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <PendingIcon color="warning" />;
      case 'executing':
        return <ExecuteIcon color="primary" />;
      case 'completed':
        return <CompleteIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'cancelled':
        return <PauseIcon color="disabled" />;
      default:
        return <PendingIcon />;
    }
  };

  const formatActionType = (actionType: string) => {
    return actionType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Pending Actions */}
      {pendingActions.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <SecurityIcon color="warning" />
              <Typography variant="h6">
                Pending AI Actions ({pendingActions.length})
              </Typography>
              <Chip 
                label="Approval Required" 
                color="warning" 
                size="small"
              />
            </Box>

            {pendingActions.map((action) => (
              <Accordion key={action.id} sx={{ mb: 1 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center" gap={2} width="100%">
                    {getActionIcon(action.action_type)}
                    
                    <Box flex={1}>
                      <Typography variant="subtitle1" fontWeight="medium">
                        {action.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatActionType(action.action_type)} • {action.estimated_duration}
                      </Typography>
                    </Box>
                    
                    <Chip
                      label={`Risk: ${action.risk_level}`}
                      color={getRiskColor(action.risk_level)}
                      size="small"
                    />
                  </Box>
                </AccordionSummary>
                
                <AccordionDetails>
                  <Box>
                    <Typography variant="body2" paragraph>
                      {action.description}
                    </Typography>
                    
                    {Object.keys(action.parameters).length > 0 && (
                      <Box mb={2}>
                        <Typography variant="subtitle2" gutterBottom>
                          Parameters:
                        </Typography>
                        <Box component="pre" sx={{ 
                          fontSize: '0.75rem', 
                          backgroundColor: 'grey.100', 
                          p: 1, 
                          borderRadius: 1,
                          overflow: 'auto'
                        }}>
                          {JSON.stringify(action.parameters, null, 2)}
                        </Box>
                      </Box>
                    )}
                    
                    <Box display="flex" gap={1} justifyContent="flex-end">
                      <Button
                        variant="outlined"
                        color="error"
                        onClick={() => handleRejectAction(action.id, 'User rejected')}
                        disabled={loading}
                      >
                        Reject
                      </Button>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={() => handleApproveAction(action)}
                        disabled={loading}
                      >
                        Approve & Execute
                      </Button>
                    </Box>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Active/Recent Actions */}
      {Object.keys(actionStatuses).length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Action Status
            </Typography>

            <List>
              {Object.entries(actionStatuses).map(([actionId, status]) => (
                <React.Fragment key={actionId}>
                  <ListItem>
                    <ListItemIcon>
                      {getStatusIcon(status.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={status.title || actionId}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Status: {status.status}
                          </Typography>
                          {status.started_at && (
                            <Typography variant="caption" color="text.secondary">
                              Started: {new Date(status.started_at).toLocaleString()}
                            </Typography>
                          )}
                          {status.completed_at && (
                            <Typography variant="caption" color="text.secondary">
                              Completed: {new Date(status.completed_at).toLocaleString()}
                            </Typography>
                          )}
                          {status.status === 'executing' && (
                            <LinearProgress sx={{ mt: 1 }} />
                          )}
                        </Box>
                      }
                    />
                    {status.result && (
                      <Button
                        size="small"
                        onClick={() => {
                          // Show result details
                          console.log('Action result:', status.result);
                        }}
                      >
                        View Result
                      </Button>
                    )}
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* No actions message */}
      {pendingActions.length === 0 && Object.keys(actionStatuses).length === 0 && (
        <Alert severity="info">
          No AI actions pending or in progress.
        </Alert>
      )}

      {/* Approval Dialog */}
      <Dialog 
        open={approvalDialog} 
        onClose={() => setApprovalDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Approve AI Action
        </DialogTitle>
        <DialogContent>
          {selectedAction && (
            <Box>
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  You are about to approve an AI action with {selectedAction.risk_level} risk level.
                </Typography>
                <Typography variant="body2">
                  Please review the details carefully before proceeding.
                </Typography>
              </Alert>

              <Box mb={2}>
                <Typography variant="h6" gutterBottom>
                  {selectedAction.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {selectedAction.description}
                </Typography>
                
                <Box display="flex" gap={1} mb={2}>
                  <Chip 
                    label={formatActionType(selectedAction.action_type)} 
                    variant="outlined" 
                  />
                  <Chip 
                    label={`Risk: ${selectedAction.risk_level}`}
                    color={getRiskColor(selectedAction.risk_level)}
                  />
                  <Chip 
                    label={`Duration: ${selectedAction.estimated_duration}`}
                    variant="outlined"
                  />
                </Box>
              </Box>

              <TextField
                fullWidth
                multiline
                rows={3}
                label="Approval Reason (Optional)"
                value={approvalReason}
                onChange={(e) => setApprovalReason(e.target.value)}
                placeholder="Why are you approving this action?"
                sx={{ mb: 2 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setApprovalDialog(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button 
            onClick={confirmApproval}
            variant="contained"
            color="primary"
            disabled={loading}
          >
            {loading ? 'Approving...' : 'Approve & Execute'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIActionInterface;