// Extension konfigürasyonunu düzelt
console.log('=== Extension Configuration Fix ===');

// Kiro IDE'de extension ayarlarını kontrol et ve düzelt
const vscode = require('vscode');

async function fixExtensionConfig() {
    try {
        // Mevcut konfigürasyonu al
        const config = vscode.workspace.getConfiguration('mcpPlatform');
        const currentApiUrl = config.get('apiUrl');
        
        console.log('Current API URL:', currentApiUrl);
        
        // Doğru URL'yi ayarla
        const correctUrl = 'http://localhost:8001';
        
        if (currentApiUrl !== correctUrl) {
            console.log('Updating API URL to:', correctUrl);
            await config.update('apiUrl', correctUrl, vscode.ConfigurationTarget.Global);
            console.log('API URL updated successfully');
        } else {
            console.log('API URL is already correct');
        }
        
        // Diğer ayarları kontrol et
        const autoRefresh = config.get('autoRefresh');
        const refreshInterval = config.get('refreshInterval');
        const notificationLevel = config.get('notificationLevel');
        
        console.log('Configuration:');
        console.log('- API URL:', config.get('apiUrl'));
        console.log('- Auto Refresh:', autoRefresh);
        console.log('- Refresh Interval:', refreshInterval);
        console.log('- Notification Level:', notificationLevel);
        
        // Extension'ı yeniden başlat
        console.log('Reloading extension...');
        await vscode.commands.executeCommand('workbench.action.reloadWindow');
        
    } catch (error) {
        console.error('Configuration fix failed:', error);
    }
}

// Test API bağlantısı
async function testAPIConnection() {
    try {
        const apiUrl = 'http://localhost:8001';
        console.log('Testing API connection to:', apiUrl);
        
        const response = await fetch(apiUrl + '/health');
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API connection successful:', data.data.status);
        } else {
            console.error('❌ API connection failed:', response.status);
        }
        
        // MCP status test
        const mcpResponse = await fetch(apiUrl + '/api/v1/mcp/status');
        if (mcpResponse.ok) {
            const mcpData = await mcpResponse.json();
            console.log('✅ MCP status successful:', Object.keys(mcpData.data).length, 'servers');
        } else {
            console.error('❌ MCP status failed:', mcpResponse.status);
        }
        
    } catch (error) {
        console.error('❌ Connection test failed:', error);
    }
}

// Çalıştır
fixExtensionConfig();
testAPIConnection();