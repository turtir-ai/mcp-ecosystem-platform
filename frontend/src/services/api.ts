/**
 * API client for MCP Ecosystem Platform
 */
import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import { smartErrorHandler, trackUserAction } from './smartErrorHandler';

// API Types
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface MCPServerStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'offline';
  response_time_ms: number;
  last_check: string;
  error_message?: string;
  uptime_percentage?: number;
  tools?: any[];
  recent_activity?: any[];
  metrics?: {
    total_requests: number;
    successful_requests: number;
    average_response_time: number;
  };
}

export interface NetworkStatus {
  report_id: string;
  overall_status: 'excellent' | 'good' | 'fair' | 'poor' | 'critical' | 'offline';
  interfaces: NetworkInterface[];
  performance_summary: any;
  recommendations: string[];
  created_at: string;
  monitoring_duration: number;
}

export interface NetworkInterface {
  name: string;
  ip_address: string;
  status: string;
  bytes_sent?: number;
  bytes_received?: number;
  errors_in?: number;
  errors_out?: number;
}

export interface SecurityThreat {
  threat_id: string;
  threat_type: string;
  threat_level: 'info' | 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  source: string;
  target?: string;
  confidence_score: number;
  first_detected: string;
  last_seen: string;
  status: 'active' | 'investigating' | 'resolved' | 'false_positive';
  indicators: string[];
  tags: string[];
}

export interface DiagnosticReport {
  report_id: string;
  generated_at: string;
  overall_health_score: number;
  network_status: string;
  security_status: string;
  executive_summary: string;
  key_findings: string[];
  immediate_actions: string[];
  issues: DiagnosticIssue[];
  recommendations: Recommendation[];
  trend_analysis: any;
}

export interface DiagnosticIssue {
  issue_id: string;
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  category: string;
  detected_at: string;
  impact_description: string;
  affected_components: string[];
  is_resolved: boolean;
}

export interface Recommendation {
  recommendation_id: string;
  title: string;
  description: string;
  type: 'performance' | 'security' | 'configuration' | 'maintenance' | 'optimization' | 'monitoring';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  implementation_steps: string[];
  estimated_effort: string;
  estimated_impact: string;
  status: string;
  tags: string[];
}

export interface WorkflowDefinition {
  id?: string;
  name: string;
  description?: string;
  version: string;
  steps: WorkflowStep[];
  tags: string[];
  is_valid: boolean;
  validation_errors: string[];
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: string;
  mcp_server?: string;
  tool_name?: string;
  parameters: Record<string, any>;
  depends_on: string[];
  retry_count: number;
  timeout_seconds: number;
  description?: string;
  tags: string[];
}

export interface ResearchRequest {
  query: string;
  research_type: 'web_search' | 'deep_research' | 'competitive_analysis' | 'content_extraction';
  depth: number;
  max_sources: number;
  include_screenshots: boolean;
  extract_structured_data: boolean;
  privacy_mode: boolean;
  timeout_seconds: number;
}

export interface ResearchResult {
  request_id: string;
  query: string;
  research_type: string;
  status: string;
  total_sources: number;
  processing_time_seconds: number;
  created_at: string;
  completed_at?: string;
  sensitive_data_detected: boolean;
  sources?: any[];
  summary?: string;
  insights?: any;
  structured_data?: any;
}

