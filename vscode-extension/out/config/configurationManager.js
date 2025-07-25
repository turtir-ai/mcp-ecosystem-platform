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
exports.ConfigurationManager = void 0;
const vscode = __importStar(require("vscode"));
class ConfigurationManager {
    constructor() {
        this.refresh();
    }
    refresh() {
        this.config = vscode.workspace.getConfiguration('mcpPlatform');
    }
    getApiUrl() {
        return this.config.get('apiUrl', 'http://localhost:8001');
    }
    getApiKey() {
        return this.config.get('apiKey', '');
    }
    getAutoReview() {
        return this.config.get('autoReview', false);
    }
    getShowStatusBar() {
        return this.config.get('showStatusBar', true);
    }
    getNotificationLevel() {
        return this.config.get('notificationLevel', 'warnings');
    }
    async setApiUrl(url) {
        await this.config.update('apiUrl', url, vscode.ConfigurationTarget.Global);
        this.refresh();
    }
    async setApiKey(key) {
        await this.config.update('apiKey', key, vscode.ConfigurationTarget.Global);
        this.refresh();
    }
    async setAutoReview(enabled) {
        await this.config.update('autoReview', enabled, vscode.ConfigurationTarget.Workspace);
        this.refresh();
    }
    async setShowStatusBar(show) {
        await this.config.update('showStatusBar', show, vscode.ConfigurationTarget.Global);
        this.refresh();
    }
    async setNotificationLevel(level) {
        await this.config.update('notificationLevel', level, vscode.ConfigurationTarget.Global);
        this.refresh();
    }
    // Validation methods
    isConfigured() {
        const apiUrl = this.getApiUrl();
        return apiUrl && apiUrl !== 'http://localhost:8009' || this.getApiKey() !== '';
    }
    validateConfiguration() {
        const errors = [];
        const apiUrl = this.getApiUrl();
        if (!apiUrl) {
            errors.push('API URL is required');
        }
        else if (!this.isValidUrl(apiUrl)) {
            errors.push('API URL is not valid');
        }
        return errors;
    }
    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        }
        catch {
            return false;
        }
    }
    // Get all configuration as object
    getAllConfig() {
        return {
            apiUrl: this.getApiUrl(),
            apiKey: this.getApiKey() ? '***' : '',
            autoReview: this.getAutoReview(),
            showStatusBar: this.getShowStatusBar(),
            notificationLevel: this.getNotificationLevel()
        };
    }
}
exports.ConfigurationManager = ConfigurationManager;
//# sourceMappingURL=configurationManager.js.map