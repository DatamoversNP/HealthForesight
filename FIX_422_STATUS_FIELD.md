# Fix: 422 Error - Status Field Not in API Model

## Issue
Getting `422 (Unprocessable Content)` error when creating a decision because the frontend is sending a `status` field that the API doesn't accept.

## Root Cause
The `DecisionCreate` Pydantic model in the API doesn't have a `status` field:
```python
class DecisionCreate(BaseModel):
    title: str
    recommendation: str
    rationale: str
    confidence_score: float = 0.5
    # ... other fields, but NO status field
```

But the frontend was sending:
```typescript
{
  title: "...",
  recommendation: "...",
  rationale: "...",
  status: "DRAFT",  // ❌ This field is not accepted
  ...
}
```

## Solution
Removed `status` from the create request. The API defaults to "DRAFT" automatically in the storage layer.

## Changes Made
- Removed `status: formData.status` from the `decisionData` object
- Status will default to "DRAFT" when decision is created
- Status can be updated later using the update endpoint

## Testing
1. Refresh browser
2. Try creating a decision
3. Should succeed now (no 422 error)
4. Decision will be created with status "DRAFT" by default

---

**Fix applied! Refresh and try again.** ✅


