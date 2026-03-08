#!/usr/bin/env python3
"""Migrate local file-based data to Azure File Storage"""
import os
import sys
import json
from pathlib import Path
from azure.storage.fileshare import ShareClient, ShareFileClient
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError

def create_directory_recursive(share_client: ShareClient, dir_path: str):
    """Recursively create directory structure"""
    if not dir_path or dir_path == '.':
        return
    
    parts = dir_path.split('/')
    current_path = ''
    for part in parts:
        if not part:
            continue
        if current_path:
            current_path = f"{current_path}/{part}"
        else:
            current_path = part
        
        try:
            dir_client = share_client.get_directory_client(current_path)
            dir_client.create_directory()
        except HttpResponseError as e:
            if e.status_code != 409:  # 409 = Directory already exists
                raise
        except Exception:
            pass  # Directory might already exist

def upload_file(share_client: ShareClient, local_path: Path, remote_path: str):
    """Upload a single file to Azure File Storage"""
    try:
        # Create directory structure if needed
        remote_dir = os.path.dirname(remote_path).replace('\\', '/')
        if remote_dir and remote_dir != '.':
            create_directory_recursive(share_client, remote_dir)
        
        # Upload file - check if file exists first, delete if it does
        file_client = share_client.get_file_client(remote_path)
        try:
            # Try to delete existing file
            file_client.delete_file()
        except ResourceNotFoundError:
            pass  # File doesn't exist, that's fine
        
        # Upload the file
        with open(local_path, 'rb') as f:
            file_client.upload_file(f)
        return True
    except Exception as e:
        print(f"  ⚠️  Error uploading {remote_path}: {e}")
        return False

def migrate_directory(share_client: ShareClient, local_dir: Path, remote_base: str = ""):
    """Recursively migrate a directory to Azure File Storage"""
    migrated_count = 0
    error_count = 0
    
    for root, dirs, files in os.walk(local_dir):
        root_path = Path(root)
        relative_path = root_path.relative_to(local_dir)
        
        for file in files:
            local_file = root_path / file
            if relative_path == Path('.'):
                remote_path = file
            else:
                remote_path = str(relative_path / file).replace('\\', '/')
            
            print(f"  Uploading: {remote_path}")
            if upload_file(share_client, local_file, remote_path):
                migrated_count += 1
            else:
                error_count += 1
    
    return migrated_count, error_count

def main():
    if len(sys.argv) < 5:
        print("Usage: migrate_data.py <account_name> <account_key> <share_name> <local_data_dir>")
        sys.exit(1)
    
    account_name = sys.argv[1]
    account_key = sys.argv[2]
    share_name = sys.argv[3]
    local_data_dir = Path(sys.argv[4])
    
    if not local_data_dir.exists():
        print(f"❌ Local data directory not found: {local_data_dir}")
        sys.exit(1)
    
    # Initialize Azure File Share client
    account_url = f"https://{account_name}.file.core.windows.net"
    share_client = ShareClient(account_url=account_url, share_name=share_name, credential=account_key)
    
    # Verify share exists
    try:
        share_client.get_share_properties()
    except ResourceNotFoundError:
        print(f"❌ File share '{share_name}' not found. Please create it first.")
        sys.exit(1)
    
    print(f"📦 Migrating data from {local_data_dir} to Azure File Share: {share_name}")
    print("")
    
    # Migrate all files
    migrated, errors = migrate_directory(share_client, local_data_dir)
    
    print("")
    print("=========================================")
    print(f"✅ Migration complete!")
    print(f"   Files migrated: {migrated}")
    if errors > 0:
        print(f"   Errors: {errors}")
    print("=========================================")

if __name__ == "__main__":
    main()

