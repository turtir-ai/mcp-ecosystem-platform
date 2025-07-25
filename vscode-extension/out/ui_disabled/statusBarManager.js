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
exports.StatusBarManager = void 0;
const vscode = __importStar(require("vscode"));
class StatusBarManager {
    constructor(mcpAPI, configManager) {
        this.mcpAPI = mcpAPI;
        this.configManager = configManager;
        this.lastStatus = 'unknown';
        this.serverCount = 0;
        this.healthyCount = 0;
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
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
        }
        catch (error) {
            this.updateStatusError();
        }
    }
    updateStatus(servers) {
        this.serverCount = servers.length;
        this.healthyCount = servers.filter(s => s.status === 'healthy').length;
        const degradedCount = servers.filter(s => s.status === 'degraded').length;
        const unhealthyCount = servers.filter(s => s.status === 'unhealthy' || s.status === 'offline').length;
        // Determine overall status
        if (unhealthyCount > 0) {
            this.lastStatus = 'unhealthy';
        }
        else if (degradedCount > 0) {
            this.lastStatus = 'degraded';
        }
        else if (this.healthyCount > 0) {
            this.lastStatus = 'healthy';
        }
        else {
            this.lastStatus = 'unknown';
        }
        this.updateStatusBarItem();
    }
    updateStatusError() {
        this.lastStatus = 'offline';
        this.serverCount = 0;
        this.healthyCount = 0;
        this.updateStatusBarItem();
    }
    updateStatusBarItem() {
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
    getStatusIcon() {
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
    getStatusText() {
        if (this.lastStatus === 'offline') {
            return 'MCP Offline';
        }
        if (this.serverCount === 0) {
            return 'MCP';
        }
        return `MCP ${this.healthyCount}/${this.serverCount}`;
    }
    getStatusTooltip() {
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
    getStatusColor() {
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
    setError(message) {
        this.statusBarItem.text = '$(error) MCP Error';
        this.statusBarItem.tooltip = `MCP Platform Error: ${message}`;
        this.statusBarItem.color = '#ff0000';
    }
    startAnimation(text = 'MCP Working') {
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
exports.StatusBarManager = StatusBarManager;
//# sourceMappingURL=statusBarManager.js.map