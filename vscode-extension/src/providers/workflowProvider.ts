import * as vscode from 'vscode';
import { MCPPlatformAPI, Workflow, WorkflowExecution } from '../api/mcpPlatformAPI';
import { NotificationManager } from '../ui/notificationManager';

interface WorkflowQuickPickItem extends vscode.QuickPickItem {
    workflow: Workflow;
}

export class WorkflowProvider {
    private activeExecutions: Map<string, WorkflowExecution> = new Map();
    private executionStatusInterval: NodeJS.Timeout | undefined;

    constructor(
        private mcpAPI: MCPPlatformAPI,
        private notificationManager: NotificationManager
    ) {}

    async showWorkflowPicker(): Promise<void> {
        try {
            const workflows = await this.mcpAPI.getWorkflows();
            
            if (workflows.length === 0) {
                this.notificationManager.showInfo('No workflows available. Create workflows in the MCP Platform dashboard.');
                return;
            }

            const quickPickItems: WorkflowQuickPickItem[] = workflows
                .filter(wf => wf.is_valid)
                .map(workflow => ({
                    label: workflow.name,
                    description: workflow.description || 'No description',
                    detail: `Status: ${workflow.status}`,
                    workflow: workflow
                }));

            if (quickPickItems.length === 0) {
                this.notificationManager.showWarning('No valid workflows available for execution.');
                return;
            }

            const selected = await this.notificationManager.showQuickPick(quickPickItems, {
                placeHolder: 'Select a workflow to execute',
                matchOnDescription: true,
                matchOnDetail: true
            });

            if (selected) {
                await this.executeWorkflow(selected.workflow);
            }
        } catch (error) {
            this.notificationManager.showError(`Failed to load workflows: ${error}`);
        }
    }

    async executeWorkflow(workflow: Workflow, inputs?: any): Promise<void> {
        try {
            // Show input dialog if needed
            const workflowInputs = inputs || await this.getWorkflowInputs(workflow);

            await this.notificationManager.showProgress(
                `Executing workflow: ${workflow.name}`,
                async (progress) => {
                    progress.report({ message: 'Starting workflow execution...' });

                    const execution = await this.mcpAPI.executeWorkflow(workflow.id, workflowInputs);
                    this.activeExecutions.set(execution.execution_id, execution);

                    progress.report({ message: 'Workflow started, monitoring progress...', increment: 20 });

                    // Start monitoring execution
                    await this.monitorExecution(execution.execution_id, progress);
                }
            );
        } catch (error) {
            this.notificationManager.showError(`Failed to execute workflow: ${error}`);
        }
    }

    private async getWorkflowInputs(workflow: Workflow): Promise<any> {
        // For now, return empty inputs
        // In a full implementation, this would parse the workflow definition
        // and prompt for required inputs
        return {};
    }

    private async monitorExecution(
        executionId: string,
        progress?: vscode.Progress<{ message?: string; increment?: number }>
    ): Promise<void> {
        const maxAttempts = 60; // 10 minutes max
        const pollInterval = 10000; // 10 seconds

        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            try {
                const execution = await this.mcpAPI.getWorkflowExecutionStatus(executionId);
                this.activeExecutions.set(executionId, execution);

                if (progress && execution.progress !== undefined) {
                    progress.report({
                        message: `Execution in progress... ${execution.progress}%`,
                        increment: execution.progress
                    });
                }

                if (execution.status === 'completed') {
                    this.handleExecutionCompleted(execution);
                    return;
                } else if (execution.status === 'failed') {
                    this.handleExecutionFailed(execution);
                    return;
                } else if (execution.status === 'cancelled') {
                    this.handleExecutionCancelled(execution);
                    return;
                }

                // Still running, wait and try again
                await new Promise(resolve => setTimeout(resolve, pollInterval));
            } catch (error) {
                this.notificationManager.logError(`Execution monitoring failed (attempt ${attempt + 1})`, error);
                
                if (attempt === maxAttempts - 1) {
                    this.handleExecutionError(executionId, error);
                    return;
                }
            }
        }

