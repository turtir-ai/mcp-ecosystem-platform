import * as vscode from 'vscode';
import { MCPPlatformAPI, MCPServerStatus } from '../api/mcpPlatformAPI';
import { ConfigurationManager } from '../config/configurationManager';

export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;
    private lastStatus: 'healthy' | 'degraded' | 'unhealthy' | 'offline' | 'unknown' = 'unknown';
    private serverCount: number = 0;
    private healthyCount: number = 0;

    constructor(
        private mcpAPI: MCPPlatformAPI,
        private configManager: ConfigurationManager
    ) {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
    }

    initialize() {
        if (this.configManager.getShowStatusBar()) {
            this.statusBarItem.show();
            this.refresh();
        }
    }

    async refresh() {
        if (!this.configManager.getShowStatusBar()) {
            this.statusBarItem.hide();
            return;
        }

        try {
            const servers = await this.mcpAPI.getMCPStatus();
            this.updateStatus(servers);
        } catch (error) {
            this.updateStatusError();
        }
    }

    private updateStatus(servers: MCPServerStatus[]) {
        this.serverCount = servers.length;
        this.healthyCount = servers.filter(s => s.status === 'healthy').length;
        
        const degradedCount = servers.filter(s => s.status === 'degraded').length;
        const unhealthyCount = servers.filter(s => s.status === 'unhealthy' || s.status === 'offline').length;

        // Determine overall status
        if (unhealthyCount > 0) {
            this.lastStatus = 'unhealthy';
        } else if (degradedCount > 0) {
            this.lastStatus = 'degraded';
        } else if (this.healthyCount > 0) {
            this.lastStatus = 'healthy';
        } else {
            this.lastStatus = 'unknown';
        }

        this.updateStatusBarItem();
    }

    private updateStatusError() {
        this.lastStatus = 'offline';
        this.serverCount = 0;
        this.healthyCount = 0;
        this.updateStatusBarItem();
    }

    private updateStatusBarItem() {
        const icon = this.getStatusIcon();
        const text = this.getStatusText();
        const tooltip = this.getStatusTooltip();
        const color = this.getStatusColor();

        this.statusBarItem.text = `${icon} ${text}`;
        this.statusBarItem.tooltip = tooltip;
        this.statusBarItem.color = color;
        this.statusBarItem.command = 'mcpPlatform.showStatus';

        this.statusBarItem.show();
    }

    private getStatusIcon(): string {
        switch (this.lastStatus) {
            case 'healthy':
                return '$(check)';
            case 'degraded':
                return '$(warning)';
            case 'unhealthy':
                return '$(error)';
            case 'offline':
                return '$(circle-slash)';
            default:
                return '$(pulse)';
        }
    }

    private getStatusText(): string {
        if (this.lastStatus === 'offline') {
            return 'MCP Offline';
        }
        
        if (this.serverCount === 0) {
            return 'MCP';
        }

        return `MCP ${this.healthyCount}/${this.serverCount}`;
    }

    private getStatusTooltip(): string {
        if (this.lastStatus === 'offline') {
            return 'MCP Platform is offline - check connection';
        }

        if (this.serverCount === 0) {
            return 'MCP Platform - No servers detected';
        }

        const statusSummary = [
            `${this.healthyCount} healthy`,
            `${this.serverCount - this.healthyCount} issues`
        ].join(', ');

        return `MCP Platform Status: ${statusSummary}\nClick to view details`;
    }

    private getStatusColor(): string | undefined {
        switch (this.lastStatus) {
            case 'healthy':
                return '#00ff00';
            case 'degraded':
                return '#ffff00';
            case 'unhealthy':
                return '#ff0000';
            case 'offline':
                return '#888888';
            default:
                return undefined;
        }
    }

    dispose() {
        this.statusBarItem.dispose();
    }

    // Public methods for external updates
    setConnecting() {
        this.statusBarItem.text = '$(sync~spin) MCP Connecting...';
        this.statusBarItem.tooltip = 'Connecting to MCP Platform...';
        this.statusBarItem.color = undefined;
    }

    setError(message: string) {
        this.statusBarItem.text = '$(error) MCP Error';
        this.statusBarItem.tooltip = `MCP Platform Error: ${message}`;
        this.statusBarItem.color = '#ff0000';
    }

    // Animation for active operations
    private animationInterval: NodeJS.Timeout | undefined;

    startAnimation(text: string = 'MCP Working') {
        this.stopAnimation();
        
        const frames = ['$(sync~spin)', '$(loading~spin)'];
        let frameIndex = 0;
        
        this.animationInterval = setInterval(() => {
            this.statusBarItem.text = `${frames[frameIndex]} ${text}`;
            frameIndex = (frameIndex + 1) % frames.length;
        }, 500);
    }

    stopAnimation() {
        if (this.animationInterval) {
            clearInterval(this.animationInterval);
            this.animationInterval = undefined;
        }
        this.updateStatusBarItem();
    }
}