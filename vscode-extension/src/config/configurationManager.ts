import * as vscode from 'vscode';

export class ConfigurationManager {
    private config!: vscode.WorkspaceConfiguration;

    constructor() {
        this.refresh();
    }

    refresh() {
        this.config = vscode.workspace.getConfiguration('mcpPlatform');
    }

    getApiUrl(): string {
        return this.config.get<string>('apiUrl', 'http://localhost:8001');
    }

    getApiKey(): string {
        return this.config.get<string>('apiKey', '');
    }

    getAutoReview(): boolean {
        return this.config.get<boolean>('autoReview', false);
    }

    getShowStatusBar(): boolean {
        return this.config.get<boolean>('showStatusBar', true);
    }

    getNotificationLevel(): 'none' | 'errors' | 'warnings' | 'all' {
        return this.config.get<'none' | 'errors' | 'warnings' | 'all'>('notificationLevel', 'warnings');
    }

    async setApiUrl(url: string): Promise<void> {
        await this.config.update('apiUrl', url, vscode.ConfigurationTarget.Global);
        this.refresh();
    }

    async setApiKey(key: string): Promise<void> {
        await this.config.update('apiKey', key, vscode.ConfigurationTarget.Global);
        this.refresh();
    }

    async setAutoReview(enabled: boolean): Promise<void> {
        await this.config.update('autoReview', enabled, vscode.ConfigurationTarget.Workspace);
        this.refresh();
    }

    async setShowStatusBar(show: boolean): Promise<void> {
        await this.config.update('showStatusBar', show, vscode.ConfigurationTarget.Global);
        this.refresh();
    }

    async setNotificationLevel(level: 'none' | 'errors' | 'warnings' | 'all'): Promise<void> {
        await this.config.update('notificationLevel', level, vscode.ConfigurationTarget.Global);
        this.refresh();
    }

    // Validation methods
    isConfigured(): boolean {
        const apiUrl = this.getApiUrl();
        return apiUrl && apiUrl !== 'http://localhost:8009' || this.getApiKey() !== '';
    }

    validateConfiguration(): string[] {
        const errors: string[] = [];
        
        const apiUrl = this.getApiUrl();
        if (!apiUrl) {
            errors.push('API URL is required');
        } else if (!this.isValidUrl(apiUrl)) {
            errors.push('API URL is not valid');
        }

        return errors;
    }

    private isValidUrl(url: string): boolean {
        try {
            new URL(url);
            return true;
        } catch {
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