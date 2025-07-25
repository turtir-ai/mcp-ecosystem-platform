# Kiro IDE Extension Debug Script
# Bu script extension sorunlarını debug etmek için kullanılır

Write-Host "🔧 Kiro IDE Extension Debug Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# 1. Backend API Status Check
Write-Host "`n1. Backend API Status Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/mcp/status" -Method GET
    Write-Host "✅ Backend API is running" -ForegroundColor Green
    Write-Host "MCP Status: $($response | ConvertTo-Json -Depth 2)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Backend API is not accessible: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please start the backend with: python start-dev.py" -ForegroundColor Yellow
    exit 1
}

# 2. Check if Kiro IDE is running
Write-Host "`n2. Checking Kiro IDE Process..." -ForegroundColor Yellow
$kiroProcess = Get-Process -Name "Kiro" -ErrorAction SilentlyContinue
if ($kiroProcess) {
    Write-Host "✅ Kiro IDE is running (PID: $($kiroProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Kiro IDE is not running" -ForegroundColor Red
    Write-Host "Please start Kiro IDE first" -ForegroundColor Yellow
}

# 3. Check Extension Installation
Write-Host "`n3. Checking Extension Installation..." -ForegroundColor Yellow
$extensionPath = "C:\Users\TT\.kiro\extensions\mcp-ecosystem.mcp-ecosystem-platform-1.0.0"
if (Test-Path $extensionPath) {
    Write-Host "✅ Extension is installed at: $extensionPath" -ForegroundColor Green
    
    # Check extension files
    $packageJsonPath = Join-Path $extensionPath "package.json"
    if (Test-Path $packageJsonPath) {
        Write-Host "✅ package.json exists" -ForegroundColor Green
    } else {
        Write-Host "❌ package.json missing" -ForegroundColor Red
    }
    
    $extensionJsPath = Join-Path $extensionPath "out\extension.js"
    if (Test-Path $extensionJsPath) {
        Write-Host "✅ extension.js exists" -ForegroundColor Green
    } else {
        Write-Host "❌ extension.js missing - extension not compiled" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Extension is not installed" -ForegroundColor Red
    Write-Host "Extension should be at: $extensionPath" -ForegroundColor Yellow
}

# 4. Test API Endpoints
Write-Host "`n4. Testing API Endpoints..." -ForegroundColor Yellow

# Test git review endpoint
try {
    $reviewRequest = @{
        repository_path = "."
        review_type = "full"
    } | ConvertTo-Json

    $reviewResponse = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/git/review" -Method POST -Body $reviewRequest -ContentType "application/json"
    Write-Host "✅ Git review endpoint working" -ForegroundColor Green
    Write-Host "Review ID: $($reviewResponse.data.id)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Git review endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Network Analysis MCP Server Check
Write-Host "`n5. Checking Network Analysis MCP Server..." -ForegroundColor Yellow
$networkMcpPath = "C:\Users\TT\CLONE\Kairos_The_Context_Keeper\network-analysis-mcp.py"
if (Test-Path $networkMcpPath) {
    Write-Host "✅ Network Analysis MCP Server exists" -ForegroundColor Green
} else {
    Write-Host "❌ Network Analysis MCP Server missing" -ForegroundColor Red
    Write-Host "Expected at: $networkMcpPath" -ForegroundColor Yellow
}

# 6. Python Environment Check
Write-Host "`n6. Checking Python Environment..." -ForegroundColor Yellow
$pythonPath = "C:\Users\TT\CLONE\Kairos_The_Context_Keeper\venv\Scripts\python.exe"
if (Test-Path $pythonPath) {
    Write-Host "✅ Python environment exists" -ForegroundColor Green
    try {
        $pythonVersion = & $pythonPath --version
        Write-Host "Python version: $pythonVersion" -ForegroundColor Gray
    } catch {
        Write-Host "❌ Python environment not working" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Python environment missing" -ForegroundColor Red
    Write-Host "Expected at: $pythonPath" -ForegroundColor Yellow
}

# 7. Recommendations
Write-Host "`n🎯 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Start Kiro IDE if not running" -ForegroundColor White
Write-Host "2. Open Settings → Search 'MCP Platform'" -ForegroundColor White
Write-Host "3. Set mcpPlatform.apiUrl to: http://localhost:8001" -ForegroundColor White
Write-Host "4. Open test-extension-config.js" -ForegroundColor White
Write-Host "5. Right-click → 'Review Current File'" -ForegroundColor White
Write-Host "6. Check Developer Console (Help → Toggle Developer Tools)" -ForegroundColor White

Write-Host "`n🔍 DEBUG COMMANDS:" -ForegroundColor Cyan
Write-Host "- Test API: curl http://localhost:8001/api/v1/mcp/status" -ForegroundColor Gray
Write-Host "- Check logs: Check Kiro IDE Developer Console" -ForegroundColor Gray
Write-Host "- Restart: Close Kiro IDE completely and restart" -ForegroundColor Gray

Write-Host "`n✅ Debug script completed!" -ForegroundColor Green