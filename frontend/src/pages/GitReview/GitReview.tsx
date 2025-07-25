import {
    Assessment as AssessmentIcon,
    BugReport as BugIcon,
    Code as CodeIcon,
    Download as DownloadIcon,
    ExpandMore as ExpandMoreIcon,
    Folder as FolderIcon,
    GitHub as GitHubIcon,
    Speed as PerformanceIcon,
    Refresh as RefreshIcon,
    Security as SecurityIcon
} from '@mui/icons-material';
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Alert,
    AlertTitle,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    Grid,
    IconButton,
    InputLabel,
    LinearProgress,
    MenuItem,
    Paper,
    Select,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Tooltip,
    Typography
} from '@mui/material';
import { format } from 'date-fns';
import React, { useState } from 'react';
import useSWR from 'swr';

import apiClient from '../../services/api';

interface Repository {
  id: string;
  name: string;
  path: string;
  branch: string;
  lastCommit: string;
  status: 'clean' | 'modified' | 'staged';
}

interface ReviewResult {
  id: string;
  repository: Repository;
  timestamp: string;
  overallScore: number;
  status: 'completed' | 'in_progress' | 'failed';
  findings: ReviewFinding[];
  summary: {
    totalIssues: number;
    criticalIssues: number;
    securityIssues: number;
    performanceIssues: number;
    codeQualityScore: number;
    maintainabilityScore: number;
    testCoverage: number;
  };
  recommendations: string[];
  executionTime: number;
}

interface ReviewFinding {
  id: string;
  type: 'security' | 'performance' | 'bug' | 'style' | 'maintainability';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  file: string;
  line?: number;
  column?: number;
  suggestion?: string;
  codeSnippet?: string;
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'error';
    case 'high':
      return 'error';
    case 'medium':
      return 'warning';
    case 'low':
      return 'info';
    case 'info':
      return 'default';
    default:
      return 'default';
  }
};

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'security':
      return <SecurityIcon />;
    case 'performance':
      return <PerformanceIcon />;
    case 'bug':
      return <BugIcon />;
    case 'style':
    case 'maintainability':
      return <CodeIcon />;
    default:
      return <CodeIcon />;
  }
};

const getScoreColor = (score: number) => {
  if (score >= 8) return 'success';
  if (score >= 6) return 'warning';
  return 'error';
};

