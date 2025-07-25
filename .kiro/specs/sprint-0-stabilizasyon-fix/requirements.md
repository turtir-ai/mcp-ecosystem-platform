# VS Code Extension API Field Mismatch Fix

## User Story
As a developer, when I use the "Review Current File" feature in the VS Code extension, I want the code review to complete successfully and show me the results, so that I can use the AI-powered code analysis feature.

## Problem Statement
The VS Code extension shows "Connection Error" after attempting to start a code review. The root cause is a field name mismatch between backend and frontend:

- **Backend sends:** `{"data": {"id": "review-uuid", ...}}`
- **Frontend expects:** `{"data": {"reviewId": "review-uuid", ...}}`

This causes the frontend to receive `undefined` for the review ID, leading to invalid API calls like `/api/v1/git/review/undefined/results` which return 400 Bad Request errors.

## Acceptance Criteria

1. **WHEN** "Review Current File" command is executed **THEN** the review ID from backend response should be correctly parsed
2. **WHEN** review ID is obtained **THEN** the GET request to fetch results should contain a valid ID instead of `undefined`
3. **WHEN** the entire process completes **THEN** a successful result notification should be shown instead of "Connection Error"

## Success Metrics
- No more `400 Bad Request` errors for `/api/v1/git/review/undefined/results`
- VS Code extension successfully completes code review workflow
- Users can see actual review results instead of connection errors

## Priority
**CRITICAL** - This blocks the core functionality of the VS Code extension and prevents users from using AI-powered code analysis.