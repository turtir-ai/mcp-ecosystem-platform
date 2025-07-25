import React, { useState, useEffect } from 'react';
import { Button, Typography, Box, Alert } from '@mui/material';
import apiClient from '../services/api';

const ConnectionTest: React.FC = () => {
  const [status, setStatus] = useState<'testing' | 'success' | 'error'>('testing');
  const [message, setMessage] = useState('Testing connection...');

  const testConnection = async () => {
    setStatus('testing');
    setMessage('Testing connection...');
    
    try {
      // Test basic API health
      const response = await fetch('/api/v1/health');
      if (response.ok) {
        const data = await response.json();
        setStatus('success');
        setMessage(`Connected successfully! API version: ${data.data?.api_version || 'v1'}`);
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error: any) {
      setStatus('error');
      setMessage(`Connection failed: ${error.message}`);
      
      // Try alternative connection methods
      try {
        const directResponse = await fetch('http://localhost:8001/api/v1/health');
        if (directResponse.ok) {
          setMessage(`Proxy issue detected. Direct connection works. Check package.json proxy setting.`);
        }
      } catch (directError) {
        setMessage(`Connection failed: ${error.message}. Backend may not be running on port 8001.`);
      }
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  return (
    <Box sx={{ p: 3, textAlign: 'center' }}>
      <Typography variant="h5" gutterBottom>
        Connection Test
      </Typography>
      
      <Alert severity={status === 'success' ? 'success' : status === 'error' ? 'error' : 'info'} sx={{ mb: 2 }}>
        {message}
      </Alert>
      
      <Button variant="contained" onClick={testConnection} disabled={status === 'testing'}>
        Retry Connection
      </Button>
      
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Expected backend URL: /api/v1 (proxied to http://localhost:8001)
        </Typography>
      </Box>
    </Box>
  );
};

export default ConnectionTest;