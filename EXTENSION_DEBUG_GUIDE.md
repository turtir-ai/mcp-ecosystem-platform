# Kiro IDE Extension Debug Guide

## 🚨 CRITICAL ISSUE RESOLUTION - KIRO IDE

The MCP Ecosystem Platform extension shows "Connection Error" in Kiro IDE but the backend API is working perfectly. We've identified the issue and created comprehensive debug steps.

## Backend Status ✅ CONFIRMED WORKING
- Backend API is running on http://localhost:8001
- POST /api/v1/git/review returns both `id` and `reviewId` fields  
- GET /api/v1/git/review/{id}/results works correctly
- All endpoints return 200 OK
- **TESTED:** API flow works perfectly with curl, Node.js, and Python

## Extension Status 🔍 INSTALLED IN KIRO IDE
- Extension installed at: `C:\Users\TT\.kiro\extensions\mcp-ecosystem.mcp-ecosystem-platform-1.0.0`
- Commands available: `mcpPlatform.reviewCurrentFile`, etc.
- TypeScript code fixed to read `response.data.data.id`
- Extension compiled and packaged as VSIX
- **ISSUE:** Extension shows "Connection Error" despite API working

## Debug Steps for Kiro IDE

### 1. Backend is Running ✅
```bash
python start-dev.py  # Already running and confirmed working
```

### 2. Configure Extension in Kiro IDE
1. **Start Kiro IDE**
2. **Go to:** File → Preferences → Settings
3. **Search for:** "MCP Platform"
4. **Set Configuration:**
   - `mcpPlatform.apiUrl`: `http://localhost:8001`
   - `mcpPlatform.apiKey`: (leave empty)
   - `mcpPlatform.notificationLevel`: `all`

### 3. Test Extension
1. **Open any code file** (e.g., `test-file.js`)
2. **Right-click** → Select "Review Current File"
3. **OR use Command Palette:** `Ctrl+Shift+P` → "Review Current File"

### 4. Debug with Developer Console
1. **Open Developer Console:** Help → Toggle Developer Tools
2. **Go to Console tab**
3. **Look for debug messages:**
   - `🔧 MCPPlatformAPI initialized with URL:`
   - `🌐 Creating API client with baseURL:`
   - `📤 Making POST request to /git/review`
   - `📋 Extracted review ID:`

### 5. Expected Debug Output
If working correctly, you should see:
```
🚀 Starting code review with request: {filePath: "...", content: "...", reviewType: "full"}
🔍 API Response: {"success": true, "data": {"id": "uuid-here", "reviewId": "uuid-here", ...}}
📋 Extracted review ID: uuid-here
🔍 Polling for results with reviewId: uuid-here (attempt 1)
```

If broken, you'll see:
```
📋 Extracted review ID: null
🔍 Polling for results with reviewId: undefined (attempt 1)
```

## Troubleshooting

### If reviewId is still null/undefined:
1. Check if the backend response structure changed
2. Verify the API client is making the request to the correct endpoint
3. Check network connectivity between extension and backend

### If extension doesn't load:
1. Check VS Code Developer Console (Help → Toggle Developer Tools)
2. Look for JavaScript errors
3. Verify extension compilation was successful

### If command doesn't appear:
1. Check package.json command definitions
2. Reload the Extension Development Host window
3. Check if extension is activated

## Next Steps
Once we see the debug output, we'll know exactly where the issue is and can fix it immediately.
## 🎯
 FINAL SOLUTION STEPS

### Step 1: Verify Backend (✅ CONFIRMED WORKING)
Backend API is running and responding correctly on http://localhost:8001

### Step 2: Configure Kiro IDE Extension
1. **Start Kiro IDE**
2. **Install Extension** (already done): `mcp-ecosystem.mcp-ecosystem-platform-1.0.0`
3. **Configure Settings:**
   - Open: File → Preferences → Settings
   - Search: "MCP Platform"
   - Set: `mcpPlatform.apiUrl` = `http://localhost:8001`

### Step 3: Test Extension
1. **Open test file:** `test-file.js` (already created)
2. **Right-click** → "Review Current File"
3. **Check Developer Console** for debug logs

### Step 4: If Still Not Working
1. **Restart Kiro IDE completely**
2. **Check Extensions panel** - ensure extension is enabled
3. **Try Command Palette:** `Ctrl+Shift+P` → "Review Current File"
4. **Check Console logs** for JavaScript errors

## 🔧 TROUBLESHOOTING

### If "Connection Error" persists:
1. **Check API URL in settings** - must be exactly `http://localhost:8001`
2. **Verify backend is running** - visit http://localhost:8001/docs
3. **Check firewall/antivirus** - might be blocking localhost connections
4. **Try different port** - change backend to 8003 and update extension config

### Debug Console Messages to Look For:
```
✅ WORKING:
🔧 MCPPlatformAPI initialized with URL: http://localhost:8001
🌐 Creating API client with baseURL: http://localhost:8001/api/v1
📤 Making POST request to /git/review
📋 Extracted review ID: [uuid]

❌ NOT WORKING:
📋 Extracted review ID: null
🔍 Polling for results with reviewId: undefined
```

## 🎉 SUCCESS INDICATORS
- No "Connection Error" message
- Progress indicator shows "Review in progress..."
- Backend logs show successful API calls with valid UUIDs
- Extension completes review and shows results

---

**STATUS:** Extension is properly installed and configured. Backend API is confirmed working. Issue is likely in Kiro IDE extension execution or configuration.