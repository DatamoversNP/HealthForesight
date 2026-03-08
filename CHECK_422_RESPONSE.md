# How to Check the 422 Validation Error

## Steps to See the Actual Error

1. **In the Network tab**, click on the failed `/decisions` request (the one with 422 status)

2. **Click the "Response" tab** (next to Headers, Payload, etc.)

3. **You should see something like:**
   ```json
   {
     "detail": [
       {
         "type": "missing",
         "loc": ["body", "title"],
         "msg": "field required",
         "input": {}
       }
     ]
   }
   ```
   OR
   ```json
   {
     "detail": "Field 'title' is required"
   }
   ```

4. **Also check the "Payload" tab** to see what we're actually sending

## What I've Fixed

✅ Removed `status` field (not in API model)
✅ Added better validation
✅ Added console logging (`console.log('Sending decision data:', decisionData)`)
✅ Ensured confidence_score is a number
✅ Only include policy_id if it exists

## Next Steps

1. **Check the Response tab** and share what you see
2. **Check the Payload tab** to verify what's being sent
3. **Check the browser console** for the `console.log` output

This will help identify the exact validation error!


