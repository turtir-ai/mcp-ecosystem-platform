import * as vscode from 'vscode';
import { MCPPlatformAPI, MCPServerStatus } from '../api/mcpPlatformAPI';

export class MCPStatusProvider {
    private statusPanel: vscode.WebviewPanel | undefined;
    private lastStatus: MCPServerStatus[] = [];

    constructor(private mcpAPI: MCPPlatformAPI) {}

    async showStatusPanel(): Promise<void> {
        if (this.statusPanel) {
            this.statusPanel.reveal();
            return;
        }

        this.statusPanel = vscode.window.createWebviewPanel(
            'mcpStatus',
            'MCP Platform Status',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.statusPanel.onDidDispose(() => {
            this.statusPanel = undefined;
        });

        await this.updateStatusPanel();
    }

    async refresh(): Promise<void> {
        try {
            this.lastStatus = await this.mcpAPI.getMCPStatus();
            
            if (this.statusPanel) {
                await this.updateStatusPanel();
            }
        } catch (error) {
            console.error('Failed to refresh MCP status:', error);
        }
    }

    private async updateStatusPanel(): Promise<void> {
        if (!this.statusPanel) return;

        try {
            const servers = await this.mcpAPI.getMCPStatus();
            this.lastStatus = servers;
            
            this.statusPanel.webview.html = this.generateStatusHTML(servers);
        } catch (error) {
            this.statusPanel.webview.html = this.generateErrorHTML(error);
        }
    }

    private generateStatusHTML(servers: MCPServerStatus[]): string {
        const healthyCount = servers.filter(s => s.status === 'healthy').length;
        const totalCount = servers.length;
        const overallStatus = this.getOverallStatus(servers);

        return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>MCP Platform Status</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                    margin: 0;
                    padding: 20px;
                }
                .header {
                    display: flex;
                    align-items: center;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .status-icon {
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    margin-right: 10px;
                }
                .status-healthy { background-color: #00ff00; }
                .status-degraded { background-color: #ffff00; }
                .status-unhealthy { background-color: #ff0000; }
                .status-offline { background-color: #888888; }
                .summary {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 30px;
                }
                .summary-card {
                    background-color: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px;
                    padding: 15px;
                    text-align: center;
                }
                .summary-number {
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                .server-list {
                    display: grid;
                    gap: 15px;
                }
                .server-card {
                    background-color: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px;
                    padding: 15px;
                }
                .server-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 10px;
                }
                .server-name {
                    font-size: 16px;
                    font-weight: bold;
                }
                .server-details {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                    font-size: 14px;
                }
                .detail-item {
                    display: flex;
                    justify-content: space-between;
                }
                .error-message {
                    color: var(--vscode-errorForeground);
                    font-style: italic;
                    margin-top: 10px;
                }
                .refresh-button {
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-left: auto;
                }
                .refresh-button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                .last-updated {
                    text-align: center;
                    color: var(--vscode-descriptionForeground);
                    font-size: 12px;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="status-icon status-${overallStatus}"></div>
                <h1>MCP Platform Status</h1>
                <button class="refresh-button" onclick="refresh()">Refresh</button>
            </div>

            <div class="summary">
                <div class="summary-card">
                    <div class="summary-number">${totalCount}</div>
                    <div>Total Servers</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">${healthyCount}</div>
                    <div>Healthy</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">${servers.filter(s => s.status === 'degraded').length}</div>
                    <div>Degraded</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">${servers.filter(s => s.status === 'unhealthy' || s.status === 'offline').length}</div>
                    <div>Unhealthy</div>
                </div>
            </div>

            <div class="server-list">
                ${servers.map(server => `
                    <div class="server-card">
                        <div class="server-header">
                            <div class="server-name">${server.name}</div>
                            <div class="status-icon status-${server.status}"></div>
                        </div>
                        <div class="server-details">
                            <div class="detail-item">
                                <span>Status:</span>
                                <span>${server.status}</span>
                            </div>
                            <div class="detail-item">
                                <span>Response Time:</span>
                                <span>${server.response_time_ms}ms</span>
                            </div>
                            <div class="detail-item">
                                <span>Uptime:</span>
                                <span>${server.uptime_percentage.toFixed(1)}%</span>
                            </div>
                            <div class="detail-item">
                                <span>Last Check:</span>
                                <span>${new Date(server.last_check).toLocaleTimeString()}</span>
                            </div>
                        </div>
                        ${server.error_message ? `<div class="error-message">${server.error_message}</div>` : ''}
                    </div>
                `).join('')}
            </div>

            <div class="last-updated">
                Last updated: ${new Date().toLocaleString()}
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                
                function refresh() {
                    vscode.postMessage({ command: 'refresh' });
                }
            </script>
        </body>
        </html>
        `;
    }

    private generateErrorHTML(error: any): string {
        return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>MCP Platform Status - Error</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                    margin: 0;
                    padding: 20px;
                    text-align: center;
                }
                .error-container {
                    max-width: 500px;
                    margin: 50px auto;
                    padding: 30px;
                    background-color: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 8px;
                }
                .error-icon {
                    font-size: 48px;
                    color: var(--vscode-errorForeground);
                    margin-bottom: 20px;
                }
                .error-title {
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    color: var(--vscode-errorForeground);
                }
                .error-message {
                    font-size: 16px;
                    margin-bottom: 20px;
                    color: var(--vscode-descriptionForeground);
                }
                .retry-button {
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                }
                .retry-button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <div class="error-title">Connection Error</div>
                <div class="error-message">
                    Failed to connect to MCP Platform. Please check your configuration and ensure the platform is running.
                </div>
                <button class="retry-button" onclick="retry()">Retry Connection</button>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                
                function retry() {
                    vscode.postMessage({ command: 'refresh' });
                }
            </script>
        </body>
        </html>
        `;
    }

    private getOverallStatus(servers: MCPServerStatus[]): string {
        if (servers.length === 0) return 'offline';
        
        const unhealthyCount = servers.filter(s => s.status === 'unhealthy' || s.status === 'offline').length;
        const degradedCount = servers.filter(s => s.status === 'degraded').length;
        
        if (unhealthyCount > 0) return 'unhealthy';
        if (degradedCount > 0) return 'degraded';
        return 'healthy';
    }

    getLastStatus(): MCPServerStatus[] {
        return this.lastStatus;
    }

    dispose(): void {
        if (this.statusPanel) {
            this.statusPanel.dispose();
        }
    }
}