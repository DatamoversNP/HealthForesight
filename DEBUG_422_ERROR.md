# Debugging 422 Error on Decision Creation

## Current Status
- ✅ Removed `status` field from request (not in API model)
- ✅ Added client-side validation
- ✅ Added error message extraction
- ⚠️ Still getting 422 error

## Next Steps to Debug

### 1. Check the Response Tab
In the Network tab, click on the failed `/decisions` request, then:
1. Click the **"Response"** tab (not Headers)
2. You should see the actual validation error from FastAPI
3. It will look like:
   ```json
   {
     "detail": [
       {
         "type": "missing",
         "loc": ["body", "field_name"],
         "msg": "field required",
         "input": {...}
       }
     ]
   }
   ```

### 2. Check the Payload Tab
1. Click the **"Payload"** tab
2. See what data is actually being sent
3. Compare with what the API expects

### 3. API Model Requirements
The `DecisionCreate` model expects:
- ✅ `title: str` (required)
- ✅ `recommendation: str` (required)
- ✅ `rationale: str` (required)
- ✅ `confidence_score: float` (optional, defaults to 0.5)
- ✅ `policy_id: Optional[str]` (optional)
- ✅ `assumptions_snapshot: Dict[str, Any]` (optional, defaults to {})

### 4. What We're Sending
```typescript
{
  title: formData.title.trim(),
  recommendation: formData.recommendation.trim(),
  rationale: formData.rationale.trim(),
  confidence_score: formData.confidence_score,
  policy_id: policyId,
  assumptions_snapshot: {},
}
```

## Common Issues

1. **Empty strings after trim**: If title/recommendation/rationale are empty after trim, Pydantic might reject them
2. **Invalid confidence_score**: Must be a float between 0 and 1
3. **Invalid policy_id**: Must be a valid UUID string or null
4. **Missing required fields**: Title, recommendation, or rationale might be empty

## Quick Fix to Try

Add validation to ensure fields are not empty after trim:

```typescript
if (!formData.title.trim()) {
  setError('Title cannot be empty')
  return
}
```

## Share the Response
Please share:
1. The **Response** tab content from the failed request
2. The **Payload** tab content showing what was sent

This will help identify the exact validation error.


