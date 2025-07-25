import { useCallback, useState } from 'react';
import { apiClient, WorkflowDefinition, WorkflowStep } from '../services/api';

interface Workflow extends WorkflowDefinition {
  status?: string;
  created_at?: string;
  updated_at?: string;
}

interface WorkflowExecution {
  id: string;
  workflowId: string;
  workflowName: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';
  startTime: string;
  endTime?: string;
  duration?: number;
  progress: number;
  steps: any[];
  totalSteps: number;
  completedSteps: number;
  failedSteps: number;
  inputs?: any;
  outputs?: any;
  error?: string;
}

export const useWorkflows = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshWorkflows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.getWorkflows();
      setWorkflows(response);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch workflows');
      console.error('Failed to fetch workflows:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshExecutions = useCallback(async () => {
    try {
      // Mock data for now - replace with actual API call
      const mockExecutions: WorkflowExecution[] = [
        {
          id: 'exec-001',
          workflowId: 'wf-001',
          workflowName: 'Code Review & Security Scan',
          status: 'running',
          startTime: new Date().toISOString(),
          progress: 60,
          steps: [
            { id: 'step-1', name: 'Git Analysis', status: 'completed' },
            { id: 'step-2', name: 'Code Quality Check', status: 'completed' },
            { id: 'step-3', name: 'Security Scan', status: 'running', progress: 75 },
            { id: 'step-4', name: 'Generate Report', status: 'pending' },
            { id: 'step-5', name: 'Send Notification', status: 'pending' }
          ],
          totalSteps: 5,
          completedSteps: 2,
          failedSteps: 0,
          duration: 180
        },
        {
          id: 'exec-002',
          workflowId: 'wf-002',
          workflowName: 'Market Research Analysis',
          status: 'completed',
          startTime: new Date(Date.now() - 600000).toISOString(),
          endTime: new Date(Date.now() - 60000).toISOString(),
          progress: 100,
          steps: [
            { id: 'step-1', name: 'Web Search', status: 'completed' },
            { id: 'step-2', name: 'Data Extraction', status: 'completed' },
            { id: 'step-3', name: 'Analysis', status: 'completed' },
            { id: 'step-4', name: 'Report Generation', status: 'completed' }
          ],
          totalSteps: 4,
          completedSteps: 4,
          failedSteps: 0,
          duration: 540,
          outputs: { insights: 'Market analysis complete', score: 8.5 }
        }
      ];
      setExecutions(mockExecutions);
    } catch (err: any) {
      console.error('Failed to fetch executions:', err);
    }
  }, []);

  const createWorkflow = useCallback(async (workflowData: WorkflowDefinition) => {
    setLoading(true);
    setError(null);
    try {
      // Ensure the workflow data matches the expected API format
      const formattedWorkflow: Partial<WorkflowDefinition> = {
        name: workflowData.name,
        description: workflowData.description,
        version: workflowData.version,
        steps: workflowData.steps.map(step => ({
          id: step.id || `step-${Date.now()}`,
          name: step.name || '',
          type: step.type || 'action',
          mcp_server: step.mcp_server,
          tool_name: step.tool_name,
          parameters: step.parameters || {},
          depends_on: step.depends_on || [],
          retry_count: step.retry_count || 0,
          timeout_seconds: step.timeout_seconds || 300,
          description: step.description,
          tags: step.tags || []
        })),
        tags: workflowData.tags || [],
        is_valid: workflowData.is_valid,
        validation_errors: workflowData.validation_errors || []
      };
      
      const response = await apiClient.createWorkflow(formattedWorkflow);
      await refreshWorkflows(); // Refresh the list
      return response.data;
    } catch (err: any) {
      setError(err.message || 'Failed to create workflow');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [refreshWorkflows]);

  const updateWorkflow = useCallback(async (workflowId: string, workflowData: Partial<WorkflowDefinition>) => {
    setLoading(true);
    setError(null);
    try {
      const response = { data: workflowData }; // Mock for now - need to implement update method
      await refreshWorkflows(); // Refresh the list
      return response.data;
    } catch (err: any) {
      setError(err.message || 'Failed to update workflow');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [refreshWorkflows]);

  const deleteWorkflow = useCallback(async (workflowId: string) => {
    setLoading(true);
    setError(null);
    try {
      // Mock for now - need to implement delete method
      await refreshWorkflows(); // Refresh the list
    } catch (err: any) {
      setError(err.message || 'Failed to delete workflow');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [refreshWorkflows]);

  const executeWorkflow = useCallback(async (workflowId: string, inputs?: any) => {
    setError(null);
    try {
      const response = await apiClient.executeWorkflow(parseInt(workflowId), inputs);
      await refreshExecutions(); // Refresh executions
      return response.data;
    } catch (err: any) {
      setError(err.message || 'Failed to execute workflow');
      throw err;
    }
  }, [refreshExecutions]);

  const cancelExecution = useCallback(async (executionId: string) => {
    setError(null);
    try {
      await apiClient.cancelExecution(executionId);
      await refreshExecutions(); // Refresh executions
    } catch (err: any) {
      setError(err.message || 'Failed to cancel execution');
      throw err;
    }
  }, [refreshExecutions]);

  const getExecutionStatus = useCallback(async (executionId: string) => {
    try {
      const response = await apiClient.getExecutionStatus(executionId);
      return response.data;
    } catch (err: any) {
      console.error('Failed to get execution status:', err);
      throw err;
    }
  }, []);

  const validateWorkflow = useCallback(async (workflowDefinition: WorkflowDefinition) => {
    try {
      // Ensure the workflow data matches the expected API format
      const formattedWorkflow: WorkflowDefinition = {
        ...workflowDefinition,
        steps: workflowDefinition.steps.map(step => ({
          id: step.id || `step-${Date.now()}`,
          name: step.name || '',
          type: step.type || 'action',
          mcp_server: step.mcp_server,
          tool_name: step.tool_name,
          parameters: step.parameters || {},
          depends_on: step.depends_on || [],
          retry_count: step.retry_count || 0,
          timeout_seconds: step.timeout_seconds || 300,
          description: step.description,
          tags: step.tags || []
        }))
      };
      
      const response = await apiClient.validateWorkflow(formattedWorkflow);
      return response;
    } catch (err: any) {
      console.error('Failed to validate workflow:', err);
      throw err;
    }
  }, []);

  const getWorkflowTemplates = useCallback(async () => {
    try {
      const response = await apiClient.getWorkflowTemplates();
      return response;
    } catch (err: any) {
      console.error('Failed to get workflow templates:', err);
      throw err;
    }
  }, []);

  const createWorkflowFromTemplate = useCallback(async (templateId: string, name: string, parameters?: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.createWorkflowFromTemplate(templateId, name, parameters);
      await refreshWorkflows(); // Refresh the list
      return response.data;
    } catch (err: any) {
      setError(err.message || 'Failed to create workflow from template');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [refreshWorkflows]);

  return {
    workflows,
    executions,
    loading,
    error,
    refreshWorkflows,
    refreshExecutions,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    executeWorkflow,
    cancelExecution,
    getExecutionStatus,
    validateWorkflow,
    getWorkflowTemplates,
    createWorkflowFromTemplate
  };
};