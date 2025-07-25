"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MCPPlatformAPI = void 0;
const axios_1 = __importDefault(require("axios"));
class MCPPlatformAPI {
    constructor(configManager) {
        this.configManager = configManager;
        this.client = this.createClient();
    }
    createClient() {
        const baseURL = `${this.configManager.getApiUrl()}/api/v1`;
        console.log('🌐 Creating API client with baseURL:', baseURL);
        const client = axios_1.default.create({
            baseURL: baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        // Add request interceptor for authentication
        client.interceptors.request.use((config) => {
            const apiKey = this.configManager.getApiKey();
            if (apiKey) {
                config.headers.Authorization = `Bearer ${apiKey}`;
            }
            else {
                // For development, add a dummy token to bypass auth
                config.headers.Authorization = `Bearer dev-token`;
            }
            console.log('📤 API Request:', config.method?.toUpperCase(), config.url);
            return config;
        }, (error) => {
            console.error('❌ Request interceptor error:', error);
            return Promise.reject(error);
        });
        // Add response interceptor for error handling
        client.interceptors.response.use((response) => {
            console.log('📥 API Response:', response.status, response.config.url);
            return response;
        }, (error) => {
            console.error('❌ API Error:', error.response?.data || error.message);
            return Promise.reject(error);
        });
        return client;
    }
    updateConfiguration(configManager) {
        this.configManager = configManager;
        this.client = this.createClient();
    }
    // MCP Status endpoints
    async getMCPStatus() {
        try {
            const response = await this.client.get('/mcp/status');
            if (response.data.success && response.data.data) {
                // Convert backend format to expected format
                const servers = response.data.data;
                return Object.keys(servers).map(name => ({
                    name,
                    status: servers[name].status,
                    response_time_ms: servers[name].response_time_ms || 0,
                    last_check: servers[name].last_check || new Date().toISOString(),
                    error_message: servers[name].error_message,
                    uptime_percentage: servers[name].uptime_percentage || 0
                }));
            }
            return [];
        }
        catch (error) {
            console.error('Failed to get MCP status:', error);
            throw new Error('Failed to connect to MCP Platform');
        }
    }
    async getServerDetails(serverName) {
        try {
            const response = await this.client.get('/mcp/status');
            if (response.data.success && response.data.data) {
                const servers = response.data.data;
                const serverData = servers[serverName];
                if (serverData) {
                    return {
                        name: serverName,
                        status: serverData.status,
                        response_time_ms: serverData.response_time_ms || 0,
                        last_check: serverData.last_check || new Date().toISOString(),
                        error_message: serverData.error_message,
                        uptime_percentage: serverData.uptime_percentage || 0
                    };
                }
            }
            throw new Error(`Server ${serverName} not found`);
        }
        catch (error) {
            console.error(`Failed to get server details for ${serverName}:`, error);
            throw new Error(`Failed to get details for ${serverName}`);
        }
    }
    async restartServer(serverName) {
        try {
            const response = await this.client.post(`/mcp/restart/${serverName}`);
            return response.data.success;
        }
        catch (error) {
            console.error(`Failed to restart server ${serverName}:`, error);
            throw new Error(`Failed to restart ${serverName}`);
        }
    }
    // Code Review endpoints (mock implementations for now)
    async startCodeReview(request) {
        try {
            // Mock implementation - return a review ID
            const reviewId = `review-${Date.now()}`;
            console.log('🔍 Starting code review:', reviewId, request);
            return reviewId;
        }
        catch (error) {
            console.error('Failed to start code review:', error);
            throw new Error('Failed to start code review');
        }
    }
    async getReviewResults(reviewId) {
        try {
            // Mock implementation
            return {
                id: reviewId,
                status: 'completed',
                securityScore: 85,
                qualityScore: 90,
                findings: [],
                summary: 'Code review completed successfully',
                recommendations: ['Consider adding more comments', 'Improve error handling']
            };
        }
        catch (error) {
            console.error('Failed to get review results:', error);
            throw new Error('Failed to get review results');
        }
    }
    async getReviewHistory(limit = 10) {
        try {
            // Mock implementation
            return [];
        }
        catch (error) {
            console.error('Failed to get review history:', error);
            return [];
        }
    }
    // Workflow endpoints
    async getWorkflows() {
        try {
            const response = await this.client.get('/workflows/');
            if (response.data && Array.isArray(response.data)) {
                return response.data.map((workflow) => ({
                    id: workflow.id,
                    name: workflow.name,
                    description: workflow.description,
                    status: workflow.status,
                    is_valid: true
                }));
            }
            // Return mock data if no workflows found
            return [
                {
                    id: 'workflow-1',
                    name: 'Daily Health Check',
                    description: 'Automated daily system health monitoring',
                    status: 'active',
                    is_valid: true
                }
            ];
        }
        catch (error) {
            console.error('Failed to get workflows:', error);
            return [];
        }
    }
    async executeWorkflow(workflowId, inputs) {
        try {
            // Mock implementation
            return {
                execution_id: `exec-${Date.now()}`,
                status: 'running',
                started_at: new Date().toISOString(),
                progress: 0
            };
        }
        catch (error) {
            console.error('Failed to execute workflow:', error);
            throw new Error('Failed to execute workflow');
        }
    }
    async getWorkflowExecutionStatus(executionId) {
        try {
            // Mock implementation
            return {
                execution_id: executionId,
                status: 'completed',
                started_at: new Date().toISOString(),
                progress: 100
            };
        }
        catch (error) {
            console.error('Failed to get execution status:', error);
            throw new Error('Failed to get execution status');
        }
    }
    async cancelWorkflowExecution(executionId) {
        try {
            // Mock implementation
            return true;
        }
        catch (error) {
            console.error('Failed to cancel execution:', error);
            return false;
        }
    }
    // Health check
    async healthCheck() {
        try {
            const response = await this.client.get('/health');
            return response.status === 200;
        }
        catch (error) {
            return false;
        }
    }
    // Git operations (mock implementations)
    async getGitStatus() {
        try {
            // Mock implementation
            return {
                branch: 'main',
                changes: [],
                clean: true
            };
        }
        catch (error) {
            console.error('Failed to get git status:', error);
            return null;
        }
    }
    async getGitDiff(staged = false) {
        try {
            // Mock implementation
            return '';
        }
        catch (error) {
            console.error('Failed to get git diff:', error);
            return '';
        }
    }
}
exports.MCPPlatformAPI = MCPPlatformAPI;
//# sourceMappingURL=mcpPlatformAPI.js.map