import {
    Alert,
    Avatar,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    Grid,
    IconButton,
    InputAdornment,
    InputLabel,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    MenuItem,
    Paper,
    Select,
    Stack,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TablePagination,
    TableRow,
    TextField,
    Tooltip,
    Typography
} from '@mui/material';
import {
    CalendarToday as CalendarIcon,
    CheckCircle as CheckCircleIcon,
    Download as DownloadIcon,
    Error as ErrorIcon,
    FilterList as FilterIcon,
    Person as PersonIcon,
    PlayArrow as PlayIcon,
    Schedule as ScheduleIcon,
    Search as SearchIcon,
    Stop as StopIcon,
    AccessTime as TimeIcon,
    Visibility as ViewIcon
} from '@mui/icons-material';
// Note: DatePicker components would need @mui/x-date-pickers package
// For now, we'll use regular TextField for date inputs
import React, { useEffect, useState } from 'react';

interface HistoryExecution {
  id: string;
  workflowId: string;
  workflowName: string;
  status: 'completed' | 'failed' | 'cancelled';
  startTime: string;
  endTime: string;
  duration: number;
  totalSteps: number;
  completedSteps: number;
  failedSteps: number;
  executedBy: string;
  inputs?: any;
  outputs?: any;
  error?: string;
  logs?: string[];
}

