# How to Fix Docker Container Creation Issue

## Problem
Azure App Service is failing to create the Docker container (`ContainerCreateFailure`).

## Solution
Run the `fix_docker_container_creation.sh` script **in your terminal** (outside of Cursor's sandbox) because Docker requires full system permissions.

## Steps

### 1. Open your terminal
Navigate to the project directory:
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
```

### 2. Find your ACR name (if not auto-detected)
```bash
az acr list --resource-group healthforesight-rg --query "[].name" -o table
```

If you see an ACR name, note it down. If empty, you may need to create one first using `deploy_with_docker.sh`.

### 3. Run the fix script

**Option A: Let it auto-detect the ACR**
```bash
./fix_docker_container_creation.sh
```

**Option B: Specify the ACR name manually**
```bash
ACR_NAME_OVERRIDE=healthforesightacr12666 ./fix_docker_container_creation.sh
```

Replace `healthforesightacr12666` with your actual ACR name.

### 4. What the script does
1. ✅ Clears any conflicting startup commands (uses Dockerfile CMD instead)
2. ✅ Sets `WEBSITES_PORT=8000` in app settings
3. ✅ Sets `PORT=8000` environment variable
4. ✅ Builds Docker image for `linux/amd64` architecture
5. ✅ Pushes image to Azure Container Registry
6. ✅ Restarts the app
7. ⏳ Waits 90 seconds for container to start

### 5. Verify the fix

After the script completes, check the logs:
```bash
az webapp log tail --name hf-api8755146 --resource-group healthforesight-rg
```

Look for `[STARTUP]` messages. You should see:
- `[STARTUP] Starting uepi-api container...`
- `[STARTUP] PYTHONPATH=/app/src:/app/packages/common/src`
- `[STARTUP] Import successful`
- `Application startup complete.`

Test the health endpoint:
```bash
curl https://hf-api8755146.azurewebsites.net/health
```

Expected response: `{"status":"healthy"}`

## Troubleshooting

### If Docker build fails:
- Make sure Docker Desktop is running
- Try: `docker ps` to verify Docker is accessible
- Check disk space: `df -h`

### If ACR login fails:
- Make sure you're logged into Azure: `az account show`
- Login: `az login`
- Try logging in to ACR manually: `az acr login --name YOUR_ACR_NAME`

### If container still fails to start:
Check the logs for specific error messages:
```bash
az webapp log tail --name hf-api8755146 --resource-group healthforesight-rg | grep -i error
```

Common issues:
- **ModuleNotFoundError**: PYTHONPATH not set correctly (should be fixed by script)
- **Permission denied**: Storage path issue (should be `/home/data`)
- **Port binding error**: WEBSITES_PORT not set (should be fixed by script)

## Next Steps

If the container starts successfully:
1. ✅ Your API should be accessible at `https://hf-api8755146.azurewebsites.net`
2. ✅ Test endpoints: `/health`, `/api/v1/...`
3. ✅ Deploy the web frontend next (if not already done)

If issues persist:
1. Check Azure Portal → App Service → Log stream
2. Check Azure Portal → App Service → Container settings
3. Review the `apps/api/start.sh` startup script output in logs
