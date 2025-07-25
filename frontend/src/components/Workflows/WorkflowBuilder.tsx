import {
    Add as AddIcon,
    Code as CodeIcon,
    Delete as DeleteIcon,
    DragIndicator as DragIcon,
    Link as LinkIcon,
    NetworkCheck as NetworkIcon,
    Save as SaveIcon,
    Search as SearchIcon,
    Security as SecurityIcon,
    Settings as SettingsIcon,
    Storage as StorageIcon,
    Terminal as TerminalIcon
} from '@mui/icons-material';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    CardHeader,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Drawer,
    FormControl,
    FormControlLabel,
    Grid,
    IconButton,
    InputLabel,
    List,
    ListItem,
    ListItemIcon,
    MenuItem,
    Paper,
    Select,
    Switch,
    TextField,
    Typography
} from '@mui/material';
import React, { useCallback, useEffect, useState } from 'react';
// Note: react-beautiful-dnd would need to be installed
// For now, we'll implement basic reordering functionality

import { useMCPServers } from '../../hooks/useMCPServers';

interface WorkflowStep {
  id: string;
  name: string;
  mcpServer: string;
  toolName: string;
  arguments: Record<string, any>;
  dependsOn: string[];
  timeout: number;
  retryCount: number;
  enabled: boolean;
}

interface WorkflowBuilderProps {
  workflow?: any;
  onSave: (workflow: any) => Promise<void>;
  onCancel: () => void;
}

