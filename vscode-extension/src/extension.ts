import * as vscode from 'vscode';
import { MCPPlatformAPI } from './api/mcpPlatformAPI';
import { ConfigurationManager } from './config/configurationManager';
import { CodeReviewProvider } from './providers/codeReviewProvider';
import { MCPStatusProvider } from './providers/mcpStatusProvider';
import { WorkflowProvider } from './providers/workflowProvider';
import { NotificationManager } from './ui/notificationManager';
import { StatusBarManager } from './ui/statusBarManager';

let mcpAPI: MCPPlatformAPI;
let statusBarManager: StatusBarManager;
let codeReviewProvider: CodeReviewProvider;
let workflowProvider: WorkflowProvider;
let mcpStatusProvider: MCPStatusProvider;
let notificationManager: NotificationManager;
let configManager: ConfigurationManager;

export function activate(context: vscode.ExtensionContext) {
    console.log('MCP Ecosystem Platform extension is now active!');

    // Initialize configuration manager
    configManager = new ConfigurationManager();
    
    // Initialize API client
    mcpAPI = new MCPPlatformAPI(configManager);
    
    // Initialize managers and providers
    statusBarManager = new StatusBarManager(mcpAPI, configManager);
    notificationManager = new NotificationManager(configManager);
    codeReviewProvider = new CodeReviewProvider(mcpAPI, notificationManager);
    workflowProvider = new WorkflowProvider(mcpAPI, notificationManager);
    mcpStatusProvider = new MCPStatusProvider(mcpAPI);

    // Register commands
    registerCommands(context);
    
    // Register providers
    registerProviders(context);
    
    // Initialize status bar
    statusBarManager.initialize();
    
    // Start periodic status updates
    startPeriodicUpdates();
    
    // Listen for configuration changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration('mcpPlatform')) {
                configManager.refresh();
                mcpAPI.updateConfiguration(configManager);
                statusBarManager.refresh();
            }
        })
    );

    // Listen for file save events for auto-review
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(document => {
            if (configManager.getAutoReview()) {
                codeReviewProvider.reviewDocument(document);
            }
        })
    );
}

function registerCommands(context: vscode.ExtensionContext) {
    // Review code command
    context.subscriptions.push(
        vscode.commands.registerCommand('mcpPlatform.reviewCode', async (uri?: vscode.Uri) => {
            try {
                if (uri) {
                    await codeReviewProvider.reviewPath(uri.fsPath);
                } else {
                    await codeReviewProvider.reviewWorkspace();
                }
            } catch (error) {
                notificationManager.showError(`Code review failed: ${error}`);
            }
        })
    );

    // Review current file command
    context.subscriptions.push(
        vscode.commands.registerCommand('mcpPlatform.reviewCurrentFile', async () => {
            try {
                const activeEditor = vscode.window.activeTextEditor;
                if (activeEditor) {
                    await codeReviewProvider.reviewDocument(activeEditor.document);
                } else {
                    notificationManager.showWarning('No active file to review');
                }
            } catch (error) {
                notificationManager.showError(`File review failed: ${error}`);
            }
        })
    );

    // Run workflow command
    context.subscriptions.push(
        vscode.commands.registerCommand('mcpPlatform.runWorkflow', async () => {
            try {
                await workflowProvider.showWorkflowPicker();
            } catch (error) {
                notificationManager.showError(`Workflow execution failed: ${error}`);
            }
        })
    );

    // Open dashboard command
    context.subscriptions.push(
        vscode.commands.registerCommand('mcpPlatform.openDashboard', () => {
            const dashboardUrl = `${configManager.getApiUrl().replace('/api', '')}/dashboard`;
            vscode.env.openExternal(vscode.Uri.parse(dashboardUrl));
        })
    );

    // Show status command
    context.subscriptions.push(
        vscode.commands.registerCommand('mcpPlatform.showStatus', async () => {
            try {
                await mcpStatusProvider.showStatusPanel();
            } catch (error) {
                notificationManager.showError(`Failed to show status: ${error}`);
            }
        })
    );

    // Refresh status command
    context.subscriptions.push(
        vscode.commands.registerCommand('mcpPlatform.refreshStatus', async () => {
            try {
                await statusBarManager.refresh();
                await mcpStatusProvider.refresh();
                notificationManager.showInfo('MCP Platform status refreshed');
            } catch (error) {
                notificationManager.showError(`Failed to refresh status: ${error}`);
            }
        })
    );
}

