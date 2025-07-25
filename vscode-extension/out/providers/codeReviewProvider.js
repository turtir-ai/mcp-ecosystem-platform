"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CodeReviewProvider = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
class CodeReviewProvider {
    constructor(mcpAPI, notificationManager) {
        this.mcpAPI = mcpAPI;
        this.notificationManager = notificationManager;
        this.activeReviews = new Map(); // file path -> review id
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('mcpPlatform');
    }
    async reviewWorkspace() {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            this.notificationManager.showWarning('No workspace folder is open');
            return;
        }
        const workspaceFolder = workspaceFolders[0];
        await this.reviewPath(workspaceFolder.uri.fsPath);
    }
    async reviewPath(fsPath) {
        const stat = fs.statSync(fsPath);
        if (stat.isDirectory()) {
            await this.reviewDirectory(fsPath);
        }
        else {
            await this.reviewFile(fsPath);
        }
    }
    async reviewDocument(document) {
        if (document.uri.scheme !== 'file') {
            this.notificationManager.showWarning('Can only review files from the file system');
            return;
        }
        await this.reviewFile(document.uri.fsPath, document.getText());
    }
    async reviewDirectory(dirPath) {
        await this.notificationManager.showProgress('Reviewing directory', async (progress) => {
            progress.report({ message: 'Starting directory review...' });
            const request = {
                repositoryPath: dirPath,
                reviewType: 'full'
            };
            try {
                const reviewId = await this.mcpAPI.startCodeReview(request);
                this.activeReviews.set(dirPath, reviewId);
                progress.report({ message: 'Review in progress...', increment: 50 });
                // Poll for results
                const result = await this.pollForResults(reviewId, progress);
                if (result) {
                    await this.handleReviewResults(dirPath, result);
                    progress.report({ message: 'Review completed', increment: 100 });
                }
            }
            catch (error) {
                this.notificationManager.logError('Directory review failed', error);
                throw error;
            }
            finally {
                this.activeReviews.delete(dirPath);
            }
        });
    }
    async reviewFile(filePath, content) {
        await this.notificationManager.showProgress(`Reviewing ${path.basename(filePath)}`, async (progress) => {
            progress.report({ message: 'Starting file review...' });
            const request = {
                filePath: filePath,
                content: content,
                reviewType: 'full'
            };
            try {
                const reviewId = await this.mcpAPI.startCodeReview(request);
                this.activeReviews.set(filePath, reviewId);
                progress.report({ message: 'Review in progress...', increment: 50 });
                // Poll for results
                const result = await this.pollForResults(reviewId, progress);
                if (result) {
                    await this.handleReviewResults(filePath, result);
                    progress.report({ message: 'Review completed', increment: 100 });
                }
            }
            catch (error) {
                this.notificationManager.logError('File review failed', error);
                throw error;
            }
            finally {
                this.activeReviews.delete(filePath);
            }
        });
    }
    async pollForResults(reviewId, progress) {
        const maxAttempts = 30; // 5 minutes max
        const pollInterval = 10000; // 10 seconds
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            try {
                const result = await this.mcpAPI.getReviewResults(reviewId);
                if (result.status === 'completed') {
                    return result;
                }
                else if (result.status === 'failed') {
                    throw new Error('Review failed on server');
                }
                // Still running, wait and try again
                if (progress) {
                    const progressPercent = Math.min(90, (attempt / maxAttempts) * 90);
                    progress.report({
                        message: `Review in progress... (${attempt + 1}/${maxAttempts})`,
                        increment: progressPercent
                    });
                }
                await new Promise(resolve => setTimeout(resolve, pollInterval));
            }
            catch (error) {
                this.notificationManager.logError(`Review polling failed (attempt ${attempt + 1})`, error);
                if (attempt === maxAttempts - 1) {
                    throw error;
                }
            }
        }
        throw new Error('Review timed out');
    }
    async handleReviewResults(path, result) {
        // Clear existing diagnostics for this path
        this.clearDiagnostics(path);
        // Add new diagnostics
        if (result.findings && result.findings.length > 0) {
            await this.addDiagnostics(result.findings);
        }
        // Show notification with results
        await this.notificationManager.showCodeReviewResults({
            securityScore: result.securityScore,
            qualityScore: result.qualityScore,
            findingsCount: result.findings?.length || 0
        });
        // Log detailed results
        this.notificationManager.logInfo(`Review completed for ${path}`);
        this.notificationManager.logInfo(`Security Score: ${result.securityScore}/10`);
        this.notificationManager.logInfo(`Quality Score: ${result.qualityScore}/10`);
        this.notificationManager.logInfo(`Findings: ${result.findings?.length || 0}`);
        if (result.summary) {
            this.notificationManager.logInfo(`Summary: ${result.summary}`);
        }
        if (result.recommendations && result.recommendations.length > 0) {
            this.notificationManager.logInfo('Recommendations:');
            result.recommendations.forEach((rec, index) => {
                this.notificationManager.logInfo(`  ${index + 1}. ${rec}`);
            });
        }
    }
    async addDiagnostics(findings) {
        const diagnosticsByFile = new Map();
        for (const finding of findings) {
            const fileUri = vscode.Uri.file(finding.file);
            if (!diagnosticsByFile.has(finding.file)) {
                diagnosticsByFile.set(finding.file, []);
            }
            const diagnostics = diagnosticsByFile.get(finding.file);
            const range = new vscode.Range(Math.max(0, finding.line - 1), Math.max(0, finding.column - 1), Math.max(0, finding.line - 1), Number.MAX_SAFE_INTEGER);
            const diagnostic = new vscode.Diagnostic(range, finding.message, this.getSeverity(finding.severity));
            diagnostic.source = 'MCP Platform';
            diagnostic.code = finding.category;
            if (finding.suggestion) {
                diagnostic.relatedInformation = [
                    new vscode.DiagnosticRelatedInformation(new vscode.Location(fileUri, range), `Suggestion: ${finding.suggestion}`)
                ];
            }
            diagnostics.push(diagnostic);
        }
        // Set diagnostics for each file
        for (const [filePath, diagnostics] of diagnosticsByFile) {
            const fileUri = vscode.Uri.file(filePath);
            this.diagnosticCollection.set(fileUri, diagnostics);
        }
    }
    getSeverity(severity) {
        switch (severity.toLowerCase()) {
            case 'error':
                return vscode.DiagnosticSeverity.Error;
            case 'warning':
                return vscode.DiagnosticSeverity.Warning;
            case 'info':
                return vscode.DiagnosticSeverity.Information;
            default:
                return vscode.DiagnosticSeverity.Hint;
        }
    }
    clearDiagnostics(path) {
        const stat = fs.statSync(path);
        if (stat.isDirectory()) {
            // Clear diagnostics for all files in directory
            this.diagnosticCollection.clear();
        }
        else {
            // Clear diagnostics for specific file
            const fileUri = vscode.Uri.file(path);
            this.diagnosticCollection.delete(fileUri);
        }
    }
    // Public methods for external use
    async getReviewHistory() {
        try {
            return await this.mcpAPI.getReviewHistory(20);
        }
        catch (error) {
            this.notificationManager.logError('Failed to get review history', error);
            return [];
        }
    }
    isReviewActive(path) {
        return this.activeReviews.has(path);
    }
    getActiveReviews() {
        return Array.from(this.activeReviews.keys());
    }
    dispose() {
        this.diagnosticCollection.dispose();
        this.activeReviews.clear();
    }
}
exports.CodeReviewProvider = CodeReviewProvider;
//# sourceMappingURL=codeReviewProvider.js.map