const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  workflow,
  onSave,
  onCancel
}) => {
  const [workflowName, setWorkflowName] = useState(workflow?.name || '');
  const [workflowDescription, setWorkflowDescription] = useState(workflow?.description || '');
  const [steps, setSteps] = useState<WorkflowStep[]>(workflow?.definition?.steps || []);
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [stepDialogOpen, setStepDialogOpen] = useState(false);
  const [editingStep, setEditingStep] = useState<WorkflowStep | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const { servers, tools, loading: serversLoading } = useMCPServers();

  const mcpServerIcons: Record<string, React.ReactElement> = {
    'kiro-tools': <TerminalIcon />,
    'groq-llm': <CodeIcon />,
    'browser-automation': <SearchIcon />,
    'deep-research': <SearchIcon />,
    'api-key-sniffer': <SecurityIcon />,
    'network-analysis': <NetworkIcon />,
    'enhanced-filesystem': <StorageIcon />,
    'enhanced-git': <CodeIcon />,
    'openrouter-llm': <CodeIcon />,
    'real-browser': <SearchIcon />,
    'simple-warp': <TerminalIcon />
  };

  const createNewStep = (): WorkflowStep => ({
    id: `step-${Date.now()}`,
    name: '',
    mcpServer: '',
    toolName: '',
    arguments: {},
    dependsOn: [],
    timeout: 60,
    retryCount: 3,
    enabled: true
  });

  const handleAddStep = () => {
    setEditingStep(createNewStep());
    setStepDialogOpen(true);
  };

  const handleEditStep = (step: WorkflowStep) => {
    setEditingStep({ ...step });
    setStepDialogOpen(true);
  };

  const handleDeleteStep = (stepId: string) => {
    setSteps(prev => prev.filter(step => step.id !== stepId));
    // Remove dependencies on deleted step
    setSteps(prev => prev.map(step => ({
      ...step,
      dependsOn: step.dependsOn.filter(dep => dep !== stepId)
    })));
  };

  const handleSaveStep = () => {
    if (!editingStep) return;

    if (editingStep.name && editingStep.mcpServer && editingStep.toolName) {
      const existingIndex = steps.findIndex(s => s.id === editingStep.id);
      if (existingIndex >= 0) {
        setSteps(prev => prev.map((step, index) => 
          index === existingIndex ? editingStep : step
        ));
      } else {
        setSteps(prev => [...prev, editingStep]);
      }
      setStepDialogOpen(false);
      setEditingStep(null);
    }
  };

  // Simple reordering functions (can be enhanced with drag-and-drop later)
  const moveStepUp = (index: number) => {
    if (index > 0) {
      const newSteps = [...steps];
      [newSteps[index - 1], newSteps[index]] = [newSteps[index], newSteps[index - 1]];
      setSteps(newSteps);
    }
  };

  const moveStepDown = (index: number) => {
    if (index < steps.length - 1) {
      const newSteps = [...steps];
      [newSteps[index], newSteps[index + 1]] = [newSteps[index + 1], newSteps[index]];
      setSteps(newSteps);
    }
  };

  const validateWorkflow = useCallback(() => {
    const errors: string[] = [];

    if (!workflowName.trim()) {
      errors.push('Workflow name is required');
    }

    if (steps.length === 0) {
      errors.push('At least one step is required');
    }

    // Check for circular dependencies
    const checkCircularDependency = (stepId: string, visited: Set<string> = new Set()): boolean => {
      if (visited.has(stepId)) return true;
      visited.add(stepId);

      const step = steps.find(s => s.id === stepId);
      if (!step) return false;

      return step.dependsOn.some(dep => checkCircularDependency(dep, new Set(visited)));
    };

    steps.forEach(step => {
      if (checkCircularDependency(step.id)) {
        errors.push(`Circular dependency detected involving step "${step.name}"`);
      }

      if (!step.name.trim()) {
        errors.push(`Step name is required for step ${step.id}`);
      }

      if (!step.mcpServer) {
        errors.push(`MCP server is required for step "${step.name}"`);
      }

      if (!step.toolName) {
        errors.push(`Tool name is required for step "${step.name}"`);
      }
    });

    setValidationErrors(errors);
    return errors.length === 0;
  }, [workflowName, steps]);

  useEffect(() => {
    validateWorkflow();
  }, [validateWorkflow]);

  const handleSave = async () => {
    if (!validateWorkflow()) return;

    setSaving(true);
    try {
      const workflowData = {
        name: workflowName,
        description: workflowDescription,
        definition: {
          steps: steps.map((step, index) => ({
            name: step.name,
            mcp_server: step.mcpServer,
            tool_name: step.toolName,
            arguments: step.arguments,
            depends_on: step.dependsOn,
            timeout: step.timeout,
            retry_count: step.retryCount,
            enabled: step.enabled,
            order: index
          }))
        }
      };

      await onSave(workflowData);
    } catch (error) {
      console.error('Failed to save workflow:', error);
    } finally {
      setSaving(false);
    }
  };

  const getAvailableTools = (serverName: string) => {
    return tools[serverName] || [];
  };

  const getStepDependencyOptions = (currentStepId: string) => {
    return steps.filter(step => step.id !== currentStepId);
  };

  return (
    <Box sx={{ display: 'flex', height: '100%' }}>
      {/* MCP Servers Drawer */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={drawerOpen}
        sx={{
          width: 300,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 300,
            boxSizing: 'border-box',
            position: 'relative',
            height: '100%'
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Available MCP Servers
          </Typography>
          <List>
            {servers.map((server) => (
              <ListItem key={server.name} sx={{ px: 1 }}>
                <Card sx={{ width: '100%' }}>
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        {mcpServerIcons[server.name] || <TerminalIcon />}
                      </ListItemIcon>
                      <Typography variant="subtitle2">
                        {server.name}
                      </Typography>
                    </Box>
                    <Chip
                      label={server.status}
                      color={server.status === 'healthy' ? 'success' : 'error'}
                      size="small"
                    />
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      {getAvailableTools(server.name).length} tools available
                    </Typography>
                  </CardContent>
                </Card>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, p: 3 }}>
        {/* Workflow Header */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Workflow Name"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                error={!workflowName.trim() && validationErrors.length > 0}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Description"
                value={workflowDescription}
                onChange={(e) => setWorkflowDescription(e.target.value)}
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        </Paper>

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Please fix the following issues:
            </Typography>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </Alert>
        )}

        {/* Workflow Steps */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Workflow Steps ({steps.length})
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddStep}
            >
              Add Step
            </Button>
          </Box>

          <Box>
            {steps.map((step, index) => (
              <Card
                key={step.id}
                sx={{
                  mb: 2,
                  opacity: step.enabled ? 1 : 0.6
                }}
              >
                <CardHeader
                  avatar={<DragIcon />}
                            title={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="h6">
                                  {step.name || `Step ${index + 1}`}
                                </Typography>
                                {!step.enabled && (
                                  <Chip label="Disabled" size="small" color="default" />
                                )}
                              </Box>
                            }
                            subheader={`${step.mcpServer} → ${step.toolName}`}
                            action={
                              <Box>
                                <IconButton onClick={() => handleEditStep(step)}>
                                  <SettingsIcon />
                                </IconButton>
                                <IconButton onClick={() => handleDeleteStep(step.id)}>
                                  <DeleteIcon />
                                </IconButton>
                              </Box>
                            }
                          />
                          <CardContent>
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              {step.dependsOn.length > 0 && (
                                <Chip
                                  label={`Depends on: ${step.dependsOn.length} step(s)`}
                                  size="small"
                                  icon={<LinkIcon />}
                                />
                              )}
                              <Chip
                                label={`Timeout: ${step.timeout}s`}
                                size="small"
                              />
                              <Chip
                                label={`Retries: ${step.retryCount}`}
                                size="small"
                              />
                            </Box>
                          </CardContent>
                </Card>
            ))}
          </Box>

          {steps.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No steps added yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Add steps to build your workflow
              </Typography>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={handleAddStep}
              >
                Add First Step
              </Button>
            </Box>
          )}
        </Paper>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            onClick={onCancel}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={validationErrors.length > 0 || saving}
          >
            {saving ? 'Saving...' : 'Save Workflow'}
          </Button>
        </Box>
      </Box>

      {/* Step Configuration Dialog */}
      <Dialog
        open={stepDialogOpen}
        onClose={() => setStepDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingStep?.name ? 'Edit Step' : 'Add New Step'}
        </DialogTitle>
        <DialogContent>
          {editingStep && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Step Name"
                    value={editingStep.name}
                    onChange={(e) => setEditingStep({
                      ...editingStep,
                      name: e.target.value
                    })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={editingStep.enabled}
                        onChange={(e) => setEditingStep({
                          ...editingStep,
                          enabled: e.target.checked
                        })}
                      />
                    }
                    label="Enabled"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>MCP Server</InputLabel>
                    <Select
                      value={editingStep.mcpServer}
                      onChange={(e) => setEditingStep({
                        ...editingStep,
                        mcpServer: e.target.value,
                        toolName: '' // Reset tool when server changes
                      })}
                    >
                      {servers.map((server) => (
                        <MenuItem key={server.name} value={server.name}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {mcpServerIcons[server.name] || <TerminalIcon />}
                            {server.name}
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth disabled={!editingStep.mcpServer}>
                    <InputLabel>Tool</InputLabel>
                    <Select
                      value={editingStep.toolName}
                      onChange={(e) => setEditingStep({
                        ...editingStep,
                        toolName: e.target.value
                      })}
                    >
                      {getAvailableTools(editingStep.mcpServer).map((tool: any) => (
                        <MenuItem key={tool.name} value={tool.name}>
                          {tool.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Timeout (seconds)"
                    type="number"
                    value={editingStep.timeout}
                    onChange={(e) => setEditingStep({
                      ...editingStep,
                      timeout: parseInt(e.target.value) || 60
                    })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Retry Count"
                    type="number"
                    value={editingStep.retryCount}
                    onChange={(e) => setEditingStep({
                      ...editingStep,
                      retryCount: parseInt(e.target.value) || 0
                    })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Dependencies</InputLabel>
                    <Select
                      multiple
                      value={editingStep.dependsOn}
                      onChange={(e) => setEditingStep({
                        ...editingStep,
                        dependsOn: e.target.value as string[]
                      })}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(selected as string[]).map((value) => {
                            const step = steps.find(s => s.id === value);
                            return (
                              <Chip key={value} label={step?.name || value} size="small" />
                            );
                          })}
                        </Box>
                      )}
                    >
                      {getStepDependencyOptions(editingStep.id).map((step) => (
                        <MenuItem key={step.id} value={step.id}>
                          {step.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStepDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSaveStep}
            variant="contained"
            disabled={!editingStep?.name || !editingStep?.mcpServer || !editingStep?.toolName}
          >
            Save Step
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WorkflowBuilder;