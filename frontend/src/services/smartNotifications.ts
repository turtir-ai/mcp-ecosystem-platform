/**
 * Smart Notifications Service
 * 
 * Provides AI-powered toast notifications with suggested actions
 * for system health issues and connection problems.
 */

import React from 'react';
// @ts-ignore
import { toast } from 'react-hot-toast';
import apiService from './api';
import { SystemAlert, ActionableInsight, AIActionType } from '../types/health';
import { SmartErrorResponse, ActionSuggestion } from './smartErrorHandler';

export interface SmartToastOptions {
  duration?: number;
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
  style?: React.CSSProperties;
  className?: string;
  icon?: string;
  id?: string;
}

export interface ConnectionLossAnalysis {
  component: string;
  error_details: string;
  timestamp: string;
  possible_causes: string[];
  suggested_solutions: string[];
  confidence: number;
}

export interface SmartNotification {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  aiGenerated: boolean;
  actionable: boolean;
  suggestedActions: ActionSuggestion[];
  learnFromUserAction: boolean;
  timestamp: Date;
  smartResponse?: SmartErrorResponse;
}

class SmartNotificationService {
  private activeToasts: Set<string> = new Set();
  private connectionAnalysisCache: Map<string, ConnectionLossAnalysis> = new Map();

  /**
   * Show a smart toast notification with AI-suggested actions
   */
  showSmartToast(
    message: string,
    type: 'success' | 'error' | 'warning' | 'info' = 'info',
    suggestedActions: string[] = [],
    options: SmartToastOptions = {}
  ): string {
    const toastId = options.id || `toast-${Date.now()}`;
    
    // Prevent duplicate toasts
    if (this.activeToasts.has(toastId)) {
      return toastId;
    }

    this.activeToasts.add(toastId);

    const toastOptions = {
      duration: options.duration || 6000,
      position: options.position || 'top-right' as const,
      style: {
        background: this.getToastBackground(type),
        color: '#fff',
        borderRadius: '8px',
        padding: '16px',
        maxWidth: '400px',
        ...options.style
      },
      className: options.className || '',
      icon: options.icon || this.getToastIcon(type),
      id: toastId
    };

    const toastContent = this.createToastContent(message, suggestedActions, type);

    const toastResult = toast.custom(toastContent, {
      ...toastOptions
    });
    
    // Track toast dismissal manually
    setTimeout(() => {
      this.activeToasts.delete(toastId);
    }, toastOptions.duration || 6000);

    return toastId;
  }

  /**
   * Show notification for system alert
   */
  showAlertNotification(alert: SystemAlert): string {
    const suggestedActions = alert.suggested_actions || [];
    const type = this.mapAlertSeverityToToastType(alert.severity);
    
    return this.showSmartToast(
      alert.message,
      type,
      suggestedActions,
      {
        id: `alert-${alert.id}`,
        duration: type === 'error' ? 10000 : 6000
      }
    );
  }

  /**
   * Show notification for actionable insight
   */
  showInsightNotification(insight: ActionableInsight): string {
    const actions = insight.suggested_action ? [insight.suggested_action] : [];
    const type = this.mapInsightTypeToToastType(insight.type);
    
    const message = insight.server_name 
      ? `${insight.message} (${insight.server_name})`
      : insight.message;
    
    return this.showSmartToast(
      message,
      type,
      actions,
      {
        id: `insight-${insight.id}`,
        duration: insight.priority === 'urgent' ? 12000 : 8000
      }
    );
  }

  /**
   * Analyze connection loss and show smart notification
   */
  async analyzeAndNotifyConnectionLoss(
    component: string, 
    errorDetails: string
  ): Promise<void> {
    try {
      // Check cache first
      const cacheKey = `${component}-${errorDetails}`;
      let analysis = this.connectionAnalysisCache.get(cacheKey);

      if (!analysis) {
        // Get AI analysis from backend
        const response = await apiService.post('/monitoring/analyze-connection-loss', {
          component,
          error_details: errorDetails
        });

        if ((response as any).success) {
          analysis = (response as any).data as ConnectionLossAnalysis;
          this.connectionAnalysisCache.set(cacheKey, analysis);
        }
      }

      if (analysis) {
        const message = `Connection lost to ${component}. AI suggests: ${analysis.possible_causes[0] || 'Unknown cause'}`;
        
        this.showSmartToast(
          message,
          'error',
          analysis.suggested_solutions,
          {
            id: `connection-loss-${component}`,
            duration: 10000
          }
        );
      } else {
        // Fallback notification
        this.showSmartToast(
          `Connection lost to ${component}`,
          'error',
          ['check_connection', 'restart_component'],
          {
            id: `connection-loss-${component}`,
            duration: 8000
          }
        );
      }
    } catch (error) {
      console.error('Failed to analyze connection loss:', error);
      
      // Show basic notification on analysis failure
      this.showSmartToast(
        `Connection lost to ${component}`,
        'error',
        ['check_connection'],
        {
          id: `connection-loss-${component}`,
          duration: 6000
        }
      );
    }
  }

