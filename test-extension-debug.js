// Extension debug test script
console.log('=== MCP Extension Debug Test ===');

// Test API connection
async function testAPIConnection() {
    const apiUrl = 'http://localhost:8009';
    
    console.log(`Testing API connection to: ${apiUrl}`);
    
    try {
        // Test health endpoint
        const healthResponse = await fetch(`${apiUrl}/health`);
        const healthData = await healthResponse.json();
        console.log('✅ Health endpoint:', healthData);
        
        // Test MCP status endpoint
        const statusResponse = await fetch(`${apiUrl}/api/v1/mcp/status`);
        const statusData = await statusResponse.json();
        console.log('✅ MCP Status endpoint:', statusData);
        
        // Test workflows endpoint
        const workflowsResponse = await fetch(`${apiUrl}/api/v1/workflows/`);
        const workflowsData = await workflowsResponse.json();
        console.log('✅ Workflows endpoint:', workflowsData);
        
        console.log('🎉 All API endpoints working!');
        
    } catch (error) {
        console.error('❌ API connection failed:', error);
    }
}

// Test extension configuration
function testExtensionConfig() {
    console.log('=== Extension Configuration Test ===');
    
    // Check if VS Code API is available
    if (typeof vscode !== 'undefined') {
        const config = vscode.workspace.getConfiguration('mcpEcosystem');
        console.log('Extension config:', {
            apiUrl: config.get('apiUrl'),
            autoRefresh: config.get('autoRefresh'),
            refreshInterval: config.get('refreshInterval')
        });
    } else {
        console.log('VS Code API not available - running in browser context');
    }
}

// Run tests
testExtensionConfig();
testAPIConnection();