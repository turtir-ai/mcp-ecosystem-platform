/**
 * AI Action Suggestion Panel Component
 * Shows AI-generated suggestions with approval workflow
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  AlertTitle,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  CircularProgress,
  Snackbar
} from '@mui/material';
import {
  SmartToy as AIIcon,
  Security as SecurityIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { ActionableInsight, AIActionResponse } from '../../types/health';

interface ActionSuggestionPanelProps {
  insights: ActionableInsight[];
  onInsightExecuted?: (insight: ActionableInsight, success: boolean) => void;
}

const ActionSuggestionPanel: React.FC<ActionSuggestionPanelProps> = ({
  insights,
  onInsightExecuted
}) => {
  const [approvalDialog, setApprovalDialog] = useState<{
    open: boolean;
    insight: ActionableInsight | null;
    approvalData: any;
  }>({
    open: false,
    insight: null,
    approvalData: null
  });
  
  const [executing, setExecuting] = useState<string | null>(null);
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });

  const handleExecuteAction = async (insight: ActionableInsight) => {
    if (!insight.suggested_action || !insight.server_name) return;

    setExecuting(insight.server_name);

    try {
      const response = await fetch(`/api/v1/ai/mcp/restart/${insight.server_name}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reasoning: `AI-initiated restart based on insight: ${insight.message}`
        })
      });

      const result: AIActionResponse = await response.json();
      
      if (result.success) {
        setNotification({
          open: true,
          message: `Successfully restarted ${insight.server_name}`,
          severity: 'success'
        });
        onInsightExecuted?.(insight, true);
      } else if (result.data?.approval_required) {
        // Show approval dialog
        setApprovalDialog({
          open: true,
          insight,
          approvalData: result.data
        });
      } else {
        throw new Error(result.error || 'Action failed');
      }
    } catch (error) {
      setNotification({
        open: true,
        message: `Failed to execute action: ${error instanceof Error ? error.message : 'Unknown error'}`,
        severity: 'error'
      });
      onInsightExecuted?.(insight, false);
    } finally {
      setExecuting(null);
    }
  };

  const handleApprovalSubmit = async (approved: boolean) => {
    if (!approvalDialog.insight || !approvalDialog.approvalData) return;

    const { approval_request } = approvalDialog.approvalData;
    
    try {
      const endpoint = approved 
        ? `/api/v1/security/approve/${approval_request.operation_id}`
        : `/api/v1/security/reject/${approval_request.operation_id}`;
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'frontend_user',
          reason: approved ? 'User approved AI action' : 'User rejected AI action'
        })
      });

      const result = await response.json();
      
      if (result.success && approved) {
        // If approved, execute the original action
        await handleExecuteAction(approvalDialog.insight);
      }
      
      setNotification({
        open: true,
        message: approved ? 'Action approved and executed' : 'Action rejected',
        severity: approved ? 'success' : 'info'
      });
      
    } catch (error) {
      setNotification({
        open: true,
        message: `Approval failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        severity: 'error'
      });
    } finally {
      setApprovalDialog({ open: false, insight: null, approvalData: null });
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'high':
      case 'critical':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getInsightSeverity = (type: string) => {
    switch (type) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  if (!insights.length) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="center" p={2}>
            <AIIcon sx={{ mr: 1, color: 'text.secondary' }} />
            <Typography variant="body2" color="textSecondary">
              No AI insights available
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <AIIcon sx={{ mr: 1 }} />
            AI Insights & Recommendations
          </Typography>
          
          {insights.map((insight, index) => (
            <Alert
              key={index}
              severity={getInsightSeverity(insight.type)}
              sx={{ mb: 2 }}
              action={
                insight.suggested_action && insight.can_auto_fix ? (
                  <Box display="flex" alignItems="center" gap={1}>
                    <Chip
                      label={`Risk: ${insight.risk_level}`}
                      color={getRiskLevelColor(insight.risk_level) as any}
                      size="small"
                    />
                    <Button
                      color="inherit"
                      size="small"
                      onClick={() => handleExecuteAction(insight)}
                      disabled={executing === insight.server_name}
                      startIcon={executing === insight.server_name ? <CircularProgress size={16} /> : <AIIcon />}
                    >
                      {executing === insight.server_name ? 'Executing...' : 'AI Fix'}
                    </Button>
                  </Box>
                ) : !insight.suggested_action ? (
                  <Chip
                    label="Manual Action Required"
                    color="warning"
                    size="small"
                  />
                ) : null
              }
            >
              <AlertTitle>
                {insight.message}
                {insight.server_name && (
                  <Chip
                    label={insight.server_name}
                    size="small"
                    variant="outlined"
                    sx={{ ml: 1 }}
                  />
                )}
              </AlertTitle>
              {insight.reasoning && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  <strong>AI Analysis:</strong> {insight.reasoning}
                </Typography>
              )}
            </Alert>
          ))}
        </CardContent>
      </Card>

      {/* Approval Dialog */}
      <Dialog
        open={approvalDialog.open}
        onClose={() => setApprovalDialog({ open: false, insight: null, approvalData: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <SecurityIcon sx={{ mr: 1 }} />
          AI Action Approval Required
        </DialogTitle>
        <DialogContent>
          {approvalDialog.approvalData && (
            <>
              <Alert severity="warning" sx={{ mb: 2 }}>
                <AlertTitle>High Risk Operation</AlertTitle>
                This AI action requires your approval due to security policies.
              </Alert>
              
              <DialogContentText component="div">
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Action:</strong> {approvalDialog.approvalData.approval_request?.operation_type}
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Target:</strong> {approvalDialog.insight?.server_name}
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Risk Level:</strong> 
                  <Chip
                    label={approvalDialog.approvalData.risk_level}
                    color={getRiskLevelColor(approvalDialog.approvalData.risk_level) as any}
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Reason:</strong> {approvalDialog.approvalData.reason}
                </Typography>
                {approvalDialog.approvalData.approval_request?.ai_reasoning && (
                  <Typography variant="subtitle2" gutterBottom>
                    <strong>AI Reasoning:</strong> {approvalDialog.approvalData.approval_request.ai_reasoning}
                  </Typography>
                )}
              </DialogContentText>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => handleApprovalSubmit(false)}
            color="error"
            startIcon={<WarningIcon />}
          >
            Reject
          </Button>
          <Button
            onClick={() => handleApprovalSubmit(true)}
            color="primary"
            variant="contained"
            startIcon={<AIIcon />}
          >
            Approve & Execute
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
        message={notification.message}
      />
    </>
  );
};

export default ActionSuggestionPanel;