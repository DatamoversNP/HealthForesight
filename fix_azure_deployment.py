#!/usr/bin/env python3
"""
Fix Azure App Service deployment by ensuring correct PYTHONPATH and file structure.
This script updates the startup command to handle Oryx build system correctly.
"""

import subprocess
import sys
import os

APP_NAME = "hf-api8755146"
RESOURCE_GROUP = "healthforesight-rg"

def run_cmd(cmd, check=True):
    """Run a command and return output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    print("=== Fixing Azure App Service Deployment ===\n")
    
    # Check current app state
    print("1. Checking app state...")
    state = run_cmd(f"az webapp show --name {APP_NAME} --resource-group {RESOURCE_GROUP} --query state -o tsv", check=False)
    print(f"   App state: {state}\n")
    
    # Update startup command to work with Oryx build system
    # The key is to ensure PYTHONPATH is set correctly AND we change to the right directory
    print("2. Updating startup command...")
    
    # This startup command:
    # 1. Sets PYTHONPATH to multiple possible locations
    # 2. Changes to the wwwroot directory
    # 3. Ensures we can find uepi_api module
    startup_cmd = (
        "bash -c '"
        "export PYTHONPATH=\"/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH\" && "
        "cd /home/site/wwwroot && "
        "if [ -d src/uepi_api ]; then cd src; fi && "
        "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}'"
    )
    
    # Set the startup command
    result = run_cmd(
        f'az webapp config set '
        f'--name {APP_NAME} '
        f'--resource-group {RESOURCE_GROUP} '
        f'--startup-file "{startup_cmd}"',
        check=False
    )
    
    if "error" in result.lower() or "conflict" in result.lower():
        print(f"   Warning: {result}")
    else:
        print("   ✅ Startup command updated\n")
    
    # Ensure PYTHONPATH is set in app settings as well
    print("3. Updating app settings...")
    run_cmd(
        f'az webapp config appsettings set '
        f'--name {APP_NAME} '
        f'--resource-group {RESOURCE_GROUP} '
        f'--settings PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src"',
        check=False
    )
    print("   ✅ App settings updated\n")
    
    # Restart the app
    print("4. Restarting app...")
    run_cmd(f"az webapp restart --name {APP_NAME} --resource-group {RESOURCE_GROUP}")
    print("   ✅ App restarted\n")
    
    print("5. Waiting for app to start (30 seconds)...")
    import time
    time.sleep(30)
    
    # Test the health endpoint
    print("\n6. Testing health endpoint...")
    import urllib.request
    try:
        response = urllib.request.urlopen(f"https://{APP_NAME}.azurewebsites.net/health", timeout=10)
        if response.status == 200:
            print(f"   ✅ App is responding! Status: {response.status}")
            print(f"   Response: {response.read().decode()[:100]}")
        else:
            print(f"   ⚠️  App responded with status {response.status}")
    except Exception as e:
        print(f"   ⚠️  Could not reach app: {e}")
        print(f"   Check logs: az webapp log tail --name {APP_NAME} --resource-group {RESOURCE_GROUP}")
    
    print("\n=== Fix Complete ===")
    print("\nNext steps:")
    print("1. Check logs: az webapp log tail --name {APP_NAME} --resource-group {RESOURCE_GROUP}")
    print("2. Test health: curl https://{APP_NAME}.azurewebsites.net/health")

if __name__ == "__main__":
    main()