const GitReview: React.FC = () => {
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const [reviewType, setReviewType] = useState<string>('full');
  const [isReviewing, setIsReviewing] = useState(false);
  const [currentReviewId, setCurrentReviewId] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<ReviewResult | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Fetch available repositories
  const {
    data: repositories = [],
    error: reposError,
    isLoading: reposLoading,
    mutate: refreshRepos,
  } = useSWR<Repository[]>('/git/repositories', () => apiClient.getRepositories(), {
    refreshInterval: 30000,
  });

  // Fetch review history
  const {
    data: reviewHistory = [],
    error: historyError,
    isLoading: historyLoading,
    mutate: refreshHistory,
  } = useSWR<ReviewResult[]>('/git/reviews', () => apiClient.getReviewHistory(), {
    refreshInterval: 10000,
  });

  // Fetch current review results
  const {
    data: currentReviewResults,
    error: reviewResultsError,
    isLoading: reviewResultsLoading,
  } = useSWR(
    currentReviewId ? `/git/review/${currentReviewId}/results` : null,
    () => currentReviewId ? apiClient.getReviewResults(currentReviewId) : null,
    {
      refreshInterval: currentReviewId ? 5000 : 0, // Poll every 5 seconds if we have a review ID
      revalidateOnFocus: false,
    }
  );

  const handleStartReview = async () => {
    if (!selectedRepo) return;

    setIsReviewing(true);
    setCurrentReviewId(null);
    try {
      const result = await apiClient.startGitReview({
        repositoryId: selectedRepo,
        reviewType,
      });
      
      // Store the review ID for fetching results
      if (result && result.reviewId) {
        setCurrentReviewId(result.reviewId);
        console.log('Review started with ID:', result.reviewId);
      }
      
      // Refresh the history to show the new review
      refreshHistory();
      
    } catch (error) {
      console.error('Failed to start review:', error);
      setCurrentReviewId(null);
    } finally {
      setIsReviewing(false);
    }
  };

  const handleViewDetails = (result: ReviewResult) => {
    setSelectedResult(result);
    setDetailsOpen(true);
  };

  const handleDownloadReport = async (reviewId: string) => {
    try {
      const report = await apiClient.downloadReviewReport(reviewId);
      // Create and download file
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `review-report-${reviewId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download report:', error);
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Smart Git Review
      </Typography>

      {/* Repository Selection and Review Configuration */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Start New Review
          </Typography>
          
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Repository</InputLabel>
                <Select
                  value={selectedRepo}
                  onChange={(e) => setSelectedRepo(e.target.value)}
                  disabled={reposLoading || isReviewing}
                >
                  {repositories.map((repo) => (
                    <MenuItem key={repo.id} value={repo.id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <FolderIcon fontSize="small" />
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {repo.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {repo.branch} • {repo.status}
                          </Typography>
                        </Box>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Review Type</InputLabel>
                <Select
                  value={reviewType}
                  onChange={(e) => setReviewType(e.target.value)}
                  disabled={isReviewing}
                >
                  <MenuItem value="full">Full Review</MenuItem>
                  <MenuItem value="security">Security Focus</MenuItem>
                  <MenuItem value="performance">Performance Focus</MenuItem>
                  <MenuItem value="quick">Quick Scan</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={3}>
              <Button
                variant="contained"
                size="large"
                onClick={handleStartReview}
                disabled={!selectedRepo || isReviewing}
                startIcon={isReviewing ? <CircularProgress size={20} /> : <AssessmentIcon />}
                fullWidth
              >
                {isReviewing ? 'Reviewing...' : 'Start Review'}
              </Button>
            </Grid>

            <Grid item xs={12} md={2}>
              <Tooltip title="Refresh repositories">
                <IconButton onClick={() => refreshRepos()} disabled={reposLoading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Grid>
          </Grid>

          {reposError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              Failed to load repositories. Please check your Git configuration.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Review History */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Review History
            </Typography>
            <Tooltip title="Refresh history">
              <IconButton onClick={() => refreshHistory()}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {historyLoading ? (
            <LinearProgress sx={{ mb: 2 }} />
          ) : historyError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to load review history
            </Alert>
          ) : reviewHistory.length > 0 ? (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Repository</TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>Issues</TableCell>
                    <TableCell>Security</TableCell>
                    <TableCell>Performance</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reviewHistory.map((result) => (
                    <TableRow key={result.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <GitHubIcon fontSize="small" />
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {result.repository.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {result.repository.branch}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography
                            variant="h6"
                            color={`${getScoreColor(result.overallScore)}.main`}
                          >
                            {result.overallScore.toFixed(1)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            /10
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2">
                            {result.summary.totalIssues}
                          </Typography>
                          {result.summary.criticalIssues > 0 && (
                            <Chip
                              label={`${result.summary.criticalIssues} critical`}
                              color="error"
                              size="small"
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          color={result.summary.securityIssues > 0 ? 'error.main' : 'text.primary'}
                        >
                          {result.summary.securityIssues} issues
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          color={result.summary.performanceIssues > 0 ? 'warning.main' : 'text.primary'}
                        >
                          {result.summary.performanceIssues} issues
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {format(new Date(result.timestamp), 'MMM dd, HH:mm')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={result.status.toUpperCase()}
                          color={
                            result.status === 'completed'
                              ? 'success'
                              : result.status === 'failed'
                              ? 'error'
                              : 'default'
                          }
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="View details">
                            <IconButton
                              size="small"
                              onClick={() => handleViewDetails(result)}
                              disabled={result.status !== 'completed'}
                            >
                              <AssessmentIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Download report">
                            <IconButton
                              size="small"
                              onClick={() => handleDownloadReport(result.id)}
                              disabled={result.status !== 'completed'}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Alert severity="info">
              No reviews found. Start your first code review above.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Review Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              Review Details: {selectedResult?.repository.name}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h4" color={`${getScoreColor(selectedResult?.overallScore || 0)}.main`}>
                {selectedResult?.overallScore.toFixed(1)}/10
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {selectedResult && (
            <Box>
              {/* Summary Cards */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {selectedResult.summary.totalIssues}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Issues
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="error">
                        {selectedResult.summary.criticalIssues}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Critical
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="warning">
                        {selectedResult.summary.securityIssues}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Security
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="info">
                        {selectedResult.summary.testCoverage}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Test Coverage
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Recommendations */}
              {selectedResult.recommendations.length > 0 && (
                <Alert severity="info" sx={{ mb: 3 }}>
                  <AlertTitle>Recommendations</AlertTitle>
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    {selectedResult.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </Alert>
              )}

              {/* Findings */}
              <Typography variant="h6" gutterBottom>
                Detailed Findings ({selectedResult.findings.length})
              </Typography>
              
              {selectedResult.findings.map((finding, index) => (
                <Accordion key={finding.id} sx={{ mb: 1 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getTypeIcon(finding.type)}
                        <Chip
                          label={finding.severity.toUpperCase()}
                          color={getSeverityColor(finding.severity) as any}
                          size="small"
                        />
                      </Box>
                      <Typography variant="body1" sx={{ flexGrow: 1 }}>
                        {finding.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {finding.file}
                        {finding.line && `:${finding.line}`}
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="body2" paragraph>
                        {finding.description}
                      </Typography>
                      
                      {finding.codeSnippet && (
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            Code:
                          </Typography>
                          <Paper
                            variant="outlined"
                            sx={{
                              p: 2,
                              backgroundColor: 'grey.50',
                              fontFamily: 'monospace',
                              fontSize: '0.875rem',
                              mb: 2,
                            }}
                          >
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                              {finding.codeSnippet}
                            </pre>
                          </Paper>
                        </Box>
                      )}
                      
                      {finding.suggestion && (
                        <Alert severity="success">
                          <AlertTitle>Suggestion</AlertTitle>
                          {finding.suggestion}
                        </Alert>
                      )}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>
            Close
          </Button>
          {selectedResult && (
            <Button
              variant="contained"
              onClick={() => handleDownloadReport(selectedResult.id)}
              startIcon={<DownloadIcon />}
            >
              Download Report
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GitReview;