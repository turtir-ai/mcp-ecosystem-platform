/**
 * TypeScript type definitions for AI-enhanced health system
 * Enhanced with better type safety, generics, and comprehensive enums
 */

// Core Enums for better type safety
export enum ServerStatus {
  HEALTHY = 'HEALTHY',
  DEGRADED = 'DEGRADED',
  OFFLINE = 'OFFLINE',
  STARTING = 'STARTING',
  UNKNOWN = 'UNKNOWN'
}

export enum SystemHealthStatus {
  HEALTHY = 'healthy',
  UNHEALTHY = 'unhealthy',
  DEGRADED = 'degraded',
  UNKNOWN = 'unknown'
}

export enum InsightType {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

export enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

export enum RiskLevel {
  SAFE = 'safe',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum AIActionType {
  MCP_SERVER_RESTART = 'mcp_server_restart',
  MCP_SERVER_STOP = 'mcp_server_stop',
  MCP_SERVER_LOGS = 'mcp_server_logs',
  SYSTEM_HEALTH_CHECK = 'system_health_check',
  INVESTIGATE_PROCESSES = 'investigate_processes',
  RESTART_SERVICES = 'restart_services',
  AUTO_FIX_APPLY = 'auto_fix_apply',
  RESOURCE_OPTIMIZATION = 'resource_optimization'
}

export enum ApprovalStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXPIRED = 'expired'
}

// Enhanced interfaces with better type safety
export interface MCPServerHealth {
  status: ServerStatus;
  response_time_ms: number;
  uptime_percentage: number;
  last_check: string;
  error_message?: string;
  pid?: number;
  memoryUsageMb?: number;
  cpuUsagePercent?: number;
  lastHeartbeat?: string;
  errorCount?: number;
  server_name?: string;
  version?: string;
  capabilities?: string[];
  health_score?: number; // 0-100
}

export interface ActionableInsight<T = Record<string, any>> {
  id: string;
  type: InsightType;
  message: string;
  suggested_action?: AIActionType;
  server_name?: string;
  priority: Priority;
  can_auto_fix: boolean;
  risk_level: RiskLevel;
  reasoning?: string;
  estimated_fix_time?: string;
  impact_description?: string;
  affected_components?: string[];
  confidence_score?: number; // 0-100
  created_at: string;
  expires_at?: string;
  metadata?: T;
  tags?: string[];
  category?: 'performance' | 'security' | 'maintenance' | 'connectivity';
}

export enum RecommendationType {
  PERFORMANCE = 'performance',
  DATABASE = 'database',
  SECURITY = 'security',
  MAINTENANCE = 'maintenance',
  RESOURCE = 'resource',
  CONNECTIVITY = 'connectivity'
}

export interface SystemRecommendation<T = Record<string, any>> {
  id: string;
  type: RecommendationType;
  message: string;
  suggestion: string;
  priority: Priority;
  estimated_impact?: string;
  implementation_time?: string;
  metadata?: T;
  created_at: string;
  auto_applicable?: boolean;
}

export interface ResourceUsage {
  cpu_percent: number;
  memory_percent: number;
  disk_usage_percent: number;
  memory_available_gb?: number;
  disk_free_gb?: number;
  network_io?: {
    bytes_sent: number;
    bytes_recv: number;
  };
  process_count?: number;
  load_average?: number[];
  timestamp: string;
}

export interface ResourceThresholds {
  cpu_warning: number;
  cpu_critical: number;
  memory_warning: number;
  memory_critical: number;
  disk_warning: number;
  disk_critical: number;
}

export interface DatabaseInfo {
  status: SystemHealthStatus;
  latency_ms: number;
  connection_pool_active: number;
  connection_pool_max?: number;
  query_count_per_second?: number;
  slow_queries?: number;
  last_backup?: string;
  size_mb?: number;
}

export interface MCPServersInfo {
  status: SystemHealthStatus;
  active_count: number;
  total_count: number;
  unhealthy_servers: string[];
  server_details: Record<string, MCPServerHealth>;
  average_response_time?: number;
  total_requests?: number;
  error_rate?: number;
}

export interface SystemServices {
  database: DatabaseInfo;
  mcp_servers: MCPServersInfo;
  external_apis?: Record<string, {
    status: SystemHealthStatus;
    response_time_ms: number;
    last_check: string;
  }>;
}

export interface HealthResponse<T = Record<string, any>> {
  status: SystemHealthStatus;
  timestamp: string;
  version: string;
  services: SystemServices;
  resource_usage: ResourceUsage;
  actionable_insights: ActionableInsight<T>[];
  system_recommendations: SystemRecommendation<T>[];
  health_score: number; // 0-100 overall system health
  uptime_seconds: number;
  environment: 'development' | 'staging' | 'production';
}

export interface SystemStatus<T = Record<string, any>> {
  backend: {
    status: SystemHealthStatus;
    url: string;
    version?: string;
    lastChecked: Date;
    resourceUsage?: ResourceUsage;
    response_time_ms?: number;
  };
  frontend: {
    status: 'running' | 'error' | 'loading';
    version: string;
    build_time?: string;
    features_enabled?: string[];
  };
  mcpServers: MCPServerHealth[];
  actionableInsights: ActionableInsight<T>[];
  overall_health_score?: number;
  last_updated: string;
}

// Enhanced AI Action interfaces with better type safety
export interface AIApprovalRequest<T = Record<string, any>> {
  operation_id: string;
  operation_type: AIActionType;
  parameters: T;
  risk_level: RiskLevel;
  reason: string;
  ai_reasoning?: string;
  timestamp: string;
  status: ApprovalStatus;
  requester: string;
  timeout_minutes: number;
  affected_systems?: string[];
  rollback_plan?: string;
  estimated_duration?: string;
  prerequisites?: string[];
}

export interface AIActionResponse<T = any> {
  success: boolean;
  error?: string;
  operation_id?: string;
  data?: {
    approval_required?: boolean;
    approval_request?: AIApprovalRequest<T>;
    reason?: string;
    risk_level?: RiskLevel;
    message?: string;
    reasoning?: string;
    execution_time_ms?: number;
    affected_components?: string[];
  };
}

export interface AIActionResult<T = any> {
  operation_id: string;
  success: boolean;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  result?: T;
  error?: string;
  logs?: string[];
  rollback_available?: boolean;
}

// Enhanced API Response wrapper with better error handling
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
  request_id?: string;
  execution_time_ms?: number;
}

