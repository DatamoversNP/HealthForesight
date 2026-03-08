# Deployment Issue Summary

## Problem
- Oryx extracts files to `/tmp/XXX` but PYTHONPATH doesn't include `/tmp/XXX/src`
- Our custom startup.sh isn't being executed by Oryx
- Oryx generates its own startup script that overrides ours
- App keeps failing with `ModuleNotFoundError: No module named 'uepi_api'`

## Root Cause
Oryx build system extracts files to a temporary directory, but Python can't find them because:
1. Oryx sets PYTHONPATH to `/home/site/wwwroot/src` (which doesn't exist)
2. Files are actually in `/tmp/XXX/src` (where Oryx extracted them)
3. Our startup commands/scripts aren't executing before the error

## Solutions to Try

### Option 1: Stop app and use Docker deployment (Recommended)
- More control over the environment
- No Oryx interference
- Predictable file locations

### Option 2: Fix ZIP structure for Oryx
- Ensure files are in the exact structure Oryx expects
- Use `.deployment` file to control Oryx behavior

### Option 3: Skip Oryx build
- Deploy pre-built application
- Use custom container

## Immediate Action
**STOP THE APP** to save costs:
```bash
az webapp stop --name hf-api8755146 --resource-group healthforesight-rg
```