  /**
   * Show notification for backend connection issues
   */
  notifyBackendConnectionIssue(errorMessage: string): void {
    this.analyzeAndNotifyConnectionLoss('Backend API', errorMessage);
  }

  /**
   * Show notification for MCP server issues
   */
  notifyMCPServerIssue(serverName: string, errorMessage: string): void {
    this.analyzeAndNotifyConnectionLoss(`MCP Server: ${serverName}`, errorMessage);
  }

  /**
   * Show notification for resource issues
   */
  notifyResourceIssue(resourceType: string, currentValue: number, threshold: number): void {
    const message = `${resourceType} usage is high: ${currentValue.toFixed(1)}% (threshold: ${threshold}%)`;
    const actions = resourceType === 'CPU' 
      ? ['investigate_processes', 'restart_services']
      : resourceType === 'Memory'
      ? ['restart_services', 'memory_cleanup']
      : ['cleanup_logs', 'disk_maintenance'];

    this.showSmartToast(
      message,
      'warning',
      actions,
      {
        id: `resource-${resourceType.toLowerCase()}`,
        duration: 8000
      }
    );
  }

  /**
   * Dismiss a specific toast
   */
  dismissToast(toastId: string): void {
    toast.dismiss(toastId);
    this.activeToasts.delete(toastId);
  }

  /**
   * Dismiss all active toasts
   */
  dismissAll(): void {
    toast.dismiss();
    this.activeToasts.clear();
  }

  /**
   * Clear analysis cache
   */
  clearCache(): void {
    this.connectionAnalysisCache.clear();
  }

  // Private helper methods

  private createToastContent(
    message: string, 
    suggestedActions: string[], 
    type: string
  ): React.ReactElement {
    return React.createElement('div', {
      className: 'smart-toast-content'
    }, [
      React.createElement('div', {
        key: 'message',
        className: 'smart-toast-message',
        style: { marginBottom: suggestedActions.length > 0 ? '12px' : '0' }
      }, message),
      
      suggestedActions.length > 0 && React.createElement('div', {
        key: 'actions',
        className: 'smart-toast-actions',
        style: {
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          marginTop: '8px'
        }
      }, suggestedActions.map((action, index) => 
        React.createElement('button', {
          key: index,
          className: 'smart-toast-action-btn',
          style: {
            background: 'rgba(255, 255, 255, 0.2)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '4px',
            padding: '4px 8px',
            color: '#fff',
            fontSize: '12px',
            cursor: 'pointer',
            transition: 'background 0.2s'
          },
          onClick: () => this.handleSimpleActionClick(action),
          onMouseEnter: (e: React.MouseEvent<HTMLButtonElement>) => {
            (e.target as HTMLButtonElement).style.background = 'rgba(255, 255, 255, 0.3)';
          },
          onMouseLeave: (e: React.MouseEvent<HTMLButtonElement>) => {
            (e.target as HTMLButtonElement).style.background = 'rgba(255, 255, 255, 0.2)';
          }
        }, this.formatActionText(action))
      ))
    ]);
  }

  private handleSimpleActionClick(action: string): void {
    // Emit custom event for action handling
    window.dispatchEvent(new CustomEvent('smart-toast-action', {
      detail: { action }
    }));
  }

  private formatActionText(action: string): string {
    return action
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  }

  private getToastBackground(type: string): string {
    switch (type) {
      case 'success': return '#10B981';
      case 'error': return '#EF4444';
      case 'warning': return '#F59E0B';
      case 'info': return '#3B82F6';
      default: return '#6B7280';
    }
  }

