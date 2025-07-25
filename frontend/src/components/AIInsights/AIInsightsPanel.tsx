/**
 * AI Insights Panel - Displays AI-generated system insights and recommendations
 * 
 * Bu component, AI'ın sistem analizi sonuçlarını ve proaktif önerilerini gösterir.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Psychology as AIIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  TrendingUp as TrendIcon,
  AutoFixHigh as AutoFixIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import apiService from '../../services/api';

interface AIInsight {
  id: string;
  type: 'ai_alert' | 'pattern_insight';
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  confidence: number;
  root_cause?: string;
  suggested_actions: Array<{
    title: string;
    description: string;
    risk_level: string;
    estimated_duration: string;
  }>;
  timestamp: string;
  auto_resolve?: boolean;
  pattern_type?: string;
  server_name?: string;
}

interface AIInsightsData {
  insights: AIInsight[];
  total_count: number;
  timestamp: string;
}

export const AIInsightsPanel: React.FC = () => {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiService.get<AIInsightsData>('/ai/insights');
      setInsights(response.insights);
      setLastUpdate(new Date());
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch AI insights');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
    
    // Auto-refresh every 2 minutes
    const interval = setInterval(fetchInsights, 120000);
    return () => clearInterval(interval);
  }, []);

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
        return <InfoIcon color="info" />;
      default:
        return <InfoIcon />;
    }
  };

  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'success' => {
    switch (severity) {
      case 'critical':
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'info';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981'; // Green
    if (confidence >= 0.6) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const handleActionClick = async (insight: AIInsight, action: any) => {
    try {
      // Create an AI action request based on the insight
      const actionRequest = {
        insight_id: insight.id,
        action_title: action.title,
        action_description: action.description,
        risk_level: action.risk_level,
        estimated_duration: action.estimated_duration,
        parameters: {
          server_name: insight.server_name,
          insight_type: insight.type,
          pattern_type: insight.pattern_type
        }
      };
      
      // For now, just log the action - in a real implementation,
      // this would create a pending action in the orchestrator
      console.log('Creating AI action request:', actionRequest);
      
      // Show success message
      // TODO: Add proper notification system
      alert(`Action "${action.title}" has been queued for approval.`);
      
    } catch (err) {
      console.error('Failed to create action request:', err);
      alert('Failed to create action request. Please try again.');
    }
  };

  if (loading && insights.length === 0) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={24} />
            <Typography>Loading AI insights...</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <AIIcon color="primary" />
            <Typography variant="h6">
              AI System Insights
            </Typography>
            <Chip 
              label={`${insights.length} insights`} 
              size="small" 
              color="primary" 
              variant="outlined"
            />
          </Box>
          
          <Box display="flex" alignItems="center" gap={1}>
            {lastUpdate && (
              <Typography variant="caption" color="text.secondary">
                Last updated: {lastUpdate.toLocaleTimeString()}
              </Typography>
            )}
            <Button 
              size="small" 
              onClick={fetchInsights}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {insights.length === 0 ? (
          <Alert severity="success" icon={<SuccessIcon />}>
            <Typography variant="body2">
              🎉 No issues detected! Your system is running smoothly.
            </Typography>
          </Alert>
        ) : (
          <Box>
            {insights.map((insight) => (
              <Accordion key={insight.id} sx={{ mb: 1 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center" gap={2} width="100%">
                    {getSeverityIcon(insight.severity)}
                    
                    <Box flex={1}>
                      <Typography variant="subtitle1" fontWeight="medium">
                        {insight.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {insight.message}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={`${Math.round(insight.confidence * 100)}% confidence`}
                        size="small"
                        style={{
                          backgroundColor: getConfidenceColor(insight.confidence),
                          color: 'white'
                        }}
                      />
                      
                      <Chip
                        label={insight.severity}
                        size="small"
                        color={getSeverityColor(insight.severity)}
                        variant="outlined"
                      />
                      
                      {insight.type === 'pattern_insight' && (
                        <Chip
                          icon={<TrendIcon />}
                          label="Pattern"
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                      )}
                      
                      {insight.auto_resolve && (
                        <Chip
                          icon={<AutoFixIcon />}
                          label="Auto-resolve"
                          size="small"
                          color="success"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </Box>
                </AccordionSummary>
                
                <AccordionDetails>
                  <Box>
                    {insight.root_cause && (
                      <Box mb={2}>
                        <Typography variant="subtitle2" gutterBottom>
                          Root Cause Analysis:
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {insight.root_cause}
                        </Typography>
                      </Box>
                    )}
                    
                    {insight.pattern_type && (
                      <Box mb={2}>
                        <Typography variant="subtitle2" gutterBottom>
                          Pattern Type:
                        </Typography>
                        <Chip 
                          label={insight.pattern_type.replace('_', ' ')} 
                          size="small" 
                          variant="outlined"
                        />
                      </Box>
                    )}
                    
                    {insight.server_name && (
                      <Box mb={2}>
                        <Typography variant="subtitle2" gutterBottom>
                          Affected Server:
                        </Typography>
                        <Chip 
                          label={insight.server_name} 
                          size="small" 
                          color="primary"
                          variant="outlined"
                        />
                      </Box>
                    )}
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Suggested Actions:
                    </Typography>
                    
                    <List dense>
                      {insight.suggested_actions.map((action, index) => (
                        <ListItem key={index} sx={{ pl: 0 }}>
                          <ListItemIcon>
                            <ScheduleIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={action.title}
                            secondary={
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  {action.description}
                                </Typography>
                                <Box display="flex" gap={1} mt={0.5}>
                                  <Chip
                                    label={`Risk: ${action.risk_level}`}
                                    size="small"
                                    color={action.risk_level === 'safe' ? 'success' : 
                                           action.risk_level === 'low' ? 'info' :
                                           action.risk_level === 'medium' ? 'warning' : 'error'}
                                    variant="outlined"
                                  />
                                  <Chip
                                    label={`Duration: ${action.estimated_duration}`}
                                    size="small"
                                    variant="outlined"
                                  />
                                </Box>
                              </Box>
                            }
                          />
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => handleActionClick(insight, action)}
                            sx={{ ml: 1 }}
                          >
                            Execute
                          </Button>
                        </ListItem>
                      ))}
                    </List>
                    
                    <Box mt={2} pt={2} borderTop={1} borderColor="divider">
                      <Typography variant="caption" color="text.secondary">
                        Generated: {new Date(insight.timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AIInsightsPanel;