export interface PaginatedResponse<T> extends APIResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Utility types for better type safety
export type HealthMetric = keyof ResourceUsage;
export type ServerHealthField = keyof MCPServerHealth;
export type InsightField = keyof ActionableInsight;

// Type guards for runtime type checking
export const isServerStatus = (status: string): status is ServerStatus => {
  return Object.values(ServerStatus).includes(status as ServerStatus);
};

export const isSystemHealthStatus = (status: string): status is SystemHealthStatus => {
  return Object.values(SystemHealthStatus).includes(status as SystemHealthStatus);
};

export const isRiskLevel = (level: string): level is RiskLevel => {
  return Object.values(RiskLevel).includes(level as RiskLevel);
};

export const isAIActionType = (action: string): action is AIActionType => {
  return Object.values(AIActionType).includes(action as AIActionType);
};

// Generic event types for real-time updates
export interface HealthEvent<T = any> {
  type: 'health_update' | 'insight_created' | 'action_completed' | 'server_status_changed';
  timestamp: string;
  data: T;
  source: string;
}

export interface SystemAlert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  auto_resolve: boolean;
  related_insight_id?: string;
  related_server?: string;
  suggested_actions?: string[];
}

// Configuration types
export interface HealthCheckConfig {
  intervals: {
    health_check_seconds: number;
    mcp_server_check_seconds: number;
    resource_check_seconds: number;
  };
  thresholds: ResourceThresholds;
  ai_settings: {
    auto_fix_enabled: boolean;
    approval_timeout_minutes: number;
    max_concurrent_actions: number;
    risk_tolerance: RiskLevel;
  };
}

// Export all enums as const assertions for better tree-shaking
export const SERVER_STATUS = ServerStatus;
export const SYSTEM_HEALTH_STATUS = SystemHealthStatus;
export const INSIGHT_TYPE = InsightType;
export const PRIORITY = Priority;
export const RISK_LEVEL = RiskLevel;
export const AI_ACTION_TYPE = AIActionType;
export const APPROVAL_STATUS = ApprovalStatus;
export const RECOMMENDATION_TYPE = RecommendationType;