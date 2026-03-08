# CORS Fix Applied

## Issue
When clicking "Predicted Impact" button, the browser console showed:
```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/policies/.../predicted-impact' 
from origin 'http://localhost:3050' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
The API server's CORS configuration was not allowing requests from `http://localhost:3050`.

## Fix Applied
Updated `apps/api/src/uepi_api/main.py` to explicitly allow CORS from:
- `http://localhost:3050` (web server)
- `http://localhost:5173` (Vite default port)
- `http://127.0.0.1:3050` (alternative localhost)
- `http://127.0.0.1:5173` (alternative Vite port)
- Any origins already configured in settings

## Code Change
```python
# Before: Only using settings.cors_origins
allow_origins=settings.cors_origins,

# After: Explicitly allow localhost ports
allow_origins=[
    "http://localhost:3050",
    "http://localhost:5173",
    "http://127.0.0.1:3050",
    "http://127.0.0.1:5173",
    *settings.cors_origins,
],
```

## Verification

After the API server restarts, test:

1. **Check CORS headers** (in browser console):
   ```javascript
   fetch('http://localhost:8000/api/v1/health')
     .then(r => console.log('CORS OK:', r.headers.get('access-control-allow-origin')))
   ```

2. **Try the Predicted Impact button again** - it should work now!

## Next Steps

1. ✅ API server is restarting with CORS fix
2. Wait 15-20 seconds for server to fully start
3. Refresh your browser page (http://localhost:3050)
4. Click "Predicted Impact" button again
5. The CORS error should be gone!

## Status

✅ **CORS Configuration**: Fixed
⏳ **API Server**: Restarting with new configuration

The CORS error should be resolved once the API server finishes restarting.
