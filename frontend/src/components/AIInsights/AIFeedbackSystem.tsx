/**
 * AI Feedback System - Collects user feedback for AI actions and resolutions
 * 
 * Bu component, AI'ın eylemlerinin etkinliğini ölçmek ve öğrenme sürecini desteklemek için
 * kullanıcı feedback'i toplar.
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
  Rating,
  TextField,
  FormControlLabel,
  Checkbox,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  LinearProgress,
  Grid,
  Paper
} from '@mui/material';
import {
  Feedback as FeedbackIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  TrendingUp as TrendingUpIcon,
  Analytics as AnalyticsIcon,
  School as LearningIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import apiService from '../../services/api';

interface FeedbackRequest {
  actionId: string;
  actionTitle: string;
  actionType: string;
  completedAt: string;
  result?: any;
}

interface LearningInsights {
  total_events: number;
  total_resolutions: number;
  overall_success_rate: number;
  most_common_issues: Array<[string, number]>;
  best_performing_actions: Array<{
    action: string;
    issue_type: string;
    success_rate: number;
    attempts: number;
    user_satisfaction: number;
  }>;
  user_satisfaction: {
    average: number;
    trend: string;
  };
  patterns_discovered: number;
  learning_maturity: number;
  recommendations_available: boolean;
}

interface AIFeedbackSystemProps {
  pendingFeedback?: FeedbackRequest[];
  onFeedbackSubmitted?: (actionId: string) => void;
}

export const AIFeedbackSystem: React.FC<AIFeedbackSystemProps> = ({
  pendingFeedback = [],
  onFeedbackSubmitted
}) => {
  const [feedbackDialog, setFeedbackDialog] = useState(false);
  const [selectedAction, setSelectedAction] = useState<FeedbackRequest | null>(null);
  const [rating, setRating] = useState<number>(0);
  const [comment, setComment] = useState('');
  const [resolutionHelpful, setResolutionHelpful] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [learningInsights, setLearningInsights] = useState<LearningInsights | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  const fetchLearningInsights = async () => {
    try {
      setInsightsLoading(true);
      const response = await apiService.get<LearningInsights>('/orchestrator/learning/insights');
      setLearningInsights(response);
    } catch (err) {
      console.error('Failed to fetch learning insights:', err);
    } finally {
      setInsightsLoading(false);
    }
  };

  useEffect(() => {
    fetchLearningInsights();
  }, []);

  const handleFeedbackClick = (action: FeedbackRequest) => {
    setSelectedAction(action);
    setRating(0);
    setComment('');
    setResolutionHelpful(true);
    setError(null);
    setFeedbackDialog(true);
  };

  const submitFeedback = async () => {
    if (!selectedAction || rating === 0) {
      setError('Please provide a rating');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await apiService.post('/orchestrator/learning/feedback', {
        action_id: selectedAction.actionId,
        rating: rating,
        comment: comment,
        resolution_helpful: resolutionHelpful
      });

      setFeedbackDialog(false);
      
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted(selectedAction.actionId);
      }

      // Refresh insights after feedback
      await fetchLearningInsights();

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback');
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUpIcon color="success" />;
      case 'declining':
        return <ThumbDownIcon color="error" />;
      case 'stable':
        return <ThumbUpIcon color="info" />;
      default:
        return <InfoIcon color="disabled" />;
    }
  };

  const getTrendColor = (trend: string): 'success' | 'error' | 'info' | 'default' => {
    switch (trend) {
      case 'improving':
        return 'success';
      case 'declining':
        return 'error';
      case 'stable':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Pending Feedback */}
      {pendingFeedback.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <FeedbackIcon color="primary" />
              <Typography variant="h6">
                Feedback Needed ({pendingFeedback.length})
              </Typography>
              <Chip 
                label="Help AI Learn" 
                color="primary" 
                size="small"
                icon={<LearningIcon />}
              />
            </Box>

            <List>
              {pendingFeedback.map((action, index) => (
                <React.Fragment key={action.actionId}>
                  <ListItem>
                    <ListItemIcon>
                      <SuccessIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary={action.actionTitle}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Action Type: {action.actionType}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Completed: {new Date(action.completedAt).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleFeedbackClick(action)}
                    >
                      Rate Experience
                    </Button>
                  </ListItem>
                  {index < pendingFeedback.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Learning Insights */}
      {learningInsights && (
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <AnalyticsIcon color="primary" />
              <Typography variant="h6">
                AI Learning Progress
              </Typography>
              <Chip 
                label={`${Math.round(learningInsights.learning_maturity * 100)}% Maturity`}
                color={learningInsights.learning_maturity > 0.7 ? 'success' : 
                       learningInsights.learning_maturity > 0.4 ? 'warning' : 'default'}
                size="small"
              />
            </Box>

            {insightsLoading ? (
              <LinearProgress />
            ) : (
              <Grid container spacing={2}>
                {/* Overall Stats */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Overall Performance
                    </Typography>
                    <Box display="flex" alignItems="center" gap={2} mb={1}>
                      <Typography variant="h4" color="primary">
                        {Math.round(learningInsights.overall_success_rate * 100)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Success Rate
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {learningInsights.total_resolutions} resolutions from {learningInsights.total_events} events
                    </Typography>
                  </Paper>
                </Grid>

                {/* User Satisfaction */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      User Satisfaction
                    </Typography>
                    <Box display="flex" alignItems="center" gap={2} mb={1}>
                      <Rating 
                        value={learningInsights.user_satisfaction.average} 
                        readOnly 
                        precision={0.1}
                      />
                      <Box display="flex" alignItems="center" gap={1}>
                        {getTrendIcon(learningInsights.user_satisfaction.trend)}
                        <Chip
                          label={learningInsights.user_satisfaction.trend}
                          size="small"
                          color={getTrendColor(learningInsights.user_satisfaction.trend)}
                          variant="outlined"
                        />
                      </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Average: {learningInsights.user_satisfaction.average.toFixed(1)}/5.0
                    </Typography>
                  </Paper>
                </Grid>

                {/* Most Common Issues */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Most Common Issues
                    </Typography>
                    <List dense>
                      {learningInsights.most_common_issues.slice(0, 3).map(([issue, count]) => (
                        <ListItem key={issue} sx={{ px: 0 }}>
                          <ListItemText
                            primary={issue.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            secondary={`${count} occurrences`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Grid>

                {/* Best Performing Actions */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Best Performing Actions
                    </Typography>
                    <List dense>
                      {learningInsights.best_performing_actions.slice(0, 3).map((action, index) => (
                        <ListItem key={index} sx={{ px: 0 }}>
                          <ListItemText
                            primary={action.action.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            secondary={
                              <Box>
                                <Typography variant="caption" display="block">
                                  Success: {Math.round(action.success_rate * 100)}% 
                                  ({action.attempts} attempts)
                                </Typography>
                                <Rating 
                                  value={action.user_satisfaction} 
                                  readOnly 
                                  size="small"
                                  precision={0.1}
                                />
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Grid>

                {/* Learning Progress */}
                <Grid item xs={12}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Learning Progress
                    </Typography>
                    <Box mb={2}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2">
                          AI Learning Maturity
                        </Typography>
                        <Typography variant="body2">
                          {Math.round(learningInsights.learning_maturity * 100)}%
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={learningInsights.learning_maturity * 100}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                    <Box display="flex" gap={2}>
                      <Chip
                        label={`${learningInsights.patterns_discovered} Patterns Discovered`}
                        size="small"
                        color="info"
                        variant="outlined"
                      />
                      <Chip
                        label={learningInsights.recommendations_available ? 'Smart Recommendations Available' : 'Building Recommendations'}
                        size="small"
                        color={learningInsights.recommendations_available ? 'success' : 'default'}
                        variant="outlined"
                      />
                    </Box>
                  </Paper>
                </Grid>
              </Grid>
            )}
          </CardContent>
        </Card>
      )}

      {/* Feedback Dialog */}
      <Dialog 
        open={feedbackDialog} 
        onClose={() => setFeedbackDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Rate AI Action
        </DialogTitle>
        <DialogContent>
          {selectedAction && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                {selectedAction.actionTitle}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                How would you rate the effectiveness of this AI action?
              </Typography>

              <Box mb={3}>
                <Typography component="legend" gutterBottom>
                  Overall Rating *
                </Typography>
                <Rating
                  value={rating}
                  onChange={(_, newValue) => setRating(newValue || 0)}
                  size="large"
                />
              </Box>

              <FormControlLabel
                control={
                  <Checkbox
                    checked={resolutionHelpful}
                    onChange={(e) => setResolutionHelpful(e.target.checked)}
                  />
                }
                label="This resolution was helpful"
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                multiline
                rows={3}
                label="Additional Comments (Optional)"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="What worked well? What could be improved?"
                sx={{ mb: 2 }}
              />

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setFeedbackDialog(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button 
            onClick={submitFeedback}
            variant="contained"
            disabled={loading || rating === 0}
          >
            {loading ? 'Submitting...' : 'Submit Feedback'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIFeedbackSystem;