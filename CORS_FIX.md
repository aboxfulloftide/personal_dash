# CORS Configuration Fix

## Problem
When accessing the web UI from a different machine on the network (e.g., `http://192.168.1.100:5173`), you get a CORS error when trying to create servers or perform other API operations.

## Root Cause
The backend was configured to only allow CORS requests from `http://localhost:5173`, which meant requests from other network addresses were blocked.

## Solution Applied

### 1. Updated Default CORS Configuration
**File:** `backend/app/core/config.py`

Changed from:
```python
CORS_ORIGINS: List[str] = ["http://localhost:5173"]
```

To:
```python
CORS_ORIGINS: List[str] = ["*"]  # Allow all origins by default
```

### 2. Updated Environment Variable Documentation
**File:** `backend/.env.example`

Added comprehensive CORS configuration examples with comments explaining:
- Development setup (allow all)
- Production setup (specific origins only)
- Multiple origins (local + network)

## Configuration Options

### Development (Recommended)
Allow all origins for easy testing:

```bash
# In backend/.env
CORS_ORIGINS=["*"]
```

### Production (Recommended)
Specify exact allowed origins:

```bash
# In backend/.env
CORS_ORIGINS=["https://dash.yourdomain.com"]
```

### Mixed (Local + Network)
Allow multiple specific origins:

```bash
# In backend/.env
CORS_ORIGINS=["http://localhost:5173","http://192.168.1.100:5173","http://your-server:5173"]
```

## How to Apply the Fix

### If Backend is Running
1. Stop the backend server (Ctrl+C)
2. Restart it:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### If Backend is Not Running
1. Start the backend:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. The new CORS settings will be loaded automatically

## Testing the Fix

1. Access the web UI from another machine: `http://YOUR_SERVER_IP:5173`
2. Navigate to "Servers" page
3. Click "Add Server"
4. Fill in the form and submit
5. Should work without CORS errors!

## Security Considerations

### Development
- `CORS_ORIGINS=["*"]` is fine for development
- Allows access from any origin
- Makes testing on different devices easy

### Production
- **NEVER use `["*"]` in production!**
- Always specify exact allowed origins
- Use HTTPS in production:
  ```bash
  CORS_ORIGINS=["https://dash.yourdomain.com"]
  ```

### Behind a Reverse Proxy (Nginx/Apache)
If using a reverse proxy, you may need to allow the proxy's origin:

```bash
# Example with Nginx reverse proxy
CORS_ORIGINS=["https://dash.yourdomain.com"]
```

The reverse proxy handles external requests and forwards to the backend, so the backend only needs to allow the proxy's origin.

## Common Scenarios

### Scenario 1: Local Development
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- **Solution:** `CORS_ORIGINS=["*"]` or `["http://localhost:5173"]`

### Scenario 2: Network Access (Same LAN)
- Backend: `http://192.168.1.50:8000`
- Frontend: `http://192.168.1.50:5173`
- Accessing from: `http://192.168.1.100` (different machine)
- **Solution:** `CORS_ORIGINS=["*"]` or `["http://192.168.1.50:5173"]`

### Scenario 3: Production Deployment
- Backend: `https://api.dash.example.com`
- Frontend: `https://dash.example.com`
- **Solution:** `CORS_ORIGINS=["https://dash.example.com"]`

### Scenario 4: Multiple Frontends
- Main UI: `https://dash.example.com`
- Admin UI: `https://admin.dash.example.com`
- Mobile app: `https://mobile.dash.example.com`
- **Solution:** `CORS_ORIGINS=["https://dash.example.com","https://admin.dash.example.com","https://mobile.dash.example.com"]`

## Troubleshooting

### Still Getting CORS Errors?

**1. Check Backend Logs**
Look for CORS-related messages:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**2. Verify .env is Being Loaded**
The backend reads from `backend/.env`. Make sure:
- File exists
- `CORS_ORIGINS` is set
- Backend was restarted after changes

**3. Check Browser Console**
The error will show the origin that was rejected:
```
Access to XMLHttpRequest at 'http://192.168.1.50:8000/api/v1/servers'
from origin 'http://192.168.1.100:5173' has been blocked by CORS policy
```

Copy that origin and add it to `CORS_ORIGINS`.

**4. Verify Backend is Listening on 0.0.0.0**
The backend must bind to `0.0.0.0` (all interfaces) to accept network requests:
```bash
# Correct
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Wrong (only accepts localhost)
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**5. Check Firewall**
Ensure port 8000 is open:
```bash
# Linux
sudo ufw allow 8000

# Check if port is listening
netstat -tuln | grep 8000
```

## Environment Variable Format

The `CORS_ORIGINS` must be a valid Python list in the .env file:

✅ **Correct:**
```bash
CORS_ORIGINS=["*"]
CORS_ORIGINS=["http://localhost:5173"]
CORS_ORIGINS=["http://localhost:5173","http://192.168.1.100:5173"]
```

❌ **Incorrect:**
```bash
CORS_ORIGINS=*
CORS_ORIGINS=http://localhost:5173
CORS_ORIGINS=["http://localhost:5173", "http://192.168.1.100:5173"]  # No spaces!
```

## Additional Notes

- Changes to `.env` require backend restart
- Browser caches CORS responses - hard refresh (Ctrl+Shift+R) if needed
- CORS is a browser security feature - API tools like curl/Postman aren't affected
- Preflight OPTIONS requests are handled automatically by FastAPI middleware

## References

- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
