#!/usr/bin/env python3
"""Test workspace API response structure"""
import json
from pathlib import Path

# Simulate what the API should return
policy_file = Path('data/policy_ST_BIOLOGIC_006.json')
with open(policy_file, 'r') as f:
    policy = json.load(f)

metadata = policy.get('metadata', {})
assumptions = metadata.get('assumptions', [])
guardrails = metadata.get('guardrails', [])
versions = metadata.get('versions', [])

# Simulate API response
workspace_response = {
    "policy": policy,
    "versions": versions,
    "assumptions": assumptions,
    "guardrails": guardrails,
    "changelog": metadata.get('changelog', [])
}

print("Workspace Response Structure:")
print(f"  - Policy ID: {workspace_response['policy'].get('policy_id')}")
print(f"  - Assumptions: {len(workspace_response['assumptions'])}")
print(f"  - Guardrails: {len(workspace_response['guardrails'])}")
print(f"  - Versions: {len(workspace_response['versions'])}")
print(f"  - Changelog: {len(workspace_response['changelog'])}")
print()
print("Response keys:", list(workspace_response.keys()))
print()
print("Sample assumption:", json.dumps(assumptions[0] if assumptions else {}, indent=2)[:200])
print()
print("Sample guardrail:", json.dumps(guardrails[0] if guardrails else {}, indent=2)[:200])
print()
print("Sample version:", json.dumps(versions[0] if versions else {}, indent=2)[:200])