        this.handleExecutionTimeout(executionId);
    }

    private handleExecutionCompleted(execution: WorkflowExecution): void {
        this.activeExecutions.delete(execution.execution_id);
        
        const duration = execution.started_at ? 
            (Date.now() - new Date(execution.started_at).getTime()) / 1000 : undefined;

        this.notificationManager.showWorkflowCompletion(
            'Workflow', // We don't have workflow name in execution object
            'completed',
            duration
        );

        this.notificationManager.logInfo(`Workflow execution ${execution.execution_id} completed successfully`);
    }

    private handleExecutionFailed(execution: WorkflowExecution): void {
        this.activeExecutions.delete(execution.execution_id);
        
        const duration = execution.started_at ? 
            (Date.now() - new Date(execution.started_at).getTime()) / 1000 : undefined;

        this.notificationManager.showWorkflowCompletion(
            'Workflow', // We don't have workflow name in execution object
            'failed',
            duration
        );

        this.notificationManager.logError(`Workflow execution ${execution.execution_id} failed`);
    }

    private handleExecutionCancelled(execution: WorkflowExecution): void {
        this.activeExecutions.delete(execution.execution_id);
        this.notificationManager.showInfo('Workflow execution was cancelled');
        this.notificationManager.logInfo(`Workflow execution ${execution.execution_id} was cancelled`);
    }

    private handleExecutionError(executionId: string, error: any): void {
        this.activeExecutions.delete(executionId);
        this.notificationManager.showError(`Workflow execution monitoring failed: ${error}`);
        this.notificationManager.logError(`Workflow execution ${executionId} monitoring failed`, error);
    }

    private handleExecutionTimeout(executionId: string): void {
        this.activeExecutions.delete(executionId);
        this.notificationManager.showWarning('Workflow execution monitoring timed out');
        this.notificationManager.logWarning(`Workflow execution ${executionId} monitoring timed out`);
    }

    async cancelExecution(executionId: string): Promise<void> {
        try {
            const success = await this.mcpAPI.cancelWorkflowExecution(executionId);
            
            if (success) {
                this.activeExecutions.delete(executionId);
                this.notificationManager.showInfo('Workflow execution cancelled successfully');
            } else {
                this.notificationManager.showWarning('Failed to cancel workflow execution');
            }
        } catch (error) {
            this.notificationManager.showError(`Failed to cancel execution: ${error}`);
        }
    }

    // Quick workflow execution for common tasks
    async executeCodeReviewWorkflow(): Promise<void> {
        try {
            const workflows = await this.mcpAPI.getWorkflows();
            const codeReviewWorkflow = workflows.find(wf => 
                wf.name.toLowerCase().includes('code review') || 
                wf.name.toLowerCase().includes('review')
            );

            if (codeReviewWorkflow) {
                await this.executeWorkflow(codeReviewWorkflow);
            } else {
                this.notificationManager.showInfo('No code review workflow found. Create one in the dashboard.');
            }
        } catch (error) {
            this.notificationManager.showError(`Failed to execute code review workflow: ${error}`);
        }
    }

    async executeSecurityScanWorkflow(): Promise<void> {
        try {
            const workflows = await this.mcpAPI.getWorkflows();
            const securityWorkflow = workflows.find(wf => 
                wf.name.toLowerCase().includes('security') || 
                wf.name.toLowerCase().includes('scan')
            );

            if (securityWorkflow) {
                await this.executeWorkflow(securityWorkflow);
            } else {
                this.notificationManager.showInfo('No security scan workflow found. Create one in the dashboard.');
            }
        } catch (error) {
            this.notificationManager.showError(`Failed to execute security scan workflow: ${error}`);
        }
    }

    // Status and management methods
    getActiveExecutions(): WorkflowExecution[] {
        return Array.from(this.activeExecutions.values());
    }

    isExecutionActive(executionId: string): boolean {
        return this.activeExecutions.has(executionId);
    }

    async refreshExecutionStatus(): Promise<void> {
        const executionIds = Array.from(this.activeExecutions.keys());
        
        for (const executionId of executionIds) {
            try {
                const execution = await this.mcpAPI.getWorkflowExecutionStatus(executionId);
                this.activeExecutions.set(executionId, execution);

                // Check if execution is complete
                if (['completed', 'failed', 'cancelled'].includes(execution.status)) {
                    this.activeExecutions.delete(executionId);
                }
            } catch (error) {
                this.notificationManager.logError(`Failed to refresh execution ${executionId}`, error);
            }
        }
    }

    startPeriodicStatusUpdates(): void {
        this.stopPeriodicStatusUpdates();
        
        this.executionStatusInterval = setInterval(async () => {
            if (this.activeExecutions.size > 0) {
                await this.refreshExecutionStatus();
            }
        }, 15000); // Update every 15 seconds
    }

    stopPeriodicStatusUpdates(): void {
        if (this.executionStatusInterval) {
            clearInterval(this.executionStatusInterval);
            this.executionStatusInterval = undefined;
        }
    }

    dispose(): void {
        this.stopPeriodicStatusUpdates();
        this.activeExecutions.clear();
    }
}