  private getToastIcon(type: string): string {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '📢';
    }
  }

  private mapAlertSeverityToToastType(severity: string): 'success' | 'error' | 'warning' | 'info' {
    switch (severity) {
      case 'critical':
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'info';
    }
  }

  private mapInsightTypeToToastType(type: string): 'success' | 'error' | 'warning' | 'info' {
    switch (type) {
      case 'critical':
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'info';
    }
  }

  /**
   * Show AI analysis result as notification
   */
  showAIAnalysis(smartResponse: SmartErrorResponse): string {
    const toastId = `ai-analysis-${Date.now()}`;
    
    // Create enhanced notification with AI insights
    const notification: SmartNotification = {
      id: toastId,
      message: smartResponse.userFriendlyMessage,
      type: this.mapSeverityToToastType(smartResponse.severity),
      aiGenerated: true,
      actionable: smartResponse.suggestedActions.length > 0,
      suggestedActions: smartResponse.suggestedActions,
      learnFromUserAction: true,
      timestamp: new Date(),
      smartResponse
    };

    return this.showEnhancedNotification(notification);
  }

  /**
   * Show action suggestion notification
   */
  showActionSuggestion(suggestion: ActionSuggestion, context?: string): string {
    const toastId = `action-suggestion-${Date.now()}`;
    
    const message = context 
      ? `${context}: ${suggestion.title}` 
      : suggestion.title;

    const notification: SmartNotification = {
      id: toastId,
      message,
      type: this.mapRiskLevelToToastType(suggestion.riskLevel),
      aiGenerated: true,
      actionable: true,
      suggestedActions: [suggestion],
      learnFromUserAction: true,
      timestamp: new Date()
    };

    return this.showEnhancedNotification(notification);
  }

  /**
   * Track user response to AI suggestions
   */
  trackUserResponse(notificationId: string, userAction: 'accepted' | 'dismissed' | 'ignored'): void {
    // Send feedback to backend for AI learning
    this.sendUserFeedback(notificationId, userAction);
    
    // Remove from active toasts
    this.activeToasts.delete(notificationId);
  }

  /**
   * Show enhanced notification with AI features
   */
  private showEnhancedNotification(notification: SmartNotification): string {
    const toastContent = this.createAIToastContent(notification);
    
    const toastOptions = {
      duration: notification.actionable ? 10000 : 6000, // Longer duration for actionable notifications
      position: 'top-right' as const,
      style: {
        background: this.getToastBackground(notification.type),
        color: '#fff',
        borderRadius: '12px',
        padding: '16px',
        maxWidth: '450px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
        border: notification.aiGenerated ? '2px solid #3B82F6' : 'none'
      },
      icon: notification.aiGenerated ? '🤖' : this.getToastIcon(notification.type),
      id: notification.id
    };

    this.activeToasts.add(notification.id);

    const toastResult = toast.custom(toastContent, toastOptions);
    
    // Auto-remove from tracking
    setTimeout(() => {
      this.activeToasts.delete(notification.id);
    }, toastOptions.duration);

    return notification.id;
  }

  /**
   * Create AI-enhanced toast content
   */
  private createAIToastContent(notification: SmartNotification): React.ReactElement {
    return React.createElement('div', {
      className: 'smart-notification',
      style: { display: 'flex', flexDirection: 'column', gap: '8px' }
    }, [
      // Header with AI badge
      React.createElement('div', {
        key: 'header',
        style: { display: 'flex', alignItems: 'center', gap: '8px' }
      }, [
        notification.aiGenerated && React.createElement('span', {
          key: 'ai-badge',
          style: {
            fontSize: '10px',
            background: 'rgba(59, 130, 246, 0.2)',
            color: '#3B82F6',
            padding: '2px 6px',
            borderRadius: '4px',
            fontWeight: 'bold'
          }
        }, 'AI'),
        React.createElement('span', {
          key: 'message',
          style: { flex: 1, fontSize: '14px', fontWeight: '500' }
        }, notification.message)
      ]),
      
      // AI Analysis details
      notification.smartResponse?.aiAnalysis && React.createElement('div', {
        key: 'analysis',
        style: { fontSize: '12px', opacity: 0.9, fontStyle: 'italic' }
      }, `Confidence: ${Math.round(notification.smartResponse.aiAnalysis.confidence * 100)}% • ${notification.smartResponse.aiAnalysis.rootCause}`),
      
      // Action buttons
      notification.actionable && React.createElement('div', {
        key: 'actions',
        style: { display: 'flex', gap: '8px', marginTop: '8px' }
      }, notification.suggestedActions.slice(0, 2).map((action, index) => 
        React.createElement('button', {
          key: `action-${index}`,
          onClick: () => this.handleActionClick(notification.id, action),
          style: {
            background: action.riskLevel === 'safe' ? '#10B981' : '#F59E0B',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            cursor: 'pointer',
            fontWeight: '500'
          }
        }, action.title)
      ))
    ]);
  }

  /**
   * Handle action button clicks
   */
  private handleActionClick(notificationId: string, action: ActionSuggestion): void {
    // Track user acceptance
    this.trackUserResponse(notificationId, 'accepted');
    
    // Execute action based on type
    switch (action.actionType) {
      case 'automatic':
        this.executeAutomaticAction(action);
        break;
      case 'ai_assisted':
        this.executeAIAssistedAction(action);
        break;
      case 'manual':
        this.showManualActionGuide(action);
        break;
    }
    
    // Dismiss the notification
    toast.dismiss(notificationId);
  }

  /**
   * Execute automatic actions
   */
  private executeAutomaticAction(action: ActionSuggestion): void {
    // Implementation for automatic actions
    console.log('Executing automatic action:', action);
  }

  /**
   * Execute AI-assisted actions
   */
  private executeAIAssistedAction(action: ActionSuggestion): void {
    // Implementation for AI-assisted actions
    console.log('Executing AI-assisted action:', action);
  }

  /**
   * Show manual action guide
   */
  private showManualActionGuide(action: ActionSuggestion): void {
    // Show detailed steps for manual actions
    if (action.steps) {
      const stepsMessage = `${action.description}\n\nSteps:\n${action.steps.map((step, i) => `${i + 1}. ${step}`).join('\n')}`;
      this.showSmartToast(stepsMessage, 'info', [], { duration: 15000 });
    }
  }

  /**
   * Send user feedback to backend
   */
  private async sendUserFeedback(notificationId: string, userAction: string): Promise<void> {
    try {
      // Send feedback to backend for AI learning
      await fetch('/api/v1/ai/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          notification_id: notificationId,
          user_action: userAction,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      console.warn('Failed to send user feedback:', error);
    }
  }

  /**
   * Map severity to toast type
   */
  private mapSeverityToToastType(severity: string): 'success' | 'error' | 'warning' | 'info' {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'info';
    }
  }

  /**
   * Map risk level to toast type
   */
  private mapRiskLevelToToastType(riskLevel: string): 'success' | 'error' | 'warning' | 'info' {
    switch (riskLevel) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      case 'safe': return 'success';
      default: return 'info';
    }
  }
}

