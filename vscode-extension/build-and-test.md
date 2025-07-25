# MCP Ecosystem Platform VS Code Extension - Build & Test Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd mcp-ecosystem-platform/vscode-extension
npm install
```

### 2. Build Extension
```bash
npm run compile
```

### 3. Test Extension
```bash
# Run tests
npm test

# Or run in VS Code
# Press F5 to launch Extension Development Host
```

## 📦 Required Dependencies

Add these to package.json if not already present:

```bash
npm install --save-dev @types/mocha @types/glob glob mocha
```

## 🔧 Development Setup

### 1. Open Extension in VS Code
```bash
code mcp-ecosystem-platform/vscode-extension
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Development
- Press `F5` to launch Extension Development Host
- Or use `Ctrl+Shift+P` → "Debug: Start Debugging"

## 🧪 Testing Steps

### 1. Basic Functionality Test
1. Launch Extension Development Host (F5)
2. Open Command Palette (`Ctrl+Shift+P`)
3. Look for "MCP Platform" commands
4. Test basic commands:
   - `MCP Platform: Show Status`
   - `MCP Platform: Open Dashboard`

### 2. Configuration Test
1. Go to Settings (`Ctrl+,`)
2. Search for "MCP Platform"
3. Set API URL: `http://localhost:8001`
4. Check status bar for MCP indicator

### 3. Code Review Test
1. Open a code file
2. Right-click → "Review Current File"
3. Or use Command Palette → "MCP Platform: Review Current File"

### 4. Status Bar Test
1. Check bottom status bar for MCP indicator
2. Click on MCP status
3. Should show status panel

## 🐛 Troubleshooting

### Common Issues

1. **Extension not loading**
   - Check console for errors (`Help` → `Toggle Developer Tools`)
   - Ensure all dependencies are installed
   - Run `npm run compile`

2. **Commands not appearing**
   - Check package.json contributes section
   - Restart Extension Development Host

3. **API connection issues**
   - Verify MCP Platform is running on localhost:8001
   - Check API URL in settings
   - Look at Output panel → "MCP Platform"

### Debug Console
- Open `Help` → `Toggle Developer Tools`
- Check Console tab for errors
- Look for "MCP Platform" logs

## 📋 Pre-Release Checklist

- [ ] Extension loads without errors
- [ ] All commands are registered
- [ ] Status bar shows MCP indicator
- [ ] Configuration settings work
- [ ] API connection successful
- [ ] Code review functionality works
- [ ] Status panel displays correctly
- [ ] No console errors
- [ ] Tests pass

## 🚀 Package for Release

### 1. Install VSCE
```bash
npm install -g vsce
```

### 2. Package Extension
```bash
vsce package
```

This creates a `.vsix` file that can be:
- Installed locally: `code --install-extension mcp-ecosystem-platform-1.0.0.vsix`
- Published to marketplace
- Shared with others

## 📤 GitHub Release Preparation

### 1. Create Release Branch
```bash
git checkout -b release/vscode-extension-v1.0.0
git add mcp-ecosystem-platform/vscode-extension/
git commit -m "feat: Add VS Code extension for MCP Ecosystem Platform"
```

### 2. Create Release Package
```bash
cd mcp-ecosystem-platform/vscode-extension
npm run compile
vsce package
```

### 3. Test Package
```bash
code --install-extension mcp-ecosystem-platform-1.0.0.vsix
```

## 🎯 Next Steps After Testing

1. **If tests pass**: Create GitHub release with .vsix file
2. **If issues found**: Fix and retest
3. **For marketplace**: Submit to VS Code Marketplace
4. **Documentation**: Update main README with extension info

## 📝 Test Results Template

```
## VS Code Extension Test Results

### ✅ Passed Tests
- [ ] Extension loads successfully
- [ ] Commands registered correctly
- [ ] Status bar integration works
- [ ] Configuration panel functional
- [ ] API connectivity established
- [ ] Code review features work
- [ ] Status dashboard displays
- [ ] No critical errors

### ❌ Failed Tests
- [ ] Issue 1: Description
- [ ] Issue 2: Description

### 📊 Performance
- Load time: X seconds
- Memory usage: X MB
- API response time: X ms

### 🔧 Environment
- VS Code version: X.X.X
- Node.js version: X.X.X
- OS: Windows/Mac/Linux
- MCP Platform: Running/Not Running
```

Ready to test! 🚀