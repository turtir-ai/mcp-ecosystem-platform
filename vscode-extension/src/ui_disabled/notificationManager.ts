import * as vscode from 'vscode';
import { ConfigurationManager } from '../config/configurationManager';

export class NotificationManager {
    constructor(private configManager: ConfigurationManager) {}

    showInfo(message: string, ...actions: string[]): Thenable<string | undefined> {
        if (this.shouldShowNotification('all')) {
            return vscode.window.showInformationMessage(`MCP Platform: ${message}`, ...actions);
        }
        return Promise.resolve(undefined);
    }

    showWarning(message: string, ...actions: string[]): Thenable<string | undefined> {
        if (this.shouldShowNotification('warnings')) {
            return vscode.window.showWarningMessage(`MCP Platform: ${message}`, ...actions);
        }
        return Promise.resolve(undefined);
    }

    showError(message: string, ...actions: string[]): Thenable<string | undefined> {
        if (this.shouldShowNotification('errors')) {
            return vscode.window.showErrorMessage(`MCP Platform: ${message}`, ...actions);
        }
        return Promise.resolve(undefined);
    }

    async showProgress<T>(
        title: string,
        task: (progress: vscode.Progress<{ message?: string; increment?: number }>) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: `MCP Platform: ${title}`,
                cancellable: false
            },
            task
        );
    }

    async showProgressWithCancellation<T>(
        title: string,
        task: (
            progress: vscode.Progress<{ message?: string; increment?: number }>,
            token: vscode.CancellationToken
        ) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: `MCP Platform: ${title}`,
                cancellable: true
            },
            task
        );
    }

    async showQuickPick<T extends vscode.QuickPickItem>(
        items: T[],
        options?: vscode.QuickPickOptions
    ): Promise<T | undefined> {
        return vscode.window.showQuickPick(items, {
            ...options,
            placeHolder: options?.placeHolder || 'Select an option...'
        });
    }

    async showInputBox(options?: vscode.InputBoxOptions): Promise<string | undefined> {
        return vscode.window.showInputBox({
            ...options,
            prompt: options?.prompt || 'Enter value...'
        });
    }

    // Specialized notification methods
    async showCodeReviewResults(results: {
        securityScore: number;
        qualityScore: number;
        findingsCount: number;
    }) {
        const message = `Code review completed - Security: ${results.securityScore}/10, Quality: ${results.qualityScore}/10, Issues: ${results.findingsCount}`;
        
        const action = await this.showInfo(message, 'View Details', 'Dismiss');
        
        if (action === 'View Details') {
            vscode.commands.executeCommand('mcpPlatform.openDashboard');
        }
    }

    async showWorkflowCompletion(workflowName: string, status: 'completed' | 'failed', duration?: number) {
        const durationText = duration ? ` in ${Math.round(duration)}s` : '';
        
        if (status === 'completed') {
            const action = await this.showInfo(
                `Workflow "${workflowName}" completed successfully${durationText}`,
                'View Results',
                'Dismiss'
            );
            
            if (action === 'View Results') {
                vscode.commands.executeCommand('mcpPlatform.openDashboard');
            }
        } else {
            const action = await this.showError(
                `Workflow "${workflowName}" failed${durationText}`,
                'View Details',
                'Retry',
                'Dismiss'
            );
            
            if (action === 'View Details') {
                vscode.commands.executeCommand('mcpPlatform.openDashboard');
            } else if (action === 'Retry') {
                vscode.commands.executeCommand('mcpPlatform.runWorkflow');
            }
        }
    }

    async showServerStatus(serverName: string, status: 'healthy' | 'degraded' | 'unhealthy' | 'offline') {
        if (status === 'unhealthy' || status === 'offline') {
            const action = await this.showWarning(
                `MCP Server "${serverName}" is ${status}`,
                'Restart Server',
                'View Status',
                'Dismiss'
            );
            
            if (action === 'Restart Server') {
                vscode.commands.executeCommand('mcpPlatform.restartServer', serverName);
            } else if (action === 'View Status') {
                vscode.commands.executeCommand('mcpPlatform.showStatus');
            }
        }
    }

    async showConfigurationPrompt() {
        const action = await this.showWarning(
            'MCP Platform is not configured. Would you like to configure it now?',
            'Configure',
            'Later'
        );
        
        if (action === 'Configure') {
            await this.showConfigurationDialog();
        }
    }

    private async showConfigurationDialog() {
        const apiUrl = await this.showInputBox({
            prompt: 'Enter MCP Platform API URL',
            value: 'http://localhost:8001',
            validateInput: (value) => {
                try {
                    new URL(value);
                    return null;
                } catch {
                    return 'Please enter a valid URL';
                }
            }
        });

        if (apiUrl) {
            await this.configManager.setApiUrl(apiUrl);
            
            const apiKey = await this.showInputBox({
                prompt: 'Enter API Key (optional)',
                password: true
            });

            if (apiKey) {
                await this.configManager.setApiKey(apiKey);
            }

            this.showInfo('Configuration saved successfully');
        }
    }

    // Output channel for detailed logging
    private outputChannel: vscode.OutputChannel | undefined;

    getOutputChannel(): vscode.OutputChannel {
        if (!this.outputChannel) {
            this.outputChannel = vscode.window.createOutputChannel('MCP Platform');
        }
        return this.outputChannel;
    }

    logInfo(message: string) {
        const channel = this.getOutputChannel();
        channel.appendLine(`[INFO] ${new Date().toISOString()}: ${message}`);
    }

    logWarning(message: string) {
        const channel = this.getOutputChannel();
        channel.appendLine(`[WARN] ${new Date().toISOString()}: ${message}`);
    }

    logError(message: string, error?: any) {
        const channel = this.getOutputChannel();
        channel.appendLine(`[ERROR] ${new Date().toISOString()}: ${message}`);
        if (error) {
            channel.appendLine(`Error details: ${JSON.stringify(error, null, 2)}`);
        }
    }

    showOutputChannel() {
        this.getOutputChannel().show();
    }

    private shouldShowNotification(level: 'errors' | 'warnings' | 'all'): boolean {
        const configLevel = this.configManager.getNotificationLevel();
        
        switch (configLevel) {
            case 'none':
                return false;
            case 'errors':
                return level === 'errors';
            case 'warnings':
                return level === 'errors' || level === 'warnings';
            case 'all':
                return true;
            default:
                return true;
        }
    }
}