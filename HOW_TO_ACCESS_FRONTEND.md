# How to Access the Frontend

## Quick Check

Based on your deployment, the frontend should be accessible at:

**Static Web App URL**: `https://hf-web8755147.azurestaticapps.net`

(Replace `hf-web8755147` with your actual web app name from the deployment)

## Find Your Frontend URL

Run this command in your terminal to find all web apps:

```bash
# List all web apps (Static Web Apps)
az staticwebapp list --resource-group healthforesight-rg --query "[].{Name:name, URL:defaultHostname, State:state}" -o table

# Or list all App Service web apps
az webapp list --resource-group healthforesight-rg --query "[?contains(name, 'web')].{Name:name, URL:defaultHostName, State:state}" -o table
```

## If Frontend Wasn't Deployed

If the web app doesn't exist or wasn't fully deployed, you have two options:

### Option 1: Continue the Deployment Script

The `DEPLOY_TO_AZURE.sh` script was interrupted during API deployment. The web app deployment (Step 10-12) might not have completed.

**To deploy the frontend now:**

1. Run the deployment script again:
   ```bash
   ./DEPLOY_TO_AZURE.sh
   ```
   
2. When prompted, use the **same values** you used before:
   - Resource Group: `healthforesight-rg`
   - API App: `hf-api8755146` (already exists)
   - Web App: `hf-web8755147` (or let it generate a new one)
   
3. The script will:
   - Skip creating resources that already exist
   - Continue with web app creation (Step 10-12)

### Option 2: Deploy Frontend Separately

If you want to deploy just the frontend:

1. **Check if Static Web App exists:**
   ```bash
   az staticwebapp show --name hf-web8755147 --resource-group healthforesight-rg
   ```

2. **If it doesn't exist, create it:**
   ```bash
   az staticwebapp create \
     --name hf-web8755147 \
     --resource-group healthforesight-rg \
     --location eastus \
     --sku Free
   ```

3. **Build and deploy the web app:**
   ```bash
   cd apps/web
   npm run build
   
   # Deploy using Azure Static Web Apps CLI (if installed)
   # Or use the Azure Portal to deploy from GitHub/VS Code
   ```

## Current Status

Based on your deployment logs:
- ✅ **API App Created**: `hf-api8755146` 
- ⚠️ **API Status**: Container creation issues (being fixed)
- ❓ **Web App**: May not be fully deployed

## Accessing the Frontend Locally

While the Azure deployment is being fixed, you can run the frontend locally:

```bash
cd apps/web
npm install
npm run dev
```

Then access it at: `http://localhost:3050`

The frontend will connect to:
- Local API: `http://localhost:8000` (if running locally)
- Azure API: `https://hf-api8755146.azurewebsites.net` (once API is fixed)

To point the local frontend to the Azure API, update `apps/web/vite.config.ts` or set environment variables.

## Next Steps

1. **Check if web app exists:**
   ```bash
   az staticwebapp list --resource-group healthforesight-rg -o table
   ```

2. **If it exists, get the URL:**
   ```bash
   az staticwebapp show --name hf-web8755147 --resource-group healthforesight-rg --query defaultHostname -o tsv
   ```

3. **Access it:**
   - Open `https://hf-web8755147.azurestaticapps.net` in your browser
   - The frontend should automatically connect to your API at `https://hf-api8755146.azurewebsites.net`

4. **If API is still not working**, the frontend may show errors. Once the API container issue is resolved (via `fix_docker_container_creation.sh`), both should work together.
