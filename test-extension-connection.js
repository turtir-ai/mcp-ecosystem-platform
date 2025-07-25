// Extension bağlantı testi
console.log('=== MCP Extension Connection Test ===');

// 1. API URL'yi kontrol et
const config = vscode.workspace.getConfiguration('mcpPlatform');
const apiUrl = config.get('apiUrl', 'http://localhost:8001');
console.log('Configured API URL:', apiUrl);

// 2. Fetch ile direkt test
async function testConnection() {
    try {
        console.log('Testing connection to:', apiUrl + '/health');
        const response = await fetch(apiUrl + '/health');
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('Health check successful:', data);
        } else {
            console.error('Health check failed:', response.statusText);
        }
    } catch (error) {
        console.error('Connection error:', error);
    }
}

// 3. MCP status test
async function testMCPStatus() {
    try {
        console.log('Testing MCP status endpoint...');
        const response = await fetch(apiUrl + '/api/v1/mcp/status');
        console.log('MCP Status response:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('MCP Status data:', data);
        } else {
            console.error('MCP Status failed:', response.statusText);
        }
    } catch (error) {
        console.error('MCP Status error:', error);
    }
}

// Testleri çalıştır
testConnection();
testMCPStatus();

// Extension komutlarını test et
console.log('Available commands:');
vscode.commands.getCommands().then(commands => {
    const mcpCommands = commands.filter(cmd => cmd.startsWith('mcpPlatform'));
    console.log('MCP Platform commands:', mcpCommands);
});