// Export singleton instance
export const smartNotifications = new SmartNotificationService();

// React hook for using smart notifications
export const useSmartNotifications = () => {
  const React = require('react');
  
  React.useEffect(() => {
    const handleSmartAction = (event: CustomEvent) => {
      const { action } = event.detail;
      console.log('Smart toast action clicked:', action);
      
      // Handle common actions
      switch (action) {
        case 'mcp_server_restart':
          // Trigger server restart flow
          window.dispatchEvent(new CustomEvent('trigger-server-restart'));
          break;
        case 'investigate_processes':
          // Open process investigation
          window.dispatchEvent(new CustomEvent('trigger-process-investigation'));
          break;
        case 'check_connection':
          // Trigger connection check
          window.dispatchEvent(new CustomEvent('trigger-connection-check'));
          break;
        default:
          console.log('Unhandled action:', action);
      }
    };

    window.addEventListener('smart-toast-action', handleSmartAction as EventListener);
    
    return () => {
      window.removeEventListener('smart-toast-action', handleSmartAction as EventListener);
    };
  }, []);

  return {
    showSmartToast: smartNotifications.showSmartToast.bind(smartNotifications),
    showAlertNotification: smartNotifications.showAlertNotification.bind(smartNotifications),
    showInsightNotification: smartNotifications.showInsightNotification.bind(smartNotifications),
    analyzeAndNotifyConnectionLoss: smartNotifications.analyzeAndNotifyConnectionLoss.bind(smartNotifications),
    notifyBackendConnectionIssue: smartNotifications.notifyBackendConnectionIssue.bind(smartNotifications),
    notifyMCPServerIssue: smartNotifications.notifyMCPServerIssue.bind(smartNotifications),
    notifyResourceIssue: smartNotifications.notifyResourceIssue.bind(smartNotifications),
    dismissToast: smartNotifications.dismissToast.bind(smartNotifications),
    dismissAll: smartNotifications.dismissAll.bind(smartNotifications)
  };
};