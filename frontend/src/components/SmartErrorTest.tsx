/**
 * Smart Error Handler Test Component
 * 
 * Bu component, Smart Error Handler'ın çalışmasını test etmek için
 * çeşitli hata senaryolarını simüle eder.
 */

import React, { useState } from 'react';
import { smartErrorHandler, trackUserAction } from '../services/smartErrorHandler';
import { smartNotifications } from '../services/smartNotifications';
import apiService from '../services/api';

interface TestResult {
  scenario: string;
  success: boolean;
  message: string;
  timestamp: Date;
}

export const SmartErrorTest: React.FC = () => {
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const addTestResult = (scenario: string, success: boolean, message: string) => {
    setTestResults(prev => [...prev, {
      scenario,
      success,
      message,
      timestamp: new Date()
    }]);
  };

  const testConnectionError = async () => {
    try {
      // Simulate connection error
      const error = new Error('ERR_CONNECTION_REFUSED');
      (error as any).code = 'ERR_CONNECTION_REFUSED';
      
      const smartResponse = await smartErrorHandler.handleError(error, {
        url: 'http://localhost:8001/api/v1/health',
        method: 'GET',
        currentRoute: '/dashboard'
      });

      // Show AI analysis notification
      smartNotifications.showAIAnalysis(smartResponse);
      
      addTestResult(
        'Connection Error', 
        true, 
        `AI Analysis: ${smartResponse.userFriendlyMessage}`
      );
    } catch (error) {
      addTestResult('Connection Error', false, `Test failed: ${error}`);
    }
  };

  const testTimeoutError = async () => {
    try {
      const error = new Error('timeout of 5000ms exceeded');
      (error as any).code = 'ECONNABORTED';
      
      const smartResponse = await smartErrorHandler.handleError(error, {
        url: 'http://localhost:8001/api/v1/mcp/status',
        method: 'GET',
        currentRoute: '/dashboard'
      });

      smartNotifications.showAIAnalysis(smartResponse);
      
      addTestResult(
        'Timeout Error', 
        true, 
        `AI Analysis: ${smartResponse.userFriendlyMessage}`
      );
    } catch (error) {
      addTestResult('Timeout Error', false, `Test failed: ${error}`);
    }
  };

  const testServerError = async () => {
    try {
      const error = new Error('Internal Server Error');
      (error as any).response = {
        status: 500,
        data: { detail: 'Internal server error occurred' }
      };
      
      const smartResponse = await smartErrorHandler.handleError(error, {
        url: 'http://localhost:8001/api/v1/health',
        method: 'GET',
        currentRoute: '/dashboard'
      });

      smartNotifications.showAIAnalysis(smartResponse);
      
      addTestResult(
        'Server Error', 
        true, 
        `AI Analysis: ${smartResponse.userFriendlyMessage}`
      );
    } catch (error) {
      addTestResult('Server Error', false, `Test failed: ${error}`);
    }
  };

  const testRealAPIError = async () => {
    try {
      // Try to call a non-existent endpoint to trigger real error handling
      await apiService.get('/nonexistent-endpoint');
      addTestResult('Real API Error', false, 'Expected error did not occur');
    } catch (error) {
      // This should trigger the smart error handler
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      const hasSmartResponse = (error as any).smartResponse;
      
      addTestResult(
        'Real API Error', 
        hasSmartResponse ? true : false, 
        hasSmartResponse 
          ? `Smart Error Handler activated: ${errorMessage}`
          : `Traditional error handling: ${errorMessage}`
      );
    }
  };

  const testUserActionTracking = () => {
    // Track some user actions
    trackUserAction({
      type: 'button_click',
      timestamp: new Date(),
      details: { button: 'test_smart_error' }
    });

    trackUserAction({
      type: 'navigation',
      timestamp: new Date(),
      details: { from: '/dashboard', to: '/test' }
    });

    addTestResult(
      'User Action Tracking', 
      true, 
      'User actions tracked successfully'
    );
  };

  const runAllTests = async () => {
    setIsRunning(true);
    setTestResults([]);

    try {
      await testConnectionError();
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      await testTimeoutError();
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      await testServerError();
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      testUserActionTracking();
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      await testRealAPIError();
      
    } finally {
      setIsRunning(false);
    }
  };

  const clearResults = () => {
    setTestResults([]);
  };

  return (
    <div style={{ 
      padding: '20px', 
      maxWidth: '800px', 
      margin: '0 auto',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <h2 style={{ color: '#1f2937', marginBottom: '20px' }}>
        🤖 Smart Error Handler Test Suite
      </h2>
      
      <div style={{ marginBottom: '20px' }}>
        <p style={{ color: '#6b7280', marginBottom: '15px' }}>
          Bu test suite, AI-powered error handling sisteminin çalışmasını test eder.
          Her test farklı bir hata senaryosunu simüle eder ve AI'ın nasıl yanıt verdiğini gösterir.
        </p>
        
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={runAllTests}
            disabled={isRunning}
            style={{
              background: isRunning ? '#9ca3af' : '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              cursor: isRunning ? 'not-allowed' : 'pointer',
              fontWeight: '500'
            }}
          >
            {isRunning ? 'Running Tests...' : 'Run All Tests'}
          </button>
          
          <button
            onClick={testConnectionError}
            disabled={isRunning}
            style={{
              background: '#ef4444',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              cursor: isRunning ? 'not-allowed' : 'pointer'
            }}
          >
            Test Connection Error
          </button>
          
          <button
            onClick={testTimeoutError}
            disabled={isRunning}
            style={{
              background: '#f59e0b',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              cursor: isRunning ? 'not-allowed' : 'pointer'
            }}
          >
            Test Timeout Error
          </button>
          
          <button
            onClick={testRealAPIError}
            disabled={isRunning}
            style={{
              background: '#8b5cf6',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              cursor: isRunning ? 'not-allowed' : 'pointer'
            }}
          >
            Test Real API Error
          </button>
          
          <button
            onClick={clearResults}
            style={{
              background: '#6b7280',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Clear Results
          </button>
        </div>
      </div>

      {testResults.length > 0 && (
        <div style={{
          background: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ color: '#1f2937', marginBottom: '15px' }}>
            Test Results ({testResults.length})
          </h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {testResults.map((result, index) => (
              <div
                key={index}
                style={{
                  background: 'white',
                  border: `2px solid ${result.success ? '#10b981' : '#ef4444'}`,
                  borderRadius: '6px',
                  padding: '12px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px'
                }}
              >
                <div style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  background: result.success ? '#10b981' : '#ef4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>
                  {result.success ? '✓' : '✗'}
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    fontWeight: '600', 
                    color: '#1f2937',
                    marginBottom: '4px'
                  }}>
                    {result.scenario}
                  </div>
                  <div style={{ 
                    color: '#6b7280', 
                    fontSize: '14px',
                    marginBottom: '4px'
                  }}>
                    {result.message}
                  </div>
                  <div style={{ 
                    color: '#9ca3af', 
                    fontSize: '12px'
                  }}>
                    {result.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div style={{
        marginTop: '30px',
        padding: '15px',
        background: '#eff6ff',
        border: '1px solid #bfdbfe',
        borderRadius: '8px'
      }}>
        <h4 style={{ color: '#1e40af', marginBottom: '10px' }}>
          💡 Test Açıklamaları
        </h4>
        <ul style={{ color: '#1e40af', fontSize: '14px', lineHeight: '1.6' }}>
          <li><strong>Connection Error:</strong> Backend sunucusuna bağlantı kurulamadığında AI'ın nasıl analiz yaptığını test eder</li>
          <li><strong>Timeout Error:</strong> İstek zaman aşımına uğradığında AI'ın önerilerini test eder</li>
          <li><strong>Server Error:</strong> 5xx sunucu hatalarında AI'ın nasıl yanıt verdiğini test eder</li>
          <li><strong>Real API Error:</strong> Gerçek bir API isteği hatası ile smart error handler'ın entegrasyonunu test eder</li>
        </ul>
      </div>
    </div>
  );
};

export default SmartErrorTest;