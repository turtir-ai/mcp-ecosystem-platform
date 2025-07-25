# Change Log

All notable changes to the MCP Ecosystem Platform VS Code extension will be documented in this file.

## [1.0.0] - 2024-01-23

### Added
- Initial release of MCP Ecosystem Platform VS Code extension
- AI-powered code review with inline diagnostics
- Workflow execution and monitoring
- MCP server status monitoring and management
- Real-time status bar integration
- Comprehensive configuration options
- Command palette integration
- Context menu integration for files and folders
- Auto-review on file save (configurable)
- Progress notifications for long-running operations
- Detailed logging and error handling
- WebView-based status dashboard
- Support for all major programming languages

### Features
- **Code Review Integration**
  - Review individual files or entire directories
  - Security scanning for API keys and vulnerabilities
  - Code quality assessment with scoring
  - Real-time diagnostics in Problems panel
  - Hover tooltips with suggestions

- **Workflow Automation**
  - Visual workflow selection and execution
  - Real-time progress monitoring
  - Background execution without blocking editor
  - Quick actions for common workflows
  - Execution history and results

- **MCP Server Monitoring**
  - Real-time status updates in status bar
  - Detailed server health dashboard
  - Performance metrics and uptime tracking
  - Server restart capabilities
  - Error reporting and diagnostics

- **Smart Integration**
  - Context-aware right-click menus
  - Command palette integration
  - Keyboard shortcuts for common actions
  - Configurable notification levels
  - Output channel for detailed logging

### Configuration
- `mcpPlatform.apiUrl` - MCP Platform API URL
- `mcpPlatform.apiKey` - Authentication API key
- `mcpPlatform.autoReview` - Auto-review on save
- `mcpPlatform.showStatusBar` - Status bar visibility
- `mcpPlatform.notificationLevel` - Notification filtering

### Commands
- `mcpPlatform.reviewCode` - Review code or directory
- `mcpPlatform.reviewCurrentFile` - Review current file
- `mcpPlatform.runWorkflow` - Execute workflow
- `mcpPlatform.openDashboard` - Open web dashboard
- `mcpPlatform.showStatus` - Show status panel
- `mcpPlatform.refreshStatus` - Refresh status

### Requirements
- VS Code 1.74.0 or higher
- MCP Ecosystem Platform instance
- Network connectivity to MCP Platform API