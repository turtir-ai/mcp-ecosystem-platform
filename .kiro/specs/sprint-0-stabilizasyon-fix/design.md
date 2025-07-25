# VS Code Extension API Field Mismatch Fix - Design

## Root Cause Analysis

**Backend Behavior:**
The backend's `POST /api/v1/git/review` endpoint returns the review ID in the `id` field:
```json
{
  "success": true,
  "data": {
    "id": "e16d4a25-45a6-44f5-9497-ed2755b11076",
    "repository_id": "test",
    "review_type": "full",
    "status": "in_progress",
    "started_at": "2025-07-25T14:53:20.552513",
    "progress": 0
  }
}
```

**Frontend Expectation:**
The API client in `mcpPlatformAPI.ts` tries to read `reviewId` field:
```typescript
return response.data.success ? response.data.data.reviewId : null;
```

**Result:** `reviewId` is `undefined`, causing subsequent API calls to fail.

## Solution Strategy

**Option 1: Fix Frontend (Recommended)**
Update the frontend API client to read the correct field name (`id`) that the backend actually sends.

**Option 2: Fix Backend**
Add `reviewId` field to backend response (already attempted but not working due to serialization issues).

**Decision:** We'll go with Option 1 as it's simpler and doesn't require backend changes.

## Technical Implementation

### File to Modify
`vscode-extension/src/api/mcpPlatformAPI.ts`

### Function to Fix
`startCodeReview` method

### Change Required
```typescript
// BEFORE (incorrect)
return response.data.success ? response.data.data.reviewId : null;

// AFTER (correct)
return response.data.success ? response.data.data.id : null;
```

## Testing Strategy

1. **Manual Testing:**
   - Start VS Code extension development host (F5)
   - Run "Review Current File" command
   - Verify no "Connection Error" appears
   - Check backend logs for successful API calls

2. **Log Verification:**
   - Should see successful `POST /api/v1/git/review` calls
   - Should see successful `GET /api/v1/git/review/{valid-id}/results` calls
   - Should NOT see `GET /api/v1/git/review/undefined/results` calls

## Risk Assessment
- **Low Risk:** Single line change in frontend code
- **High Impact:** Fixes critical extension functionality
- **Rollback:** Simple - revert the one line change