function registerProviders(context: vscode.ExtensionContext) {
    // Register MCP status tree data provider
    const mcpStatusTreeProvider = new MCPStatusTreeProvider(mcpAPI);
    context.subscriptions.push(
        vscode.window.createTreeView('mcpPlatformStatus', {
            treeDataProvider: mcpStatusTreeProvider,
            showCollapseAll: true
        })
    );

    // Register code lens provider for inline reviews
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider(
            { scheme: 'file', language: '*' },
            new CodeReviewCodeLensProvider(codeReviewProvider)
        )
    );
}

function startPeriodicUpdates() {
    // Update status every 30 seconds
    setInterval(async () => {
        try {
            await statusBarManager.refresh();
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    }, 30000);
}

export function deactivate() {
    console.log('MCP Ecosystem Platform extension is now deactivated');
}

// Tree data provider for MCP status view
class MCPStatusTreeProvider implements vscode.TreeDataProvider<MCPStatusItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<MCPStatusItem | undefined | null | void> = new vscode.EventEmitter<MCPStatusItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<MCPStatusItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor(private mcpAPI: MCPPlatformAPI) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: MCPStatusItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: MCPStatusItem): Promise<MCPStatusItem[]> {
        if (!element) {
            // Root level - show MCP servers
            try {
                const status = await this.mcpAPI.getMCPStatus();
                return status.map(server => new MCPStatusItem(
                    server.name,
                    server.status,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    {
                        command: 'mcpPlatform.showStatus',
                        title: 'Show Details',
                        arguments: [server.name]
                    }
                ));
            } catch (error) {
                return [new MCPStatusItem('Error loading status', 'error', vscode.TreeItemCollapsibleState.None)];
            }
        } else {
            // Server details
            try {
                const serverDetails = await this.mcpAPI.getServerDetails(element.label as string);
                return [
                    new MCPStatusItem(`Status: ${serverDetails.status}`, '', vscode.TreeItemCollapsibleState.None),
                    new MCPStatusItem(`Response Time: ${serverDetails.response_time_ms}ms`, '', vscode.TreeItemCollapsibleState.None),
                    new MCPStatusItem(`Uptime: ${serverDetails.uptime_percentage}%`, '', vscode.TreeItemCollapsibleState.None)
                ];
            } catch (error) {
                return [new MCPStatusItem('Error loading details', 'error', vscode.TreeItemCollapsibleState.None)];
            }
        }
    }
}

class MCPStatusItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly status: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly command?: vscode.Command
    ) {
        super(label, collapsibleState);
        this.tooltip = `${this.label}: ${this.status}`;
        this.contextValue = 'mcpStatusItem';
        
        // Set icon based on status
        if (status === 'healthy') {
            this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('charts.green'));
        } else if (status === 'degraded') {
            this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('charts.yellow'));
        } else if (status === 'unhealthy' || status === 'offline') {
            this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('charts.red'));
        } else {
            this.iconPath = new vscode.ThemeIcon('pulse');
        }
    }
}

// Code lens provider for inline code reviews
class CodeReviewCodeLensProvider implements vscode.CodeLensProvider {
    constructor(private codeReviewProvider: CodeReviewProvider) {}

    provideCodeLenses(document: vscode.TextDocument): vscode.CodeLens[] {
        const codeLenses: vscode.CodeLens[] = [];
        
        // Add code lens at the top of the file
        const range = new vscode.Range(0, 0, 0, 0);
        const reviewCommand: vscode.Command = {
            title: "$(search-fuzzy) Review with MCP Platform",
            command: 'mcpPlatform.reviewCurrentFile'
        };
        
        codeLenses.push(new vscode.CodeLens(range, reviewCommand));
        
        return codeLenses;
    }
}