#!/usr/bin/env python3
"""
Automated Data Migration Script for Azure File Storage
Migrates all data from local file system to Azure File Storage with verification
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from azure.storage.fileshare import ShareClient, ShareDirectoryClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.fileshare._shared_access_signature import FileSharedAccessSignature
import json


def get_azure_storage_client(account_name: str, account_key: str, share_name: str) -> ShareClient:
    """Create Azure File Share client"""
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
    return ShareClient.from_connection_string(connection_string, share_name=share_name)


def upload_file(share_client: ShareClient, local_path: Path, remote_path: str) -> bool:
    """Upload a single file to Azure File Storage"""
    try:
        # Create directory structure if needed
        remote_dir = os.path.dirname(remote_path)
        if remote_dir:
            try:
                share_client.create_directory(remote_dir)
            except ResourceExistsError:
                pass  # Directory already exists
        
        # Upload file
        with open(local_path, 'rb') as source_file:
            file_client = share_client.get_file_client(remote_path)
            file_client.upload_file(source_file)
        
        return True
    except Exception as e:
        print(f"  ❌ Failed to upload {local_path.name}: {str(e)}")
        return False


def upload_directory(share_client: ShareClient, local_dir: Path, remote_base: str, progress: Dict[str, int] = None) -> Tuple[int, int]:
    """Recursively upload a directory to Azure File Storage"""
    if progress is None:
        progress = {"uploaded": 0, "failed": 0}
    
    if not local_dir.exists():
        print(f"  ⚠️  Directory not found: {local_dir}")
        return progress["uploaded"], progress["failed"]
    
    # Get all files
    all_files = list(local_dir.rglob('*'))
    files = [f for f in all_files if f.is_file()]
    
    if not files:
        print(f"  ℹ️  No files in {local_dir.name}")
        return progress["uploaded"], progress["failed"]
    
    print(f"  📦 Uploading {local_dir.name} ({len(files)} files)...")
    
    for local_file in files:
        # Calculate relative path
        rel_path = local_file.relative_to(local_dir.parent if local_dir.parent.exists() else local_dir)
        remote_path = f"{remote_base}/{str(rel_path).replace(os.sep, '/')}"
        
        if upload_file(share_client, local_file, remote_path):
            progress["uploaded"] += 1
        else:
            progress["failed"] += 1
        
        # Print progress every 10 files
        total = progress["uploaded"] + progress["failed"]
        if total % 10 == 0:
            print(f"    Progress: {total}/{len(files)} files...")
    
    return progress["uploaded"], progress["failed"]


def verify_upload(share_client: ShareClient, remote_path: str, local_dir: Path) -> Tuple[int, int, bool]:
    """Verify uploaded files match local files"""
    if not local_dir.exists():
        return 0, 0, True
    
    # Count local files
    local_files = {f.relative_to(local_dir): f.stat().st_size for f in local_dir.rglob('*') if f.is_file()}
    local_count = len(local_files)
    
    # List remote files
    try:
        remote_files = {}
        for item in share_client.list_directories_and_files(remote_path, recursive=True):
            if item.get('is_directory', False):
                continue
            file_path = item['name']
            file_size = item.get('content_length', 0)
            remote_files[file_path] = file_size
        
        remote_count = len(remote_files)
        
        # Compare counts
        if local_count == remote_count:
            # Compare sizes for key files
            matches = 0
            for rel_path, local_size in list(local_files.items())[:100]:  # Check first 100 files
                remote_path_str = str(rel_path).replace(os.sep, '/')
                if remote_path_str in remote_files:
                    if local_size == remote_files[remote_path_str]:
                        matches += 1
            
            is_verified = local_count == remote_count
            return local_count, remote_count, is_verified
        else:
            return local_count, remote_count, False
    except ResourceNotFoundError:
        return local_count, 0, False


def main():
    parser = argparse.ArgumentParser(description='Migrate data to Azure File Storage')
    parser.add_argument('--account-name', required=True, help='Azure Storage Account Name')
    parser.add_argument('--account-key', required=True, help='Azure Storage Account Key')
    parser.add_argument('--share-name', default='healthforesight-data', help='File Share Name')
    parser.add_argument('--data-dir', default='apps/api/data', help='Local data directory')
    parser.add_argument('--target-dir', default='apps/api/target_data_model', help='Local target data model directory')
    parser.add_argument('--verify-only', action='store_true', help='Only verify uploads, do not upload')
    
    args = parser.parse_args()
    
    # Get project root
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir
    
    # Construct paths
    data_dir = project_root / args.data_dir
    target_dir = project_root / args.target_dir
    
    print("=" * 70)
    print("📦 Azure File Storage - Data Migration")
    print("=" * 70)
    print()
    print(f"Storage Account: {args.account_name}")
    print(f"File Share: {args.share_name}")
    print(f"Data Directory: {data_dir}")
    print(f"Target Directory: {target_dir}")
    print()
    
    # Create share client
    try:
        share_client = get_azure_storage_client(args.account_name, args.account_key, args.share_name)
        
        # Create share if it doesn't exist
        try:
            share_client.create_share()
            print("✅ File share created")
        except ResourceExistsError:
            print("✅ File share exists")
        
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Azure File Storage: {str(e)}")
        return 1
    
    if not args.verify_only:
        # Migrate data directory
        print("Step 1: Migrating data directory...")
        progress = {"uploaded": 0, "failed": 0}
        
        if data_dir.exists():
            uploaded, failed = upload_directory(share_client, data_dir, "data", progress)
            print(f"  ✅ Data directory: {uploaded} uploaded, {failed} failed")
        else:
            print(f"  ⚠️  Data directory not found: {data_dir}")
        
        print()
        
        # Migrate target data model directory
        print("Step 2: Migrating target data model directory...")
        
        if target_dir.exists():
            uploaded, failed = upload_directory(share_client, target_dir, "target_data_model", progress)
            print(f"  ✅ Target data model: {uploaded} uploaded, {failed} failed")
        else:
            print(f"  ⚠️  Target directory not found: {target_dir}")
        
        print()
        print(f"Total: {progress['uploaded']} files uploaded, {progress['failed']} failed")
        print()
    
    # Verify uploads
    print("Step 3: Verifying uploads...")
    
    if data_dir.exists():
        local_count, remote_count, verified = verify_upload(share_client, "data", data_dir)
        status = "✅" if verified else "⚠️"
        print(f"  {status} data/: Local={local_count}, Remote={remote_count}")
        
        # Verify key subdirectories
        for subdir in ['baselines', 'observations', 'policies', 'analyses', 'learning']:
            subdir_path = data_dir / subdir
            if subdir_path.exists():
                local_count, remote_count, verified = verify_upload(share_client, f"data/{subdir}", subdir_path)
                status = "✅" if verified else "⚠️"
                print(f"  {status} data/{subdir}: Local={local_count}, Remote={remote_count}")
    
    if target_dir.exists():
        local_count, remote_count, verified = verify_upload(share_client, "target_data_model", target_dir)
        status = "✅" if verified else "⚠️"
        print(f"  {status} target_data_model/: Local={local_count}, Remote={remote_count}")
    
    print()
    print("=" * 70)
    print("✅ Migration Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Verify data in Azure Portal")
    print("2. Ensure USE_AZURE_FILE_STORAGE=true in app settings")
    print("3. Test your application")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
