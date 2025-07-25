import {
    Add as AddIcon,
    CheckCircle as CheckCircleIcon,
    Delete as DeleteIcon,
    Edit as EditIcon,
    Error as ErrorIcon,
    MoreVert as MoreVertIcon,
    Pause as PauseIcon,
    PlayArrow as PlayIcon,
    Schedule as ScheduleIcon,
    Stop as StopIcon
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardActions,
    CardContent,
    Chip,
    Container,
    Dialog,
    DialogContent,
    DialogTitle,
    Grid,
    IconButton,
    LinearProgress,
    ListItemIcon,
    ListItemText,
    Menu,
    MenuItem,
    Paper,
    Tab,
    Tabs,
    Typography
} from '@mui/material';
// import { useTheme } from '@mui/material/styles';
import React, { useEffect, useState } from 'react';

import WorkflowBuilder from '../../components/Workflows/WorkflowBuilder';
import WorkflowExecutionMonitor from '../../components/Workflows/WorkflowExecutionMonitor';
import WorkflowHistory from '../../components/Workflows/WorkflowHistory';
import { useWorkflows } from '../../hooks/useWorkflows';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`workflow-tabpanel-${index}`}
      aria-labelledby={`workflow-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `workflow-tab-${index}`,
    'aria-controls': `workflow-tabpanel-${index}`,
  };
}

const Workflows: React.FC = () => {
  // const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [builderOpen, setBuilderOpen] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuWorkflow, setMenuWorkflow] = useState<any>(null);

  const {
    workflows,
    executions,
    loading,
    error,
    createWorkflow,
    executeWorkflow,
    cancelExecution,
    deleteWorkflow,
    refreshWorkflows,
    refreshExecutions
  } = useWorkflows();

  useEffect(() => {
    refreshWorkflows();
    refreshExecutions();
  }, [refreshWorkflows, refreshExecutions]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleCreateWorkflow = () => {
    setSelectedWorkflow(null);
    setBuilderOpen(true);
  };

  const handleEditWorkflow = (workflow: any) => {
    setSelectedWorkflow(workflow);
    setBuilderOpen(true);
    handleMenuClose();
  };

  const handleExecuteWorkflow = async (workflow: any) => {
    try {
      await executeWorkflow(workflow.id);
      handleMenuClose();
    } catch (error) {
      console.error('Failed to execute workflow:', error);
    }
  };

  const handleDeleteWorkflow = async (workflow: any) => {
    if (window.confirm(`Are you sure you want to delete "${workflow.name}"?`)) {
      try {
        await deleteWorkflow(workflow.id);
        handleMenuClose();
      } catch (error) {
        console.error('Failed to delete workflow:', error);
      }
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, workflow: any) => {
    setAnchorEl(event.currentTarget);
    setMenuWorkflow(workflow);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuWorkflow(null);
  };

  const getStatusColor = (status?: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    if (!status) return 'default';
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'running':
        return 'primary';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status?: string): React.ReactElement => {
    if (!status) return <ScheduleIcon />;
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircleIcon />;
      case 'running':
        return <PlayIcon />;
      case 'failed':
        return <ErrorIcon />;
      case 'cancelled':
        return <StopIcon />;
      case 'paused':
        return <PauseIcon />;
      default:
        return <ScheduleIcon />;
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Workflow Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Create, manage, and monitor automated workflows across your MCP servers
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ width: '100%', mb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="workflow tabs">
            <Tab label="My Workflows" {...a11yProps(0)} />
            <Tab label="Executions" {...a11yProps(1)} />
            <Tab label="History" {...a11yProps(2)} />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h6">
              Workflows ({workflows.length})
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateWorkflow}
            >
              Create Workflow
            </Button>
          </Box>

          {loading ? (
            <LinearProgress />
          ) : (
            <Grid container spacing={3}>
              {workflows.map((workflow) => (
                <Grid item xs={12} sm={6} md={4} key={workflow.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Typography variant="h6" component="h2" gutterBottom>
                          {workflow.name}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, workflow)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {workflow.description || 'No description'}
                      </Typography>

                      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        <Chip
                          label={workflow.status || 'Unknown'}
                          color={getStatusColor(workflow.status)}
                          size="small"
                          icon={getStatusIcon(workflow.status)}
                        />
                        {workflow.is_valid ? (
                          <Chip label="Valid" color="success" size="small" />
                        ) : (
                          <Chip label="Invalid" color="error" size="small" />
                        )}
                      </Box>

                      <Typography variant="caption" color="text.secondary">
                        Created: {workflow.created_at ? new Date(workflow.created_at).toLocaleDateString() : 'Unknown'}
                      </Typography>
                    </CardContent>
                    
                    <CardActions>
                      <Button
                        size="small"
                        startIcon={<PlayIcon />}
                        onClick={() => handleExecuteWorkflow(workflow)}
                        disabled={!workflow.is_valid}
                      >
                        Execute
                      </Button>
                      <Button
                        size="small"
                        startIcon={<EditIcon />}
                        onClick={() => handleEditWorkflow(workflow)}
                      >
                        Edit
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
              
              {workflows.length === 0 && !loading && (
                <Grid item xs={12}>
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      No workflows yet
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      Create your first workflow to automate tasks across MCP servers
                    </Typography>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={handleCreateWorkflow}
                    >
                      Create Your First Workflow
                    </Button>
                  </Box>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <WorkflowExecutionMonitor
            executions={executions}
            onCancelExecution={cancelExecution}
            onRefresh={refreshExecutions}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <WorkflowHistory />
        </TabPanel>
      </Paper>

      {/* Workflow Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleExecuteWorkflow(menuWorkflow)}>
          <ListItemIcon>
            <PlayIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Execute</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleEditWorkflow(menuWorkflow)}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleDeleteWorkflow(menuWorkflow)}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Workflow Builder Dialog */}
      <Dialog
        open={builderOpen}
        onClose={() => setBuilderOpen(false)}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          {selectedWorkflow ? 'Edit Workflow' : 'Create New Workflow'}
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          <WorkflowBuilder
            workflow={selectedWorkflow}
            onSave={async (workflowData) => {
              try {
                await createWorkflow(workflowData);
                setBuilderOpen(false);
                refreshWorkflows();
              } catch (error) {
                console.error('Failed to save workflow:', error);
              }
            }}
            onCancel={() => setBuilderOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </Container>
  );
};

export default Workflows;