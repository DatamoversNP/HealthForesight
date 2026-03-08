# Fixing ContainerCreateFailure Issue

## Problem
The Docker container is failing to create in Azure App Service with `ContainerCreateFailure` error. The container never starts, so we're not seeing any `[STARTUP]` logs.

## Diagnosis Steps

### 1. Check Container Configuration
```bash
az webapp config container show --name hf-api8755146 --resource-group healthforesight-rg -o json
```

### 2. Check App State and Settings
```bash
az webapp show --name hf-api8755146 --resource-group healthforesight-rg --query "{State:state, Kind:kind, LinuxFxVersion:siteConfig.linuxFxVersion, DockerImage:siteConfig.linuxFxVersion}" -o json
```

### 3. Verify Docker Image Exists
```bash
az acr repository show-tags --name healthforesightacr12666 --repository uepi-api --output table
```

### 4. Check Container Logs via Kudu
Navigate to: `https://hf-api8755146.scm.azurewebsites.net/api/logs/docker`

## Common Causes & Fixes

### Issue 1: Container Configuration Conflict
**Symptom**: App Service has conflicting settings (startup command + Docker image)

**Fix**:
```bash
# Clear any startup command (let Dockerfile CMD handle it)
az webapp config set \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --startup-file "" \
  --output none

# Ensure Docker image is set correctly
az webapp config container set \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --docker-custom-image-name healthforesightacr12666.azurecr.io/uepi-api:latest \
  --docker-registry-server-url https://healthforesightacr12666.azurecr.io \
  --docker-registry-server-user $(az acr credential show --name healthforesightacr12666 --query username -o tsv) \
  --docker-registry-server-password $(az acr credential show --name healthforesightacr12666 --query passwords[0].value -o tsv) \
  --output none
```

### Issue 2: Missing or Invalid Docker Image
**Symptom**: Image doesn't exist in ACR or has wrong tag

**Fix**:
```bash
# List images in ACR
az acr repository show-tags --name healthforesightacr12666 --repository uepi-api --output table

# If missing, rebuild and push
./fix_docker_container_creation.sh
```

### Issue 3: Docker Image Architecture Mismatch
**Symptom**: Image built for wrong architecture (ARM64 vs AMD64)

**Fix**: Ensure you're building for `linux/amd64`:
```bash
docker build --platform linux/amd64 -t uepi-api:latest -f apps/api/Dockerfile .
```

### Issue 4: ACR Authentication Issues
**Symptom**: App Service can't pull image from ACR

**Fix**:
```bash
# Update ACR credentials in App Service
ACR_USER=$(az acr credential show --name healthforesightacr12666 --query username -o tsv)
ACR_PASS=$(az acr credential show --name healthforesightacr12666 --query passwords[0].value -o tsv)

az webapp config container set \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --docker-registry-server-url https://healthforesightacr12666.azurecr.io \
  --docker-registry-server-user $ACR_USER \
  --docker-registry-server-password $ACR_PASS \
  --output none
```

### Issue 5: App Service Plan Issues
**Symptom**: Plan doesn't support containers or is on wrong tier

**Fix**: Verify your App Service Plan supports containers (Linux plan):
```bash
az appservice plan show --name healthforesight-plan --resource-group healthforesight-rg --query "{Name:name, Kind:kind, Tier:sku.tier}" -o json
```

## Quick Fix Script

Run this to try all fixes:
```bash
./check_container_logs_detailed.sh
```

## Alternative: Use Azure Portal

1. Go to Azure Portal → App Service → `hf-api8755146`
2. Navigate to **Container settings**
3. Check:
   - Docker image URL
   - Registry credentials
   - Startup command (should be empty or match Dockerfile CMD)
4. Navigate to **Log stream** to see real-time container logs
5. Navigate to **Advanced Tools (Kudu)** → `https://hf-api8755146.scm.azurewebsites.net`
   - Go to **Debug console** → **CMD**
   - Navigate to `/home/LogFiles` to see log files
   - Check `/home/LogFiles/2026_01_19_*_docker.log`

## If All Else Fails

If the container still won't start, try:

1. **Use a simpler CMD in Dockerfile**:
   ```dockerfile
   CMD python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```
   (Remove the startup script temporarily)

2. **Deploy without custom startup script**:
   - Comment out the `COPY apps/api/start.sh` and `CMD` lines in Dockerfile
   - Use a direct CMD instead

3. **Check if the issue is with the image itself**:
   ```bash
   # Test locally first
   docker run -p 8000:8000 -e PORT=8000 healthforesightacr12666.azurecr.io/uepi-api:latest
   ```

4. **Contact Azure Support** with:
   - App Service name: `hf-api8755146`
   - Resource Group: `healthforesight-rg`
   - Error: `ContainerCreateFailure`
   - Logs from Kudu console
