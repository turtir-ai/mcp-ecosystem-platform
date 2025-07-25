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
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const mcpPlatformAPI_1 = require("./api/mcpPlatformAPI");
const configurationManager_1 = require("./config/configurationManager");
const codeReviewProvider_1 = require("./providers/codeReviewProvider");
const mcpStatusProvider_1 = require("./providers/mcpStatusProvider");
const workflowProvider_1 = require("./providers/workflowProvider");
const notificationManager_1 = require("./ui/notificationManager");
const statusBarManager_1 = require("./ui/statusBarManager");
let mcpAPI;
let statusBarManager;
let codeReviewProvider;
let workflowProvider;
let mcpStatusProvider;
let notificationManager;
let configManager;
function activate(context) {
    console.log('MCP Ecosystem Platform extension is now active!');
    // Initialize configuration manager
    configManager = new configurationManager_1.ConfigurationManager();
    // Initialize API client
    mcpAPI = new mcpPlatformAPI_1.MCPPlatformAPI(configManager);
    // Initialize managers and providers
    statusBarManager = new statusBarManager_1.StatusBarManager(mcpAPI, configManager);
    notificationManager = new notificationManager_1.NotificationManager(configManager);
    codeReviewProvider = new codeReviewProvider_1.CodeReviewProvider(mcpAPI, notificationManager);
    workflowProvider = new workflowProvider_1.WorkflowProvider(mcpAPI, notificationManager);
    mcpStatusProvider = new mcpStatusProvider_1.MCPStatusProvider(mcpAPI);
    // Register commands
    registerCommands(context);
    // Register providers
    registerProviders(context);
    // Initialize status bar
    statusBarManager.initialize();
    // Start periodic status updates
    startPeriodicUpdates();
    // Listen for configuration changes
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(event => {
        if (event.affectsConfiguration('mcpPlatform')) {
            configManager.refresh();
            mcpAPI.updateConfiguration(configManager);
            statusBarManager.refresh();
        }
    }));
    // Listen for file save events for auto-review
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(document => {
        if (configManager.getAutoReview()) {
            codeReviewProvider.reviewDocument(document);
        }
    }));
}
exports.activate = activate;
function registerCommands(context) {
    // Review code command
    context.subscriptions.push(vscode.commands.registerCommand('mcpPlatform.reviewCode', async (uri) => {
        try {
            if (uri) {
                await codeReviewProvider.reviewPath(uri.fsPath);
            }
            else {
                await codeReviewProvider.reviewWorkspace();
            }
        }
        catch (error) {
            notificationManager.showError(`Code review failed: ${error}`);
        }
    }));
    // Review current file command
    context.subscriptions.push(vscode.commands.registerCommand('mcpPlatform.reviewCurrentFile', async () => {
        try {
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor) {
                await codeReviewProvider.reviewDocument(activeEditor.document);
            }
            else {
                notificationManager.showWarning('No active file to review');
            }
        }
        catch (error) {
            notificationManager.showError(`File review failed: ${error}`);
        }
    }));
    // Run workflow command
    context.subscriptions.push(vscode.commands.registerCommand('mcpPlatform.runWorkflow', async () => {
        try {
            await workflowProvider.showWorkflowPicker();
        }
        catch (error) {
            notificationManager.showError(`Workflow execution failed: ${error}`);
        }
    }));
    // Open dashboard command
    context.subscriptions.push(vscode.commands.registerCommand('mcpPlatform.openDashboard', () => {
        const dashboardUrl = `${configManager.getApiUrl().replace('/api', '')}/dashboard`;
        vscode.env.openExternal(vscode.Uri.parse(dashboardUrl));
    }));
    // Show status command
    context.subscriptions.push(vscode.commands.registerCommand('mcpPlatform.showStatus', async () => {
        try {
            await mcpStatusProvider.showStatusPanel();
        }
        catch (error) {
            notificationManager.showError(`Failed to show status: ${error}`);
        }
    }));
    // Refresh status command
    context.subscriptions.push(vscode.commands.registerCommand('mcpPlatform.refreshStatus', async () => {
        try {
            await statusBarManager.refresh();
            await mcpStatusProvider.refresh();
            notificationManager.showInfo('MCP Platform status refreshed');
        }
        catch (error) {
            notificationManager.showError(`Failed to refresh status: ${error}`);
        }
    }));
}
function registerProviders(context) {
    // Register MCP status tree data provider
    const mcpStatusTreeProvider = new MCPStatusTreeProvider(mcpAPI);
    context.subscriptions.push(vscode.window.createTreeView('mcpPlatformStatus', {
        treeDataProvider: mcpStatusTreeProvider,
        showCollapseAll: true
    }));
    // Register code lens provider for inline reviews
    context.subscriptions.push(vscode.languages.registerCodeLensProvider({ scheme: 'file', language: '*' }, new CodeReviewCodeLensProvider(codeReviewProvider)));
}
function startPeriodicUpdates() {
    // Update status every 30 seconds
    setInterval(async () => {
        try {
            await statusBarManager.refresh();
        }
        catch (error) {
            console.error('Failed to update status:', error);
        }
    }, 30000);
}
function deactivate() {
    console.log('MCP Ecosystem Platform extension is now deactivated');
}
exports.deactivate = deactivate;
// Tree data provider for MCP status view
class MCPStatusTreeProvider {
    constructor(mcpAPI) {
        this.mcpAPI = mcpAPI;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    async getChildren(element) {
        if (!element) {
            // Root level - show MCP servers
            try {
                const status = await this.mcpAPI.getMCPStatus();
                return status.map(server => new MCPStatusItem(server.name, server.status, vscode.TreeItemCollapsibleState.Collapsed, {
                    command: 'mcpPlatform.showStatus',
                    title: 'Show Details',
                    arguments: [server.name]
                }));
            }
            catch (error) {
                return [new MCPStatusItem('Error loading status', 'error', vscode.TreeItemCollapsibleState.None)];
            }
        }
        else {
            // Server details
            try {
                const serverDetails = await this.mcpAPI.getServerDetails(element.label);
                return [
                    new MCPStatusItem(`Status: ${serverDetails.status}`, '', vscode.TreeItemCollapsibleState.None),
                    new MCPStatusItem(`Response Time: ${serverDetails.response_time_ms}ms`, '', vscode.TreeItemCollapsibleState.None),
                    new MCPStatusItem(`Uptime: ${serverDetails.uptime_percentage}%`, '', vscode.TreeItemCollapsibleState.None)
                ];
            }
            catch (error) {
                return [new MCPStatusItem('Error loading details', 'error', vscode.TreeItemCollapsibleState.None)];
            }
        }
    }
}
class MCPStatusItem extends vscode.TreeItem {
    constructor(label, status, collapsibleState, command) {
        super(label, collapsibleState);
        this.label = label;
        this.status = status;
        this.collapsibleState = collapsibleState;
        this.command = command;
        this.tooltip = `${this.label}: ${this.status}`;
        this.contextValue = 'mcpStatusItem';
        // Set icon based on status
        if (status === 'healthy') {
            this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('charts.green'));
        }
        else if (status === 'degraded') {
            this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('charts.yellow'));
        }
        else if (status === 'unhealthy' || status === 'offline') {
            this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('charts.red'));
        }
        else {
            this.iconPath = new vscode.ThemeIcon('pulse');
        }
    }
}
// Code lens provider for inline code reviews
class CodeReviewCodeLensProvider {
    constructor(codeReviewProvider) {
        this.codeReviewProvider = codeReviewProvider;
    }
    provideCodeLenses(document) {
        const codeLenses = [];
        // Add code lens at the top of the file
        const range = new vscode.Range(0, 0, 0, 0);
        const reviewCommand = {
            title: "$(search-fuzzy) Review with MCP Platform",
            command: 'mcpPlatform.reviewCurrentFile'
        };
        codeLenses.push(new vscode.CodeLens(range, reviewCommand));
        return codeLenses;
    }
}
//# sourceMappingURL=extension.js.map