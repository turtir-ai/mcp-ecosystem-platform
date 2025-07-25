# MCP Ecosystem Platform - VS Code Extension

A powerful VS Code extension that integrates with the MCP Ecosystem Platform to provide AI-powered code review, workflow automation, and development tools directly in your editor.

## Features

### 🔍 AI-Powered Code Review
- **Inline Code Review**: Review individual files or entire directories with AI-powered analysis
- **Security Scanning**: Detect API keys, secrets, and security vulnerabilities
- **Quality Assessment**: Get code quality scores and improvement suggestions
- **Real-time Diagnostics**: See issues highlighted directly in your code

### 🚀 Workflow Automation
- **Visual Workflow Execution**: Run complex workflows across multiple MCP servers
- **Progress Monitoring**: Track workflow execution with real-time progress updates
- **Quick Actions**: Execute common workflows like code review and security scans
- **Background Processing**: Workflows run in the background without blocking your work

### 📊 MCP Server Monitoring
- **Status Dashboard**: Monitor the health of all 11 MCP servers
- **Real-time Updates**: Get live status updates in the status bar
- **Server Management**: Restart servers and view detailed metrics
- **Performance Tracking**: Monitor response times and uptime

### 🎯 Smart Integration
- **Context-Aware Actions**: Right-click menus for file and folder operations
- **Auto-Review**: Automatically review code on save (configurable)
- **Command Palette**: Access all features through VS Code's command palette
- **Status Bar Integration**: Quick access to platform status and actions

## Installation

1. Install the extension from the VS Code Marketplace
2. Configure the MCP Platform API URL in settings
3. Optionally set an API key for authentication
4. Start using AI-powered development tools!

## Configuration

### Required Settings

- **API URL**: The URL of your MCP Platform instance
  ```json
  "mcpPlatform.apiUrl": "http://localhost:8001"
  ```

### Optional Settings

- **API Key**: Authentication key for the MCP Platform
  ```json
  "mcpPlatform.apiKey": "your-api-key-here"
  ```

- **Auto Review**: Automatically review code when files are saved
  ```json
  "mcpPlatform.autoReview": false
  ```

- **Status Bar**: Show MCP Platform status in the status bar
  ```json
  "mcpPlatform.showStatusBar": true
  ```

- **Notification Level**: Control which notifications are shown
  ```json
  "mcpPlatform.notificationLevel": "warnings"
  ```

## Usage

### Code Review

1. **Review Current File**: 
   - Use `Ctrl+Shift+P` → "MCP Platform: Review Current File"
   - Or right-click in editor → "Review Current File"

2. **Review Directory**:
   - Right-click on folder in Explorer → "Review Code with AI"
   - Or use Command Palette → "MCP Platform: Review Code"

3. **View Results**:
   - Issues appear as diagnostics in the Problems panel
   - Hover over highlighted code for details and suggestions
   - Click status bar notification to view full results

### Workflow Execution

1. **Run Workflow**:
   - Use Command Palette → "MCP Platform: Run Workflow"
   - Select from available workflows
   - Monitor progress in notification

2. **Quick Actions**:
   - Code review workflows
   - Security scan workflows
   - Custom automation workflows

### Status Monitoring

1. **View Status**:
   - Click MCP status in status bar
   - Or use Command Palette → "MCP Platform: Show Status"

2. **Refresh Status**:
   - Command Palette → "MCP Platform: Refresh Status"
   - Status updates automatically every 30 seconds

## Commands

| Command                         | Description                       |
| ------------------------------- | --------------------------------- |
| `mcpPlatform.reviewCode`        | Review selected code or directory |
| `mcpPlatform.reviewCurrentFile` | Review the currently open file    |
| `mcpPlatform.runWorkflow`       | Execute a workflow                |
| `mcpPlatform.openDashboard`     | Open MCP Platform web dashboard   |
| `mcpPlatform.showStatus`        | Show MCP server status panel      |
| `mcpPlatform.refreshStatus`     | Refresh server status             |

## Keyboard Shortcuts

- `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac): Review current file
- `Ctrl+Shift+W` (Windows/Linux) or `Cmd+Shift+W` (Mac): Run workflow
- `Ctrl+Shift+M` (Windows/Linux) or `Cmd+Shift+M` (Mac): Show MCP status

## Requirements

- VS Code 1.74.0 or higher
- MCP Ecosystem Platform running and accessible
- Network access to the MCP Platform API

## Supported File Types

The extension works with all programming languages, with enhanced support for:

- JavaScript/TypeScript (.js, .ts, .jsx, .tsx)
- Python (.py)
- Java (.java)
- C/C++ (.c, .cpp, .h, .hpp)
- C# (.cs)
- PHP (.php)
- Ruby (.rb)
- Go (.go)
- Rust (.rs)

## Troubleshooting

### Connection Issues

1. **Check API URL**: Ensure the MCP Platform URL is correct in settings
2. **Network Access**: Verify VS Code can reach the MCP Platform
3. **Platform Status**: Check if the MCP Platform is running
4. **Firewall**: Ensure no firewall is blocking the connection

### Authentication Issues

1. **API Key**: Verify the API key is correct (if using authentication)
2. **Permissions**: Ensure the API key has necessary permissions
3. **Token Expiry**: Check if the API key has expired

### Performance Issues

1. **Large Files**: Code review may take longer for large files/directories
2. **Network Latency**: High latency can slow down operations
3. **Server Load**: High MCP server load can affect response times

## Support

- **Documentation**: [MCP Platform Docs](http://localhost:8001/docs)
- **Issues**: Report issues on the project repository
- **Logs**: Check the "MCP Platform" output channel for detailed logs

## Contributing

We welcome contributions! Please see the contributing guidelines in the main repository.

## License

This extension is part of the MCP Ecosystem Platform project and is licensed under the same terms.

---

**Enjoy AI-powered development with MCP Ecosystem Platform!** 🚀