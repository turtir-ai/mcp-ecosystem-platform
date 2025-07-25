"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.NotificationManager = void 0;
const vscode = __importStar(require("vscode"));
class NotificationManager {
    constructor(configManager) {
        this.configManager = configManager;
    }
    showInfo(message, ...actions) {
        if (this.shouldShowNotification('all')) {
            return vscode.window.showInformationMessage(`MCP Platform: ${message}`, ...actions);
        }
        return Promise.resolve(undefined);
    }
    showWarning(message, ...actions) {
        if (this.shouldShowNotification('warnings')) {
            return vscode.window.showWarningMessage(`MCP Platform: ${message}`, ...actions);
        }
        return Promise.resolve(undefined);
    }
    showError(message, ...actions) {
        if (this.shouldShowNotification('errors')) {
            return vscode.window.showErrorMessage(`MCP Platform: ${message}`, ...actions);
        }
        return Promise.resolve(undefined);
    }
    async showProgress(title, task) {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `MCP Platform: ${title}`,
            cancellable: false
        }, task);
    }
    async showProgressWithCancellation(title, task) {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `MCP Platform: ${title}`,
            cancellable: true
        }, task);
    }
    async showQuickPick(items, options) {
        return vscode.window.showQuickPick(items, {
            ...options,
            placeHolder: options?.placeHolder || 'Select an option...'
        });
    }
    async showInputBox(options) {
        return vscode.window.showInputBox({
            ...options,
            prompt: options?.prompt || 'Enter value...'
        });
    }
    // Specialized notification methods
    async showCodeReviewResults(results) {
        const message = `Code review completed - Security: ${results.securityScore}/10, Quality: ${results.qualityScore}/10, Issues: ${results.findingsCount}`;
        const action = await this.showInfo(message, 'View Details', 'Dismiss');
        if (action === 'View Details') {
            vscode.commands.executeCommand('mcpPlatform.openDashboard');
        }
    }
    async showWorkflowCompletion(workflowName, status, duration) {
        const durationText = duration ? ` in ${Math.round(duration)}s` : '';
        if (status === 'completed') {
            const action = await this.showInfo(`Workflow "${workflowName}" completed successfully${durationText}`, 'View Results', 'Dismiss');
            if (action === 'View Results') {
                vscode.commands.executeCommand('mcpPlatform.openDashboard');
            }
        }
        else {
            const action = await this.showError(`Workflow "${workflowName}" failed${durationText}`, 'View Details', 'Retry', 'Dismiss');
            if (action === 'View Details') {
                vscode.commands.executeCommand('mcpPlatform.openDashboard');
            }
            else if (action === 'Retry') {
                vscode.commands.executeCommand('mcpPlatform.runWorkflow');
            }
        }
    }
    async showServerStatus(serverName, status) {
        if (status === 'unhealthy' || status === 'offline') {
            const action = await this.showWarning(`MCP Server "${serverName}" is ${status}`, 'Restart Server', 'View Status', 'Dismiss');
            if (action === 'Restart Server') {
                vscode.commands.executeCommand('mcpPlatform.restartServer', serverName);
            }
            else if (action === 'View Status') {
                vscode.commands.executeCommand('mcpPlatform.showStatus');
            }
        }
    }
    async showConfigurationPrompt() {
        const action = await this.showWarning('MCP Platform is not configured. Would you like to configure it now?', 'Configure', 'Later');
        if (action === 'Configure') {
            await this.showConfigurationDialog();
        }
    }
    async showConfigurationDialog() {
        const apiUrl = await this.showInputBox({
            prompt: 'Enter MCP Platform API URL',
            value: 'http://localhost:8000',
            validateInput: (value) => {
                try {
                    new URL(value);
                    return null;
                }
                catch {
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
    getOutputChannel() {
        if (!this.outputChannel) {
            this.outputChannel = vscode.window.createOutputChannel('MCP Platform');
        }
        return this.outputChannel;
    }
    logInfo(message) {
        const channel = this.getOutputChannel();
        channel.appendLine(`[INFO] ${new Date().toISOString()}: ${message}`);
    }
    logWarning(message) {
        const channel = this.getOutputChannel();
        channel.appendLine(`[WARN] ${new Date().toISOString()}: ${message}`);
    }
    logError(message, error) {
        const channel = this.getOutputChannel();
        channel.appendLine(`[ERROR] ${new Date().toISOString()}: ${message}`);
        if (error) {
            channel.appendLine(`Error details: ${JSON.stringify(error, null, 2)}`);
        }
    }
    showOutputChannel() {
        this.getOutputChannel().show();
    }
    shouldShowNotification(level) {
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
exports.NotificationManager = NotificationManager;
//# sourceMappingURL=notificationManager.js.map