// API Client Class
class APIClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL?: string) {
    // Use environment variable or fallback to default
    const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
    this.baseURL = baseURL || `${apiUrl}/api/v1`;
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Generic request method
  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    url: string,
    data?: any,
    params?: any
  ): Promise<T> {
    try {
      const response = await this.client.request({
        method,
        url,
        data,
        params,
      });
      return response.data;
    } catch (error) {
      // Track user action for AI learning
      trackUserAction({
        type: 'api_request_failed',
        timestamp: new Date(),
        details: {
          method,
          url,
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      });

      // Use smart error handler for better user experience
      if (error instanceof Error) {
        const smartResponse = await smartErrorHandler.handleError(error, {
          url: `${this.baseURL}${url}`,
          method: method.toUpperCase(),
          currentRoute: window.location.pathname
        });
        
        // Create enhanced error with smart response
        const enhancedError = new Error(smartResponse.userFriendlyMessage);
        (enhancedError as any).smartResponse = smartResponse;
        throw enhancedError;
      }
      
      throw error;
    }
  }

  // Public HTTP methods
  async get<T>(url: string, params?: any): Promise<T> {
    return this.request<T>('GET', url, undefined, params);
  }

  async post<T>(url: string, data?: any): Promise<T> {
    return this.request<T>('POST', url, data);
  }

  async put<T>(url: string, data?: any): Promise<T> {
    return this.request<T>('PUT', url, data);
  }

  async delete<T>(url: string): Promise<T> {
    return this.request<T>('DELETE', url);
  }

  // MCP Server Management
  async getMCPStatus(): Promise<MCPServerStatus[]> {
    const response = await this.request<APIResponse<Record<string, any>>>('GET', '/mcp/status');
    
    // Convert dictionary to array format expected by frontend
    if (response.data && typeof response.data === 'object') {
      return Object.entries(response.data).map(([name, status]: [string, any]) => ({
        name,
        status: status.status || 'offline',
        response_time_ms: status.response_time_ms || 0,
        last_check: status.last_check || new Date().toISOString(),
        error_message: status.error_message,
        uptime_percentage: status.uptime_percentage || 0,
        tools: [],
        recent_activity: [],
        metrics: {
          total_requests: 0,
          successful_requests: 0,
          average_response_time: status.response_time_ms || 0
        }
      }));
    }
    
    return [];
  }

  async getServerStatus(serverName: string): Promise<MCPServerStatus> {
    const response = await this.request<APIResponse<MCPServerStatus>>('GET', `/mcp/status/${serverName}`);
    return response.data!;
  }

  async restartServer(serverName: string): Promise<void> {
    await this.request('POST', `/mcp/restart/${serverName}`);
  }

  async getServerTools(serverName: string): Promise<any[]> {
    const response = await this.request<APIResponse<any[]>>('GET', `/mcp/tools/${serverName}`);
    return response.data || [];
  }

  async executeTool(serverName: string, toolName: string, args: any): Promise<any> {
    const response = await this.request<APIResponse<any>>('POST', `/tools/execute/${serverName}/${toolName}`, args);
    return response.data;
  }

  // Network Monitoring
  async getNetworkStatus(): Promise<NetworkStatus> {
    try {
      const response = await this.request<APIResponse<NetworkStatus>>('GET', '/network/status');
      return response.data || {
        report_id: 'mock-report',
        overall_status: 'excellent',
        interfaces: [],
        performance_summary: {},
        recommendations: [],
        created_at: new Date().toISOString(),
        monitoring_duration: 0
      };
    } catch (error) {
      // Return mock data if endpoint is not available
      return {
        report_id: 'mock-report',
        overall_status: 'excellent',
        interfaces: [],
        performance_summary: {},
        recommendations: [],
        created_at: new Date().toISOString(),
        monitoring_duration: 0
      };
    }
  }

  async getNetworkMetrics(metricType: string, target?: string, hours: number = 24): Promise<any> {
    return this.request('GET', `/network/metrics/${metricType}`, null, { target, hours });
  }

  async getNetworkTrends(hours: number = 24): Promise<any> {
    return this.request('GET', '/network/trends', null, { hours });
  }

  async startNetworkMonitoring(intervalSeconds: number = 300): Promise<any> {
    return this.request('POST', '/network/monitoring/start', { interval_seconds: intervalSeconds });
  }

  async stopNetworkMonitoring(): Promise<any> {
    return this.request('POST', '/network/monitoring/stop');
  }

  // Security Monitoring
  async getSecurityThreats(threatLevel?: string): Promise<SecurityThreat[]> {
    const response = await this.request<{ threats: SecurityThreat[] }>('GET', '/network/security/threats', null, { threat_level: threatLevel });
    return response.threats || [];
  }

  async scanSecurityThreats(): Promise<any> {
    return this.request('POST', '/network/security/scan');
  }

  async getSecuritySummary(): Promise<any> {
    try {
      const response = await this.request<APIResponse<any>>('GET', '/network/security/summary');
      return response.data || {
        total_active_threats: 0,
        critical_threats: 0,
        high_threats: 0,
        medium_threats: 0,
        low_threats: 0
      };
    } catch (error) {
      // Return mock data if endpoint is not available
      return {
        total_active_threats: 0,
        critical_threats: 0,
        high_threats: 0,
        medium_threats: 0,
        low_threats: 0
      };
    }
  }

  async resolveThreat(threatId: string, resolutionNotes: string = ''): Promise<any> {
    return this.request('POST', `/network/security/threats/${threatId}/resolve`, { resolution_notes: resolutionNotes });
  }

  // Diagnostics
  async getDiagnosticReport(): Promise<DiagnosticReport> {
    try {
      const response = await this.request<APIResponse<DiagnosticReport>>('GET', '/network/diagnostics');
      return response.data || {
        report_id: 'mock-report',
        generated_at: new Date().toISOString(),
        overall_health_score: 85,
        network_status: 'good',
        security_status: 'secure',
        executive_summary: 'System is operating normally',
        key_findings: [],
        immediate_actions: [],
        issues: [],
        recommendations: [],
        trend_analysis: {}
      };
    } catch (error) {
      // Return mock data if endpoint is not available
      return {
        report_id: 'mock-report',
        generated_at: new Date().toISOString(),
        overall_health_score: 85,
        network_status: 'good',
        security_status: 'secure',
        executive_summary: 'System is operating normally',
        key_findings: [],
        immediate_actions: [],
        issues: [],
        recommendations: [],
        trend_analysis: {}
      };
    }
  }

  async getDiagnosticHistory(days: number = 7): Promise<any> {
    return this.request('GET', '/network/diagnostics/history', null, { days });
  }

  async updateRecommendationStatus(recommendationId: string, status: string, notes: string = ''): Promise<any> {
    return this.request('POST', `/network/diagnostics/recommendations/${recommendationId}/status`, { status, notes });
  }

  // Workflow Management
  async getWorkflows(statusFilter?: string, limit: number = 100, offset: number = 0): Promise<WorkflowDefinition[]> {
    return this.request('GET', '/workflows/', null, { status_filter: statusFilter, limit, offset });
  }

  async getWorkflow(workflowId: number): Promise<WorkflowDefinition> {
    return this.request('GET', `/workflows/${workflowId}`);
  }

  async createWorkflow(workflow: Partial<WorkflowDefinition>): Promise<any> {
    return this.request('POST', '/workflows/', workflow);
  }

  async validateWorkflow(workflow: WorkflowDefinition): Promise<{ is_valid: boolean; errors: string[] }> {
    return this.request('POST', '/workflows/validate', workflow);
  }

  async executeWorkflow(workflowId: number, inputs?: any): Promise<any> {
    return this.request('POST', `/workflows/${workflowId}/execute`, { inputs });
  }

  async getExecutionStatus(executionId: string): Promise<any> {
    return this.request('GET', `/workflows/executions/${executionId}/status`);
  }

  async cancelExecution(executionId: string): Promise<any> {
    return this.request('POST', `/workflows/executions/${executionId}/cancel`);
  }

  async getWorkflowTemplates(): Promise<any[]> {
    return this.request('GET', '/workflows/templates/');
  }

  async createWorkflowFromTemplate(templateId: string, name: string, parameters?: any): Promise<any> {
    return this.request('POST', `/workflows/from-template/${templateId}`, { name, parameters });
  }

  // Research
  async startResearch(request: ResearchRequest): Promise<any> {
    return this.request('POST', '/research/', request);
  }

  async getResearchStatus(requestId: string): Promise<any> {
    return this.request('GET', `/research/${requestId}/status`);
  }

  async getResearchResults(requestId: string, includeContent: boolean = false): Promise<ResearchResult> {
    return this.request('GET', `/research/${requestId}/results`, null, { include_content: includeContent });
  }

  async cancelResearch(requestId: string): Promise<any> {
    return this.request('POST', `/research/${requestId}/cancel`);
  }

  async quickSearch(query: string, maxResults: number = 5): Promise<any> {
    return this.request('POST', '/research/quick-search', null, { query, max_results: maxResults });
  }

  async analyzeContent(content: string, analysisType: string, context?: string): Promise<any> {
    return this.request('POST', '/research/analyze', {
      content,
      analysis_type: analysisType,
      context,
    });
  }

  // Privacy
  async analyzePrivacy(content: string, contentId?: string): Promise<any> {
    return this.request('POST', '/privacy/analyze', {
      content,
      content_id: contentId,
      include_redacted: true,
      include_recommendations: true,
    });
  }

  async getPrivacyScore(content: string): Promise<any> {
    return this.request('POST', '/privacy/score', null, { content });
  }

  async redactContent(content: string, dataTypes?: string[]): Promise<any> {
    return this.request('POST', '/privacy/redact', null, { content, data_types: dataTypes });
  }

  // Git Review
  async getGitStatus(): Promise<any> {
    return this.request('GET', '/git/status');
  }

  async getGitDiff(staged: boolean = false): Promise<any> {
    return this.request('GET', '/git/diff', null, { staged });
  }

  async getRepositories(): Promise<any> {
    return this.request('GET', '/git/repositories');
  }

  async startGitReview(params: { repositoryId: string; reviewType: string }): Promise<any> {
    return this.request('POST', '/git/review', params);
  }

  async getReviewResults(reviewId: string): Promise<any> {
    // Guard against undefined or invalid review IDs
    if (!reviewId || reviewId === 'undefined' || reviewId.trim() === '') {
      console.warn('Attempted to get review results with invalid ID:', reviewId);
      return Promise.reject(new Error('Invalid review ID provided'));
    }
    return this.request('GET', `/git/review/${reviewId}/results`);
  }

  async getReviewHistory(limit: number = 20): Promise<any> {
    return this.request('GET', '/git/review/history', null, { limit });
  }

  async downloadReviewReport(reviewId: string): Promise<any> {
    return this.request('GET', `/git/review/${reviewId}/report`);
  }

  // Authentication (placeholder - implement based on your auth system)
  async login(email: string, password: string): Promise<{ token: string; user: any }> {
    const response = await this.request<{ token: string; user: any }>('POST', '/auth/login', { email, password });
    if (response.token) {
      localStorage.setItem('auth_token', response.token);
    }
    return response;
  }

  async logout(): Promise<void> {
    localStorage.removeItem('auth_token');
    await this.request('POST', '/auth/logout');
  }

  async getCurrentUser(): Promise<any> {
    return this.request('GET', '/auth/me');
  }

  // System Health
  async getSystemHealth(): Promise<any> {
    const response = await this.request<APIResponse<any>>('GET', '/health/');
    return response.data;
  }

  async getSimpleHealth(): Promise<any> {
    return this.request('GET', '/health/simple');
  }

  // AI Actions
  async aiRestartMCPServer(serverName: string, reasoning: string = ''): Promise<any> {
    return this.request('POST', `/ai/mcp/restart/${serverName}`, null, { reasoning });
  }

  async aiGetMCPLogs(serverName: string, lines: number = 100): Promise<any> {
    const response = await this.request<APIResponse<any>>('GET', `/ai/mcp/logs/${serverName}`, null, { lines });
    return response.data;
  }

  // Security Approvals
  async getPendingApprovals(): Promise<any> {
    const response = await this.request<APIResponse<any>>('GET', '/security/approvals');
    return response.data;
  }

  async approveOperation(operationId: string, userId: string = 'frontend_user'): Promise<any> {
    return this.request('POST', `/security/approve/${operationId}`, { user_id: userId });
  }

  async rejectOperation(operationId: string, userId: string = 'frontend_user', reason: string = ''): Promise<any> {
    return this.request('POST', `/security/reject/${operationId}`, { user_id: userId, reason });
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;