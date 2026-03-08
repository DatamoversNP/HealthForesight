"""Policy storage adapter - supports both database and file-based storage"""
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID
import json

# Make boto3 optional - only import when actually needed (for S3/object storage)
# This allows the API to start locally without boto3 installed or if there are permission issues
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except (ImportError, PermissionError, OSError) as e:
    # boto3 not available or permission denied (e.g., sandbox restrictions)
    boto3 = None
    ClientError = Exception
    BOTO3_AVAILABLE = False
    # Silently continue - local file storage will be used instead

from uepi_common.models import CanonicalPolicy, PolicyType, PolicyStatus
from uepi_api.config import get_settings

settings = get_settings()


class PolicyStorageAdapter:
    """Adapter for policy storage - supports DB (primary) and file-based (fallback)"""
    
    def __init__(self, use_file_storage: bool = False):
        """Initialize storage adapter
        
        Args:
            use_file_storage: If True, use file-based storage (JSON/Parquet) instead of DB
        """
        self.use_file_storage = use_file_storage
        self.s3_client = None
        self.storage_adapter = None
        if use_file_storage:
            # Get storage adapter (local or Azure File Storage)
            try:
                from uepi_api.storage_adapter import get_storage_adapter
                self.storage_adapter = get_storage_adapter()
            except Exception as e:
                print(f"Warning: Could not get storage adapter: {e}. Falling back to local file access.")
                self.storage_adapter = None
            
            # Initialize S3 client for object storage (fallback)
            self.s3_client = self._get_s3_client()
            self.bucket = settings.object_storage.bucket_name_or_bucket
            self.prefix = "policies"  # s3://bucket/policies/{tenant_id}/policies.json
    
    def _get_s3_client(self):
        """Get S3-compatible client (works with MinIO, Azure Blob, AWS S3)"""
        if not BOTO3_AVAILABLE:
            # boto3 not available - return None, will use local file storage only
            return None
        
        endpoint_url = settings.object_storage.endpoint_url_or_none
        if endpoint_url:
            return boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=settings.object_storage.access_key_id_or_access_key,
                aws_secret_access_key=settings.object_storage.secret_access_key_or_secret_key,
                use_ssl=settings.object_storage.use_ssl,
            )
        else:
            # AWS S3 (use IAM role or environment credentials)
            return boto3.client('s3')
    
    def get_policies(self, tenant_id: UUID) -> list[dict[str, Any]]:
        """Get all policies for tenant"""
        if self.use_file_storage:
            return self._load_from_file(tenant_id)
        else:
            # Database storage - return empty, will be handled by DB queries
            return []
    
    def get_policy(self, tenant_id: UUID, policy_id: UUID | str) -> dict[str, Any] | None:
        """Get a single policy by ID"""
        if self.use_file_storage:
            policies = self._load_from_file(tenant_id)
            policy_id_str = str(policy_id)
            for policy in policies:
                # Match by policy_id (can be UUID string or other string ID)
                policy_pid = str(policy.get('policy_id', ''))
                if policy_pid == policy_id_str:
                    return policy
            return None
        else:
            # Database storage - return None, will be handled by DB queries
            return None
    
    def save_policy(self, tenant_id: UUID, policy: CanonicalPolicy) -> dict[str, Any]:
        """Save policy (creates or updates)"""
        if self.use_file_storage:
            return self._save_to_file(tenant_id, policy)
        else:
            # Database storage - return policy dict for DB insert
            return policy.model_dump(mode='json')
    
    def delete_policy(self, tenant_id: UUID, policy_id: UUID | str) -> bool:
        """Delete policy"""
        if self.use_file_storage:
            return self._delete_from_file(tenant_id, policy_id)
        else:
            # Database storage handled by ORM
            return True
    
    def _load_from_file(self, tenant_id: UUID) -> list[dict[str, Any]]:
        """Load policies from JSON file in object storage or local filesystem fallback"""
        # Collect policies from all sources and merge them
        # This ensures we get the most complete data (e.g., predicted_impact from apps/api/data/policies/)
        all_policies_by_id = {}
        tenant_id_str = str(tenant_id)
        
        # If we have a storage adapter (Azure or local), use it first
        if self.storage_adapter:
            try:
                # Try to load from storage adapter (Azure File Storage or local)
                # 1. Try policies/{tenant_id}/policies.json
                policies_path = f"policies/policies_{tenant_id}.json"
                if self.storage_adapter.exists(policies_path):
                    try:
                        policies_data = self.storage_adapter.read_json(policies_path)
                        for policy in policies_data.get('policies', []):
                            pid = str(policy.get('policy_id', ''))
                            if pid and str(policy.get('tenant_id', tenant_id_str)) == tenant_id_str:
                                all_policies_by_id[pid] = policy
                        print(f"✅ Loaded {len(policies_data.get('policies', []))} policies from storage adapter: {policies_path}")
                    except Exception as e:
                        print(f"Warning: Failed to load from storage adapter {policies_path}: {e}")
                
                # 2. Try individual policy files in policies/ directory
                try:
                    if hasattr(self.storage_adapter, 'list_files'):
                        policy_files = self.storage_adapter.list_files("policies", "policy-*.json")
                        for policy_file in policy_files:
                            try:
                                policy = self.storage_adapter.read_json(f"policies/{policy_file}")
                                if isinstance(policy, dict) and 'policy_id' in policy:
                                    if 'tenant_id' not in policy:
                                        policy['tenant_id'] = str(tenant_id)
                                    policy_tenant = str(policy.get('tenant_id', tenant_id))
                                    if policy_tenant == str(tenant_id):
                                        pid = str(policy.get('policy_id', ''))
                                        if pid:
                                            if pid in all_policies_by_id:
                                                existing = all_policies_by_id[pid]
                                                if 'predicted_impact' in policy:
                                                    existing['predicted_impact'] = policy['predicted_impact']
                                                if 'metadata' in policy:
                                                    if 'metadata' not in existing:
                                                        existing['metadata'] = {}
                                                    # CRITICAL FIX: Storage adapter policies may have empty metadata
                                                    # Individual files (loaded later) have complete metadata - preserve it
                                                    policy_metadata = policy.get('metadata', {})
                                                    existing_metadata = existing.get('metadata', {})
                                                    
                                                    # For workspace data, prefer non-empty values from either source
                                                    # But if individual file (loaded later) has it, it takes precedence
                                                    for key in ['assumptions', 'guardrails', 'versions', 'changelog']:
                                                        # If new metadata has this key and it's non-empty, use it
                                                        if key in policy_metadata and policy_metadata[key]:
                                                            existing_metadata[key] = policy_metadata[key]
                                                        # If existing has it and new doesn't, keep existing
                                                        # This preserves metadata from individual files loaded later
                                                    
                                                    # Update other metadata fields (non-workspace data)
                                                    for k, v in policy_metadata.items():
                                                        if k not in ['assumptions', 'guardrails', 'versions', 'changelog']:
                                                            existing_metadata[k] = v
                                                    
                                                    existing['metadata'] = existing_metadata
                                                existing.update({k: v for k, v in policy.items() if k not in ['predicted_impact', 'metadata']})
                                            else:
                                                all_policies_by_id[pid] = policy
                            except Exception as e:
                                print(f"Warning: Failed to load policy file {policy_file}: {e}")
                        if policy_files:
                            print(f"✅ Loaded {len(policy_files)} policy files from storage adapter")
                except Exception as e:
                    print(f"Warning: Could not list policy files from storage adapter: {e}")
                
                # CRITICAL FIX: Don't return early - continue to load local files to merge metadata
                # Storage adapter policies may have empty metadata, local files have full metadata
                if all_policies_by_id:
                    policies_list = list(all_policies_by_id.values())
                    print(f"✅ Loaded {len(policies_list)} unique policies from storage adapter (continuing to load local files for metadata merge)")
                # Continue to fallback section to load local files and merge metadata
            except Exception as e:
                print(f"Warning: Storage adapter load failed: {e}. Falling back to local file access.")
        
        # Fallback to local file paths (for backward compatibility)
        # Get project root - use STORAGE_PATH if set, otherwise calculate from file path
        import os
        if "STORAGE_PATH" in os.environ:
            # If STORAGE_PATH is set, use it directly as data directory
            storage_path = Path(os.environ["STORAGE_PATH"]).resolve()
            if storage_path.name == "data":
                # STORAGE_PATH points to data/, so project_root is parent
                project_root = storage_path.parent
                data_dir = storage_path
            else:
                # STORAGE_PATH might point to project root or data dir
                if (storage_path / "data").exists():
                    project_root = storage_path
                    data_dir = storage_path / "data"
                else:
                    # Assume it's the data directory
                    project_root = storage_path.parent
                    data_dir = storage_path
            print(f"DEBUG: Using STORAGE_PATH: {os.environ['STORAGE_PATH']}")
            print(f"DEBUG: project_root = {project_root}")
            print(f"DEBUG: data_dir = {data_dir}")
        else:
            # Calculate from file path (6 levels up from this file: apps/api/src/uepi_api/storage/policy_storage.py)
            # Make it absolute to avoid issues with working directory
            project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
            data_dir = project_root / "data"
            print(f"DEBUG: Calculated project_root = {project_root}")
            print(f"DEBUG: data_dir = {data_dir}")
        
        print(f"DEBUG: data_dir exists = {data_dir.exists()}")
        if data_dir.exists():
            policy_files = list(data_dir.glob("policy_*.json"))
            print(f"DEBUG: Found {len(policy_files)} policy_*.json files in data_dir")
        
        # 1. /tmp/policies_{tenant_id}.json (migrated location)
        local_path = Path(f"/tmp/policies_{tenant_id}.json")
        if local_path.exists():
            try:
                # Check if file is empty or invalid
                file_size = local_path.stat().st_size
                if file_size > 0:
                    with open(local_path, 'r') as f:
                        content = f.read().strip()
                        if content:  # Only parse if file has content
                            policies_data = json.loads(content)
                            for policy in policies_data.get('policies', []):
                                pid = str(policy.get('policy_id', ''))
                                if pid and str(policy.get('tenant_id', tenant_id_str)) == tenant_id_str:
                                    all_policies_by_id[pid] = policy
                            print(f"✅ Loaded {len(policies_data.get('policies', []))} policies from local file: {local_path}")
                        else:
                            print(f"⚠️  Skipping empty file: {local_path}")
                else:
                    print(f"⚠️  Skipping empty file: {local_path}")
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in {local_path}: {e}. Skipping and trying other sources.")
            except Exception as e:
                print(f"Warning: Failed to load from local file {local_path}: {e}")
        
        # 2. data/policies_{tenant_id}.json (project data directory)
        project_data_path = project_root / "data" / f"policies_{tenant_id}.json"
        if project_data_path.exists():
            try:
                with open(project_data_path, 'r') as f:
                    policies_data = json.load(f)
                    for policy in policies_data.get('policies', []):
                        pid = str(policy.get('policy_id', ''))
                        if pid and str(policy.get('tenant_id', tenant_id_str)) == tenant_id_str:
                            # Merge with existing if present
                            if pid in all_policies_by_id:
                                existing = all_policies_by_id[pid]
                                # Prefer predicted_impact and metadata from policy with more data
                                if 'predicted_impact' in policy and 'predicted_impact' not in existing:
                                    existing['predicted_impact'] = policy['predicted_impact']
                                if 'metadata' in policy:
                                    if 'metadata' not in existing:
                                        existing['metadata'] = {}
                                    # CRITICAL: Preserve workspace metadata (assumptions, guardrails, versions, changelog)
                                    existing_metadata = existing.get('metadata', {})
                                    policy_metadata = policy.get('metadata', {})
                                    # Preserve existing workspace data if new metadata doesn't have it
                                    for key in ['assumptions', 'guardrails', 'versions', 'changelog']:
                                        if key in policy_metadata and policy_metadata[key]:
                                            existing_metadata[key] = policy_metadata[key]
                                        # If new metadata doesn't have it or it's empty, keep existing
                                    # Update other metadata fields
                                    existing_metadata.update({k: v for k, v in policy_metadata.items() if k not in ['assumptions', 'guardrails', 'versions', 'changelog']})
                                    existing['metadata'] = existing_metadata
                                existing.update({k: v for k, v in policy.items() if k not in ['predicted_impact', 'metadata'] or k not in existing})
                            else:
                                all_policies_by_id[pid] = policy
                    print(f"✅ Loaded policies from project data: {project_data_path}")
            except Exception as e:
                print(f"Warning: Failed to load from project data {project_data_path}: {e}")
        
        # 3. data/valid_policies.json (legacy format)
        valid_policies_path = project_root / "data" / "valid_policies.json"
        print(f"DEBUG: Checking valid_policies.json at {valid_policies_path}")
        print(f"DEBUG: File exists: {valid_policies_path.exists()}")
        if valid_policies_path.exists():
            try:
                with open(valid_policies_path, 'r') as f:
                    policies_data = json.load(f)
                    policies = policies_data.get('policies', [])
                    print(f"DEBUG: Found {len(policies)} policies in valid_policies.json")
                    
                    for policy in policies:
                        # Always assign the current tenant_id for policies from valid_policies.json
                        # (this is a legacy file that may have wrong tenant_id)
                        policy['tenant_id'] = tenant_id_str
                        pid = str(policy.get('policy_id', ''))
                        print(f"DEBUG: Processing policy with pid={pid}, name={policy.get('policy_name', policy.get('name', 'N/A'))[:50]}")
                        if pid:
                            # Merge with existing if present
                            if pid in all_policies_by_id:
                                existing = all_policies_by_id[pid]
                                # Prefer predicted_impact and metadata from policy with more data
                                if 'predicted_impact' in policy and 'predicted_impact' not in existing:
                                    existing['predicted_impact'] = policy['predicted_impact']
                                if 'metadata' in policy:
                                    if 'metadata' not in existing:
                                        existing['metadata'] = {}
                                    # CRITICAL: Preserve workspace metadata (assumptions, guardrails, versions, changelog)
                                    existing_metadata = existing.get('metadata', {})
                                    policy_metadata = policy.get('metadata', {})
                                    # Preserve existing workspace data if new metadata doesn't have it
                                    for key in ['assumptions', 'guardrails', 'versions', 'changelog']:
                                        if key in policy_metadata and policy_metadata[key]:
                                            existing_metadata[key] = policy_metadata[key]
                                        # If new metadata doesn't have it or it's empty, keep existing
                                    # Update other metadata fields
                                    existing_metadata.update({k: v for k, v in policy_metadata.items() if k not in ['assumptions', 'guardrails', 'versions', 'changelog']})
                                    existing['metadata'] = existing_metadata
                                existing.update({k: v for k, v in policy.items() if k not in ['predicted_impact', 'metadata'] or k not in existing})
                            else:
                                all_policies_by_id[pid] = policy
                                print(f"DEBUG: Added policy {pid} to all_policies_by_id (now {len(all_policies_by_id)} policies)")
                    loaded_count = len([p for p in policies if str(p.get('policy_id', ''))])
                    if loaded_count > 0:
                        print(f"✅ Loaded {loaded_count} policies from valid_policies.json (assigned tenant_id: {tenant_id_str})")
                    elif policies:
                        print(f"⚠️  Found {len(policies)} policies in valid_policies.json but none had valid policy_id")
            except Exception as e:
                import traceback
                print(f"ERROR: Failed to load from valid_policies.json: {e}")
                traceback.print_exc()
        
        # 4. Policy files in apps/api/data/policies/ directory (alternative location)
        # This location often has the most complete data (including predicted_impact)
        # PRIORITY: Load this AFTER other sources so we can merge predicted_impact into existing policies
        api_data_policies_dir = project_root / "apps" / "api" / "data" / "policies"
        if api_data_policies_dir.exists():
            for policy_file in api_data_policies_dir.glob("policy-*.json"):
                try:
                    with open(policy_file, 'r') as f:
                        policy = json.load(f)
                        if isinstance(policy, dict) and 'policy_id' in policy:
                            if 'tenant_id' not in policy:
                                policy['tenant_id'] = str(tenant_id)
                            policy_tenant = str(policy.get('tenant_id', tenant_id))
                            if policy_tenant == str(tenant_id):
                                pid = str(policy.get('policy_id', ''))
                                if pid:
                                    # Merge with existing or add new
                                    if pid in all_policies_by_id:
                                        existing = all_policies_by_id[pid]
                                        # ALWAYS prefer predicted_impact from apps/api/data/policies/ (most complete)
                                        if 'predicted_impact' in policy:
                                            existing['predicted_impact'] = policy['predicted_impact']
                                        if 'metadata' in policy:
                                            if 'metadata' not in existing:
                                                existing['metadata'] = {}
                                            # CRITICAL FIX: Only update metadata fields that are non-empty
                                            # Don't overwrite existing metadata with empty values
                                            policy_metadata = policy.get('metadata', {})
                                            existing_metadata = existing.get('metadata', {})
                                            
                                            # Merge predicted_impact from this source if present
                                            if 'predicted_impact' in policy_metadata:
                                                existing_metadata['predicted_impact'] = policy_metadata['predicted_impact']
                                            
                                            # Only update other metadata fields if they have actual data
                                            # Preserve existing assumptions, guardrails, versions, changelog if new ones are empty
                                            for key in ['assumptions', 'guardrails', 'versions', 'changelog']:
                                                if key in policy_metadata and policy_metadata[key]:
                                                    # New metadata has this field and it's non-empty
                                                    existing_metadata[key] = policy_metadata[key]
                                                # If new metadata doesn't have it or it's empty, keep existing
                                            
                                            # Update other metadata fields (non-workspace data)
                                            for k, v in policy_metadata.items():
                                                if k not in ['predicted_impact', 'assumptions', 'guardrails', 'versions', 'changelog']:
                                                    existing_metadata[k] = v
                                            
                                            existing['metadata'] = existing_metadata
                                        # Update other fields
                                        existing.update({k: v for k, v in policy.items() if k not in ['predicted_impact', 'metadata']})
                                    else:
                                        all_policies_by_id[pid] = policy
                except Exception as e:
                    print(f"Warning: Failed to load {policy_file.name}: {e}")
            print(f"✅ Merged policies from apps/api/data/policies/")
        
        # 5. Individual policy files in data/ directory (policy_*.json)
        # data_dir is already set above from STORAGE_PATH or project_root calculation
        if not data_dir.exists():
            # Final fallback: try project_root / "data" if data_dir doesn't exist
            fallback_data_dir = project_root / "data"
            if fallback_data_dir.exists():
                data_dir = fallback_data_dir
                print(f"DEBUG: Using fallback data_dir: {data_dir}")
        
        policy_files = list(data_dir.glob("policy_*.json")) if data_dir.exists() else []
        policy_files = [f for f in policy_files if f.name not in ["valid_policies.json", "canonical_policies.json", f"policies_{tenant_id}.json"]]
        print(f"DEBUG: Loading {len(policy_files)} policy files from {data_dir}")
        loaded_count = 0
        for policy_file in policy_files:
            try:
                with open(policy_file, 'r') as f:
                    policy = json.load(f)
                    if isinstance(policy, dict) and 'policy_id' in policy:
                        if 'tenant_id' not in policy:
                            policy['tenant_id'] = str(tenant_id)
                        policy_tenant = str(policy.get('tenant_id', tenant_id))
                        if policy_tenant == str(tenant_id):
                            pid = str(policy.get('policy_id', ''))
                            if pid:
                                # IMPORTANT: Preserve full policy including all metadata
                                # Merge with existing or add new
                                if pid in all_policies_by_id:
                                    existing = all_policies_by_id[pid]
                                    # Prefer predicted_impact from existing if it has it
                                    if 'predicted_impact' in policy and 'predicted_impact' not in existing:
                                        existing['predicted_impact'] = policy['predicted_impact']
                                    # CRITICAL: Individual policy files (data/policy_*.json) are loaded LAST and have the most complete metadata
                                    # ALWAYS prefer metadata from these files - they have assumptions/guardrails/versions
                                    if 'metadata' in policy:
                                        if 'metadata' not in existing:
                                            existing['metadata'] = {}
                                        # Deep merge metadata - individual files have priority for workspace data
                                        existing_metadata = existing.get('metadata', {})
                                        policy_metadata = policy.get('metadata', {})
                                        # CRITICAL FIX: Individual policy files are the source of truth for workspace data
                                        # If the individual file has assumptions/guardrails/versions, use them (even if empty lists)
                                        # This ensures that if a file has metadata, it's used, not overwritten by empty data
                                        for key in ['assumptions', 'guardrails', 'versions', 'changelog']:
                                            if key in policy_metadata:
                                                # Individual file has this key - use it (even if it's an empty list)
                                                # This ensures we don't lose metadata from individual files
                                                existing_metadata[key] = policy_metadata[key]
                                                print(f"DEBUG: Merged {key} from {policy_file.name}: {len(policy_metadata[key]) if isinstance(policy_metadata[key], list) else 'N/A'} items")
                                        # Update other metadata fields (non-workspace data)
                                        existing_metadata.update({k: v for k, v in policy_metadata.items() if k not in ['assumptions', 'guardrails', 'versions', 'changelog']})
                                        existing['metadata'] = existing_metadata
                                    existing.update({k: v for k, v in policy.items() if k not in ['predicted_impact', 'metadata'] or k not in existing})
                                else:
                                    # Add new policy - preserve ALL data including metadata
                                    all_policies_by_id[pid] = policy
                                    loaded_count += 1
                                    assumptions_count = len(policy.get('metadata', {}).get('assumptions', []))
                                    guardrails_count = len(policy.get('metadata', {}).get('guardrails', []))
                                    versions_count = len(policy.get('metadata', {}).get('versions', []))
                                    print(f"DEBUG: Loaded policy {pid} from {policy_file.name} - has metadata: {'metadata' in policy}, assumptions: {assumptions_count}, guardrails: {guardrails_count}, versions: {versions_count}")
            except Exception as e:
                print(f"Warning: Failed to load {policy_file.name}: {e}")
                import traceback
                traceback.print_exc()
        
        if loaded_count > 0:
            print(f"DEBUG: Loaded {loaded_count} new policies from {data_dir}")
        
        # Return merged policies
        if all_policies_by_id:
            policies_list = list(all_policies_by_id.values())
            print(f"✅ Loaded {len(policies_list)} unique policies (merged from all sources)")
            return policies_list
        else:
            import os
            print(f"⚠️  No policies loaded from any source for tenant {tenant_id_str}")
            print(f"DEBUG: project_root = {project_root}")
            print(f"DEBUG: data_dir = {project_root / 'data'}")
            print(f"DEBUG: data_dir exists = {(project_root / 'data').exists()}")
            print(f"DEBUG: STORAGE_PATH = {os.environ.get('STORAGE_PATH', 'NOT SET')}")
            if (project_root / 'data').exists():
                sample = list((project_root / 'data').glob('policy_*.json'))[:3]
                print(f"DEBUG: Sample files: {[f.name for f in sample]}")
            print(f"Checked:")
            print(f"   - /tmp/policies_{tenant_id}.json")
            print(f"   - data/policies_{tenant_id}.json")
            print(f"   - data/valid_policies.json")
            print(f"   - apps/api/data/policies/")
            print(f"   - data/policy_*.json")
        
        # Try object storage (only if S3 client is available)
        if self.s3_client:
            try:
                key = f"{self.prefix}/{tenant_id}/policies.json"
                response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
                policies_data = json.loads(response['Body'].read().decode('utf-8'))
                return policies_data.get('policies', [])
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    # File doesn't exist yet, return empty list
                    return []
                raise
            except Exception as e:
                print(f"Warning: Object storage load failed: {e}")
                # If file storage fails, return empty list (graceful degradation)
                return []
        # S3 client not available - return empty list (will use local files)
        return []
    
    def _save_to_file(self, tenant_id: UUID, policy: CanonicalPolicy) -> dict[str, Any]:
        """Save policy to JSON file in object storage or local file fallback"""
        policy_dict = policy.model_dump(mode='json')
        policy_id_str = str(policy.policy_id)
        
        # First try local filesystem fallback (for development)
        local_path = Path(f"/tmp/policies_{tenant_id}.json")
        
        try:
            # Load existing policies from local file
            policies = []
            if local_path.exists():
                try:
                    with open(local_path, 'r') as f:
                        policies_data = json.load(f)
                        policies = policies_data.get('policies', [])
                except Exception as e:
                    print(f"Warning: Failed to load from local file {local_path}: {e}")
                    policies = []
            
            # Update or add policy
            # IMPORTANT: Preserve predicted_impact and other metadata from existing policy
            updated = False
            for i, existing_policy in enumerate(policies):
                if str(existing_policy.get('policy_id')) == policy_id_str:
                    # Preserve predicted_impact and metadata from existing policy
                    if 'predicted_impact' in existing_policy and 'predicted_impact' not in policy_dict:
                        policy_dict['predicted_impact'] = existing_policy['predicted_impact']
                    if 'metadata' in existing_policy:
                        existing_metadata = existing_policy.get('metadata', {})
                        new_metadata = policy_dict.get('metadata', {})
                        # Merge metadata, preserving predicted_impact
                        if 'predicted_impact' in existing_metadata and 'predicted_impact' not in new_metadata:
                            new_metadata['predicted_impact'] = existing_metadata['predicted_impact']
                        # Merge all metadata
                        merged_metadata = {**existing_metadata, **new_metadata}
                        policy_dict['metadata'] = merged_metadata
                    policies[i] = policy_dict
                    updated = True
                    break
            
            if not updated:
                policies.append(policy_dict)
            
            # Save back to local file
            data = {
                'tenant_id': str(tenant_id),
                'updated_at': datetime.utcnow().isoformat(),
                'policies': policies
            }
            
            with open(local_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"✅ Saved policy to local file: {local_path}")
            return policy_dict
            
        except Exception as local_error:
            print(f"Warning: Failed to save to local file {local_path}: {local_error}")
            # Fall back to S3 (for production) - only if S3 client is available
            if self.s3_client:
                try:
                    key = f"{self.prefix}/{tenant_id}/policies.json"
                    
                    # Load existing policies
                    try:
                        response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
                        data = json.loads(response['Body'].read().decode('utf-8'))
                        policies = data.get('policies', [])
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'NoSuchKey':
                            policies = []
                        else:
                            raise
                    
                    # Update or add policy
                    updated = False
                    for i, existing_policy in enumerate(policies):
                        if str(existing_policy.get('policy_id')) == policy_id_str:
                            policies[i] = policy_dict
                            updated = True
                            break
                    
                    if not updated:
                        policies.append(policy_dict)
                    
                    # Save back to object storage
                    data = {
                        'tenant_id': str(tenant_id),
                        'updated_at': datetime.utcnow().isoformat(),
                        'policies': policies
                    }
                    
                    self.s3_client.put_object(
                        Bucket=self.bucket,
                        Key=key,
                        Body=json.dumps(data, indent=2, default=str).encode('utf-8'),
                        ContentType='application/json'
                    )
                    
                    return policy_dict
                except Exception as s3_error:
                    # If both fail, log error but don't crash
                    print(f"Warning: Failed to save policy to both local file and S3: local={local_error}, s3={s3_error}")
                    return policy.model_dump(mode='json')
            else:
                # S3 client not available - just return the policy dict
                print(f"Warning: Failed to save to local file and S3 client not available: {local_error}")
                return policy.model_dump(mode='json')
    
    def _delete_from_file(self, tenant_id: UUID, policy_id: UUID | str) -> bool:
        """Delete policy from JSON file"""
        # Only use S3 if client is available, otherwise use local file
        if not self.s3_client:
            # S3 not available - deletion from local files not implemented
            # (policies are loaded from multiple sources, deletion would require updating all)
            print(f"Warning: S3 client not available, cannot delete policy from object storage")
            return False
        
        try:
            key = f"{self.prefix}/{tenant_id}/policies.json"
            
            # Load existing policies
            try:
                response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
                data = json.loads(response['Body'].read().decode('utf-8'))
                policies = data.get('policies', [])
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    return False
                raise
            
            # Remove policy
            policy_id_str = str(policy_id)
            policies = [p for p in policies if str(p.get('policy_id')) != policy_id_str]
            
            # Save back
            data = {
                'tenant_id': str(tenant_id),
                'updated_at': datetime.utcnow().isoformat(),
                'policies': policies
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(data, indent=2, default=str).encode('utf-8'),
                ContentType='application/json'
            )
            
            return True
        except Exception as e:
            print(f"Warning: Failed to delete policy from file storage: {e}")
            return False


def get_policy_storage(use_file_storage: bool | None = None) -> PolicyStorageAdapter:
    """Get policy storage adapter
    
    Args:
        use_file_storage: If None, auto-detect based on DB availability
    """
    if use_file_storage is None:
        # Auto-detect: use file storage if DB is not available
        try:
            from uepi_api.database import is_database_available
            db_available = is_database_available()
            use_file_storage = not db_available  # Use file storage if DB unavailable
        except Exception:
            # If we can't check DB, default to file storage as fallback
            use_file_storage = True
            print("Warning: Could not check database availability, defaulting to file-based storage")
    
    return PolicyStorageAdapter(use_file_storage=use_file_storage)

