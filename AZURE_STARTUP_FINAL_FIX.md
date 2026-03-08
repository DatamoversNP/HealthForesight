# Azure Startup - Final Fix

## Issue
`startup.sh` file is not found when Oryx tries to execute it. The startup command `bash startup.sh` is looking for the file in the current working directory, but it may not be there.

## Solution
Use the full path to `startup.sh`:
```bash
bash /home/site/wwwroot/startup.sh
```

## Applied Fix
Run:
```bash
./scripts/azure/fix-oryx-startup.sh
```

This updates the startup command to use the full path.

## Alternative: Direct Command
If the script still doesn't work, we can use a direct command instead:

```bash
az webapp config set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --startup-file "cd /home/site/wwwroot && bash startup.sh"
```

Or even simpler, use a direct uvicorn command that Oryx can handle:

```bash
az webapp config set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --startup-file "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000"
```

But this requires PYTHONPATH to be set correctly in app settings.