const WorkflowHistory: React.FC = () => {
  const [executions, setExecutions] = useState<HistoryExecution[]>([]);
  const [filteredExecutions, setFilteredExecutions] = useState<HistoryExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFrom, setDateFrom] = useState<Date | null>(null);
  const [dateTo, setDateTo] = useState<Date | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<HistoryExecution | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Mock data - replace with actual API call
  useEffect(() => {
    const mockExecutions: HistoryExecution[] = [
      {
        id: 'exec-001',
        workflowId: 'wf-001',
        workflowName: 'Code Review & Security Scan',
        status: 'completed',
        startTime: '2024-01-15T10:30:00Z',
        endTime: '2024-01-15T10:35:30Z',
        duration: 330,
        totalSteps: 5,
        completedSteps: 5,
        failedSteps: 0,
        executedBy: 'john.doe@example.com',
        inputs: { repository: 'my-project', branch: 'main' },
        outputs: { securityScore: 8.5, qualityScore: 9.2 }
      },
      {
        id: 'exec-002',
        workflowId: 'wf-002',
        workflowName: 'Market Research Analysis',
        status: 'failed',
        startTime: '2024-01-15T09:15:00Z',
        endTime: '2024-01-15T09:25:45Z',
        duration: 645,
        totalSteps: 8,
        completedSteps: 3,
        failedSteps: 1,
        executedBy: 'jane.smith@example.com',
        error: 'API rate limit exceeded for search service',
        inputs: { query: 'AI development tools', depth: 3 }
      },
      {
        id: 'exec-003',
        workflowId: 'wf-003',
        workflowName: 'Network Performance Monitor',
        status: 'completed',
        startTime: '2024-01-15T08:00:00Z',
        endTime: '2024-01-15T08:10:15Z',
        duration: 615,
        totalSteps: 4,
        completedSteps: 4,
        failedSteps: 0,
        executedBy: 'admin@example.com',
        outputs: { avgLatency: 45, throughput: '1.2 Gbps', issues: 0 }
      },
      {
        id: 'exec-004',
        workflowId: 'wf-001',
        workflowName: 'Code Review & Security Scan',
        status: 'cancelled',
        startTime: '2024-01-14T16:45:00Z',
        endTime: '2024-01-14T16:47:30Z',
        duration: 150,
        totalSteps: 5,
        completedSteps: 2,
        failedSteps: 0,
        executedBy: 'john.doe@example.com',
        inputs: { repository: 'legacy-project', branch: 'develop' }
      }
    ];

    setExecutions(mockExecutions);
    setFilteredExecutions(mockExecutions);
    setLoading(false);
  }, []);

  // Filter executions based on search and filters
  useEffect(() => {
    let filtered = executions;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(exec =>
        exec.workflowName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        exec.executedBy.toLowerCase().includes(searchTerm.toLowerCase()) ||
        exec.id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(exec => exec.status === statusFilter);
    }

    // Date range filter
    if (dateFrom) {
      filtered = filtered.filter(exec => new Date(exec.startTime) >= dateFrom);
    }
    if (dateTo) {
      filtered = filtered.filter(exec => new Date(exec.startTime) <= dateTo);
    }

    setFilteredExecutions(filtered);
    setPage(0); // Reset to first page when filtering
  }, [executions, searchTerm, statusFilter, dateFrom, dateTo]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon />;
      case 'failed':
        return <ErrorIcon />;
      case 'cancelled':
        return <StopIcon />;
      default:
        return <ScheduleIcon />;
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const handleViewDetails = (execution: HistoryExecution) => {
    setSelectedExecution(execution);
    setDetailsOpen(true);
  };

  const handleExportResults = (execution: HistoryExecution) => {
    const data = {
      execution_id: execution.id,
      workflow_name: execution.workflowName,
      status: execution.status,
      duration: execution.duration,
      inputs: execution.inputs,
      outputs: execution.outputs,
      error: execution.error,
      executed_at: execution.startTime,
      executed_by: execution.executedBy
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-execution-${execution.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setDateFrom(null);
    setDateTo(null);
  };

  return (
    <Box>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Workflow Execution History
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View and analyze past workflow executions
          </Typography>
        </Box>

        {/* Filters */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Filters
          </Typography>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                placeholder="Search workflows..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="cancelled">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="From Date"
                type="date"
                value={dateFrom ? dateFrom.toISOString().split('T')[0] : ''}
                onChange={(e) => setDateFrom(e.target.value ? new Date(e.target.value) : null)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="To Date"
                type="date"
                value={dateTo ? dateTo.toISOString().split('T')[0] : ''}
                onChange={(e) => setDateTo(e.target.value ? new Date(e.target.value) : null)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Stack direction="row" spacing={1}>
                <Button
                  variant="outlined"
                  onClick={clearFilters}
                  startIcon={<FilterIcon />}
                >
                  Clear Filters
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </Paper>

        {/* Results Summary */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <PlayIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">
                      {filteredExecutions.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Executions
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar sx={{ bgcolor: 'success.main' }}>
                    <CheckCircleIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">
                      {filteredExecutions.filter(e => e.status === 'completed').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Completed
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar sx={{ bgcolor: 'error.main' }}>
                    <ErrorIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">
                      {filteredExecutions.filter(e => e.status === 'failed').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Failed
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar sx={{ bgcolor: 'info.main' }}>
                    <TimeIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">
                      {formatDuration(
                        filteredExecutions.reduce((sum, e) => sum + e.duration, 0) / 
                        filteredExecutions.length || 0
                      )}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg Duration
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Executions Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Workflow</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Steps</TableCell>
                <TableCell>Executed By</TableCell>
                <TableCell>Started</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredExecutions
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((execution) => (
                  <TableRow key={execution.id} hover>
                    <TableCell>
                      <Typography variant="subtitle2">
                        {execution.workflowName}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {execution.id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={execution.status}
                        color={getStatusColor(execution.status)}
                        icon={getStatusIcon(execution.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {formatDuration(execution.duration)}
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2">
                          {execution.completedSteps}/{execution.totalSteps}
                        </Typography>
                        {execution.failedSteps > 0 && (
                          <Typography variant="caption" color="error">
                            {execution.failedSteps} failed
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar sx={{ width: 24, height: 24 }}>
                          <PersonIcon fontSize="small" />
                        </Avatar>
                        <Typography variant="body2">
                          {execution.executedBy.split('@')[0]}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(execution.startTime).toLocaleDateString()}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(execution.startTime).toLocaleTimeString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => handleViewDetails(execution)}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Export Results">
                          <IconButton
                            size="small"
                            onClick={() => handleExportResults(execution)}
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
          <TablePagination
            rowsPerPageOptions={[5, 10, 25, 50]}
            component="div"
            count={filteredExecutions.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </TableContainer>

        {/* Execution Details Dialog */}
        <Dialog
          open={detailsOpen}
          onClose={() => setDetailsOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Execution Details: {selectedExecution?.workflowName}
          </DialogTitle>
          <DialogContent>
            {selectedExecution && (
              <Box sx={{ pt: 2 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Execution Summary
                        </Typography>
                        <List dense>
                          <ListItem>
                            <ListItemIcon>
                              <CalendarIcon />
                            </ListItemIcon>
                            <ListItemText
                              primary="Started"
                              secondary={new Date(selectedExecution.startTime).toLocaleString()}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon>
                              <CalendarIcon />
                            </ListItemIcon>
                            <ListItemText
                              primary="Completed"
                              secondary={new Date(selectedExecution.endTime).toLocaleString()}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon>
                              <TimeIcon />
                            </ListItemIcon>
                            <ListItemText
                              primary="Duration"
                              secondary={formatDuration(selectedExecution.duration)}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon>
                              <PersonIcon />
                            </ListItemIcon>
                            <ListItemText
                              primary="Executed By"
                              secondary={selectedExecution.executedBy}
                            />
                          </ListItem>
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Results
                        </Typography>
                        <List dense>
                          <ListItem>
                            <ListItemText
                              primary="Status"
                              secondary={
                                <Chip
                                  label={selectedExecution.status}
                                  color={getStatusColor(selectedExecution.status)}
                                  size="small"
                                />
                              }
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary="Steps Completed"
                              secondary={`${selectedExecution.completedSteps}/${selectedExecution.totalSteps}`}
                            />
                          </ListItem>
                          {selectedExecution.failedSteps > 0 && (
                            <ListItem>
                              <ListItemText
                                primary="Failed Steps"
                                secondary={selectedExecution.failedSteps}
                              />
                            </ListItem>
                          )}
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                  {selectedExecution.inputs && (
                    <Grid item xs={12}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Inputs
                          </Typography>
                          <pre style={{ fontSize: '0.875rem', overflow: 'auto' }}>
                            {JSON.stringify(selectedExecution.inputs, null, 2)}
                          </pre>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                  {selectedExecution.outputs && (
                    <Grid item xs={12}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Outputs
                          </Typography>
                          <pre style={{ fontSize: '0.875rem', overflow: 'auto' }}>
                            {JSON.stringify(selectedExecution.outputs, null, 2)}
                          </pre>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                  {selectedExecution.error && (
                    <Grid item xs={12}>
                      <Alert severity="error">
                        <Typography variant="subtitle2" gutterBottom>
                          Error Details
                        </Typography>
                        {selectedExecution.error}
                      </Alert>
                    </Grid>
                  )}
                </Grid>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDetailsOpen(false)}>
              Close
            </Button>
            {selectedExecution && (
              <Button
                onClick={() => handleExportResults(selectedExecution)}
                startIcon={<DownloadIcon />}
              >
                Export
              </Button>
            )}
          </DialogActions>
        </Dialog>
      </Box>
  );
};

export default WorkflowHistory;