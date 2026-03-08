# Fix: Decision Creation Error Handling

## Issue
When creating a decision, React was trying to render a validation error object directly, causing:
```
Objects are not valid as a React child (found: object with keys {type, loc, msg, input})
```

## Root Cause
FastAPI/Pydantic validation errors are returned as an array of objects:
```json
[
  {
    "type": "value_error",
    "loc": ["body", "title"],
    "msg": "field required",
    "input": {}
  }
]
```

The error handling code was trying to render this object directly in React, which doesn't work.

## Solution
Created a helper function `extractErrorMessage()` that:
1. Checks if error is from API response (`err.response.data.detail`)
2. Handles array of validation errors (Pydantic format)
3. Handles string error messages
4. Formats validation errors as readable strings: `"field: message"`
5. Falls back to generic error message

## Changes Made
- Added `extractErrorMessage()` helper function
- Updated all error handlers to use the helper:
  - `loadDecisions()` error handling
  - `handleSubmit()` error handling
  - `handleDelete()` error handling
  - `handleFinalize()` error handling

## Testing
1. Try creating a decision with missing required fields
2. Error should now display as a readable string instead of crashing
3. Example error message: `"title: field required, recommendation: field required"`

## Next Steps
- Refresh browser to see the fix
- Try creating a decision again
- If validation errors occur, they'll be displayed properly


