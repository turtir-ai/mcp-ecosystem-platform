// Final Extension Test Script
console.log('=== MCP Extension Final Test ===');

// Test all API endpoints
async function testAllEndpoints() {
    const baseUrl = 'http://localhost:8001';
    
    console.log(`Testing API endpoints on: ${baseUrl}`);
    
    const endpoints = [
        '/health',
        '/api/v1/mcp/status',
        '/api/v1/network/status',
        '/api/v1/workflows/'
    ];
    
    for (const endpoint of endpoints) {
        try {
            console.log(`\n🔍 Testing: ${endpoint}`);
            const response = await fetch(`${baseUrl}${endpoint}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log(`✅ ${endpoint}: SUCCESS`);
                console.log(`   Status: ${response.status}`);
                console.log(`   Data keys: ${Object.keys(data).join(', ')}`);
            } else {
                console.log(`❌ ${endpoint}: FAILED (${response.status})`);
            }
        } catch (error) {
            console.log(`❌ ${endpoint}: ERROR - ${error.message}`);
        }
    }
}

// Test extension configuration
function testExtensionConfig() {
    console.log('\n=== Extension Configuration Test ===');
    
    // Check if VS Code API is available
    if (typeof vscode !== 'undefined') {
        const config = vscode.workspace.getConfiguration('mcpEcosystem');
        console.log('✅ Extension config found:', {
            apiUrl: config.get('apiUrl'),
            autoRefresh: config.get('autoRefresh'),
            refreshInterval: config.get('refreshInterval')
        });
    } else {
        console.log('ℹ️ VS Code API not available - running in browser context');
        console.log('Expected configuration:');
        console.log('  mcpEcosystem.apiUrl: http://localhost:8001');
        console.log('  mcpEcosystem.autoRefresh: true');
        console.log('  mcpEcosystem.refreshInterval: 30000');
    }
}

// Test MCP status parsing
async function testMCPStatusParsing() {
    console.log('\n=== MCP Status Parsing Test ===');
    
    try {
        const response = await fetch('http://localhost:8001/api/v1/mcp/status');
        const data = await response.json();
        
        if (data.success && data.data) {
            const servers = data.data;
            const serverNames = Object.keys(servers);
            const activeServers = serverNames.filter(name => servers[name].status === 'healthy').length;
            
            console.log('✅ MCP Status parsing successful:');
            console.log(`   Total servers: ${serverNames.length}`);
            console.log(`   Active servers: ${activeServers}`);
            console.log(`   Server names: ${serverNames.join(', ')}`);
            
            // Show first server details
            if (serverNames.length > 0) {
                const firstServer = servers[serverNames[0]];
                console.log(`   Sample server (${serverNames[0]}):`, {
                    status: firstServer.status,
                    response_time: firstServer.response_time_ms + 'ms',
                    uptime: firstServer.uptime_percentage.toFixed(1) + '%'
                });
            }
        } else {
            console.log('❌ Invalid MCP status response format');
        }
    } catch (error) {
        console.log(`❌ MCP status parsing failed: ${error.message}`);
    }
}

// Run all tests
async function runAllTests() {
    testExtensionConfig();
    await testAllEndpoints();
    await testMCPStatusParsing();
    
    console.log('\n🎉 Extension test completed!');
    console.log('\n📋 Next steps:');
    console.log('1. Open Kiro IDE');
    console.log('2. Press Ctrl+Shift+P');
    console.log('3. Type "MCP Ecosystem" to see available commands');
    console.log('4. Try "MCP Ecosystem: Check Status" command');
    console.log('5. Use "MCP Ecosystem: Show Debug Output" to see logs');
}

// Start tests
runAllTests();