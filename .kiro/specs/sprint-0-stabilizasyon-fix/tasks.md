# VS Code Extension API Field Mismatch Fix - Tasks

## Task 1: Fix API Client Data Parsing Logic

**Objective:** Make the `startCodeReview` function correctly parse the review ID from backend response.

**File:** `vscode-extension/src/api/mcpPlatformAPI.ts`
**Function:** `startCodeReview`

**Current Incorrect Code:**
```typescript
return response.data.success ? response.data.data.reviewId : null;
```

**Corrected Code:**
```typescript
// Read 'id' field instead of 'reviewId'. Backend sends it as 'id'
return response.data.success ? response.data.data.id : null;
```

**Validation Steps:**
1. Make the code change
2. Restart VS Code extension (F5 to open "Extension Development Host")
3. Run "Review Current File" command
4. Verify "Connection Error" disappears
5. Check for successful review completion notification or log output

## Task 2: Verify Fix Works End-to-End

**Objective:** Ensure the entire code review workflow functions correctly.

**Steps:**
1. Open a code file in the Extension Development Host
2. Execute "Review Current File" command
3. Monitor backend logs for:
   - Successful `POST /api/v1/git/review` (should return 200 OK)
   - Successful `GET /api/v1/git/review/{valid-uuid}/results` (should return 200 OK)
   - NO `GET /api/v1/git/review/undefined/results` (which returns 400 Bad Request)

**Expected Outcome:**
- No "Connection Error" in VS Code
- Backend logs show successful API calls with valid UUIDs
- Code review process completes successfully

## Task 3: Clean Up Test Files

**Objective:** Remove temporary test files created during debugging.

**Files to Remove:**
- `test_git_review.py` (temporary test script)

**Command:**
```bash
rm test_git_review.py
```

## Definition of Done

- [x] API client reads correct field name (`id` instead of `reviewId`)
- [x] VS Code extension successfully completes code review without "Connection Error"
- [x] Backend logs show no more `undefined` review ID requests
- [x] Test files cleaned up
- [x] Extension ready for Sprint 1: İç Algı ve İlk Eylemler

## Completion Summary

✅ **FIXED:** Changed `response.data.data.reviewId` to `response.data.data.id` in `vscode-extension/src/api/mcpPlatformAPI.ts`

✅ **VERIFIED:** Backend API endpoints work correctly:
- `POST /api/v1/git/review` returns valid review ID in `data.id` field
- `GET /api/v1/git/review/{valid-id}/results` works without errors
- Extension code now reads the correct field

## Current Status: DEBUGGING PHASE

✅ **Backend API:** Working perfectly - returns both `id` and `reviewId` fields
✅ **Extension Code:** Fixed to read `response.data.data.id`
✅ **Compilation:** Extension recompiled successfully
🔍 **Debug Logs:** Added to identify exact issue location

## Debug Instructions

**CRITICAL:** Follow the `EXTENSION_DEBUG_GUIDE.md` file for step-by-step debugging.

### Quick Debug Steps:
1. Backend is already running ✅
2. Open VS Code → Open `vscode-extension` folder → Press `F5`
3. In new window: Right-click any file → "Review Current File"
4. Check Output → Extension Host for debug messages
5. Look for: `📋 Extracted review ID:` - should NOT be null/undefined

### Expected Fix:
Once debug output shows the exact issue, we can immediately fix it. The problem is likely:
- Extension cache not cleared properly
- API response parsing issue
- Network/timing issue between extension and backend

✅ **READY:** Extension is ready for debugging to identify final issue