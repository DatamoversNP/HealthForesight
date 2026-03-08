# Start Azure App Service and Check Logs

## Problem

"Error 403 - This web app is stopped" means your App Service is **stopped**. You need to **start it** before accessing Kudu console or logs.

## Quick Fix: Start the App Service

### Method 1: Azure CLI (Quickest)

```bash
# Start the app
az webapp start \
  --name hf-api8755146 \
  --resource-group healthforesight-rg

# Wait a few seconds for it to start
sleep 10

# Check status
az webapp show \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --query state -o tsv

# Should show: "Running"
```

### Method 2: Azure Portal

1. Go to: https://portal.azure.com
2. Search: `hf-api8755146`
3. Click on your App Service
4. At the top, click: **"Start"** button (green play icon)
5. Wait a few seconds for it to start

### Method 3: Use the Script

I've created `start_azure_app.sh` - just run:

```bash
./start_azure_app.sh healthforesight-rg hf-api8755146
```

## After Starting: Check Logs

Once the app is started, you can access logs:

### Check Application Logs

```bash
# Stream logs
az webapp log tail \
  --name hf-api8755146 \
  --resource-group healthforesight-rg

# Download logs
az webapp log download \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --log-file logs.zip
```

### Access Kudu Console

Once started, go to:
- `https://hf-api8755146.scm.azurewebsites.net`

### Check App Status

```bash
# Check if running
az webapp show \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --query state -o tsv

# Should show: "Running"
```

## Why Was It Stopped?

Common reasons:
1. **Failed to start** - App crashed during startup
2. **Manually stopped** - Someone stopped it
3. **Auto-stop on Free tier** - Free tier stops after inactivity
4. **Quota exceeded** - Resource limits reached

## Check Why It's Not Starting

Once you start it, check logs to see why it might have stopped:

```bash
# Enable application logging first
az webapp log config \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --application-logging filesystem \
  --level verbose

# Start the app
az webapp start \
  --name hf-api8755146 \
  --resource-group healthforesight-rg

# Wait a bit
sleep 15

# Stream logs to see startup errors
az webapp log tail \
  --name hf-api8755146 \
  --resource-group healthforesight-rg
```

## Quick Commands

```bash
# Start app
az webapp start --name hf-api8755146 --resource-group healthforesight-rg

# Check status
az webapp show --name hf-api8755146 --resource-group healthforesight-rg --query state -o tsv

# Stream logs
az webapp log tail --name hf-api8755146 --resource-group healthforesight-rg

# Test health endpoint
curl https://hf-api8755146.azurewebsites.net/health
```

## Next Steps

1. **Start the app** (use commands above)
2. **Wait 10-15 seconds** for it to start
3. **Check logs** to see if it starts successfully
4. **Test endpoint** - `curl https://hf-api8755146.azurewebsites.net/health`
5. **If it stops again** - Check logs for startup errors

## Summary

✅ **App is stopped** - That's why you see 403 error
✅ **Start it first** - Use `az webapp start` or Azure Portal
✅ **Then check logs** - Once running, you can access Kudu and logs
✅ **Diagnose startup** - Check logs to see why it might not be starting

**Start the app first, then we can check logs to see why it's not starting properly!**
