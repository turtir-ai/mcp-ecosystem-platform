#!/usr/bin/env node

/**
 * Simple test script to verify extension structure and basic functionality
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testing MCP Ecosystem Platform VS Code Extension...\n');

// Test 1: Check if all required files exist
console.log('📁 Checking file structure...');
const requiredFiles = [
    'package.json',
    'tsconfig.json',
    'src/extension.ts',
    'src/api/mcpPlatformAPI.ts',
    'src/config/configurationManager.ts',
    'src/ui/statusBarManager.ts',
    'src/ui/notificationManager.ts',
    'src/providers/codeReviewProvider.ts',
    'src/providers/workflowProvider.ts',
    'src/providers/mcpStatusProvider.ts'
];

let allFilesExist = true;
requiredFiles.forEach(file => {
    if (fs.existsSync(file)) {
        console.log(`  ✅ ${file}`);
    } else {
        console.log(`  ❌ ${file} - MISSING`);
        allFilesExist = false;
    }
});

// Test 2: Check package.json structure
console.log('\n📦 Checking package.json...');
try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    
    // Check required fields
    const requiredFields = ['name', 'displayName', 'version', 'engines', 'main', 'contributes'];
    requiredFields.forEach(field => {
        if (packageJson[field]) {
            console.log(`  ✅ ${field}: ${typeof packageJson[field] === 'object' ? 'defined' : packageJson[field]}`);
        } else {
            console.log(`  ❌ ${field} - MISSING`);
            allFilesExist = false;
        }
    });

    // Check commands
    if (packageJson.contributes && packageJson.contributes.commands) {
        console.log(`  ✅ Commands: ${packageJson.contributes.commands.length} defined`);
        packageJson.contributes.commands.forEach(cmd => {
            console.log(`    - ${cmd.command}: ${cmd.title}`);
        });
    }

    // Check configuration
    if (packageJson.contributes && packageJson.contributes.configuration) {
        console.log(`  ✅ Configuration: ${Object.keys(packageJson.contributes.configuration.properties || {}).length} settings`);
    }

} catch (error) {
    console.log(`  ❌ Error reading package.json: ${error.message}`);
    allFilesExist = false;
}

// Test 3: Check TypeScript configuration
console.log('\n🔧 Checking TypeScript configuration...');
try {
    const tsConfig = JSON.parse(fs.readFileSync('tsconfig.json', 'utf8'));
    if (tsConfig.compilerOptions) {
        console.log(`  ✅ TypeScript config valid`);
        console.log(`    - Target: ${tsConfig.compilerOptions.target}`);
        console.log(`    - Module: ${tsConfig.compilerOptions.module}`);
        console.log(`    - Output: ${tsConfig.compilerOptions.outDir}`);
    }
} catch (error) {
    console.log(`  ❌ Error reading tsconfig.json: ${error.message}`);
    allFilesExist = false;
}

// Test 4: Check main extension file
console.log('\n🚀 Checking main extension file...');
try {
    const extensionContent = fs.readFileSync('src/extension.ts', 'utf8');
    
    // Check for required exports
    if (extensionContent.includes('export function activate')) {
        console.log('  ✅ activate function exported');
    } else {
        console.log('  ❌ activate function missing');
        allFilesExist = false;
    }

    if (extensionContent.includes('export function deactivate')) {
        console.log('  ✅ deactivate function exported');
    } else {
        console.log('  ❌ deactivate function missing');
        allFilesExist = false;
    }

    // Check for command registrations
    if (extensionContent.includes('registerCommand')) {
        console.log('  ✅ Command registrations found');
    } else {
        console.log('  ❌ No command registrations found');
    }

} catch (error) {
    console.log(`  ❌ Error reading extension.ts: ${error.message}`);
    allFilesExist = false;
}

// Test 5: Check if build directory exists (after compilation)
console.log('\n🔨 Checking build output...');
if (fs.existsSync('out')) {
    console.log('  ✅ Build output directory exists');
    if (fs.existsSync('out/extension.js')) {
        console.log('  ✅ Main extension compiled');
    } else {
        console.log('  ⚠️  Extension not compiled yet (run: npm run compile)');
    }
} else {
    console.log('  ⚠️  Build output directory missing (run: npm run compile)');
}

// Final result
console.log('\n' + '='.repeat(50));
if (allFilesExist) {
    console.log('🎉 Extension structure looks good!');
    console.log('\n📋 Next steps:');
    console.log('1. Run: npm install');
    console.log('2. Run: npm run compile');
    console.log('3. Press F5 in VS Code to test');
    console.log('4. Test all commands and features');
    console.log('5. If everything works, create GitHub release');
} else {
    console.log('❌ Extension has issues that need to be fixed');
    console.log('\n🔧 Please fix the missing files/configurations above');
}
console.log('='.repeat(50));

// Create a simple installation guide
const installGuide = `# Quick Installation Guide

## For Development Testing:
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Click "..." → "Install from VSIX..."
4. Select the .vsix file after building

## For Local Installation:
\`\`\`bash
cd mcp-ecosystem-platform/vscode-extension
npm install
npm run compile
vsce package
code --install-extension mcp-ecosystem-platform-1.0.0.vsix
\`\`\`

## Configuration:
1. Open VS Code Settings (Ctrl+,)
2. Search for "MCP Platform"
3. Set API URL: http://localhost:8001
4. Optionally set API Key
5. Check status bar for MCP indicator

## Testing:
- Use Ctrl+Shift+P → "MCP Platform" commands
- Right-click files → MCP Platform options
- Check status bar for server status
`;

fs.writeFileSync('INSTALL.md', installGuide);
console.log('\n📝 Created INSTALL.md with setup instructions');

process.exit(allFilesExist ? 0 : 1);