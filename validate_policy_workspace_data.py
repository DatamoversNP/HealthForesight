#!/usr/bin/env python3
"""Validate that all policies have assumptions, guardrails, and versions"""

import json
from pathlib import Path

data_dir = Path('data')
policy_files = list(data_dir.glob('policy_*.json'))

print("🔍 Validating Policy Workspace Data")
print("=" * 70)
print()

results = []
for policy_file in sorted(policy_files):
    try:
        with open(policy_file, 'r') as f:
            policy = json.load(f)
        
        policy_id = policy.get('policy_id', 'UNKNOWN')
        metadata = policy.get('metadata', {})
        
        assumptions = metadata.get('assumptions', [])
        guardrails = metadata.get('guardrails', [])
        versions = metadata.get('versions', [])
        changelog = metadata.get('changelog', [])
        
        assumptions_count = len(assumptions) if isinstance(assumptions, list) else 0
        guardrails_count = len(guardrails) if isinstance(guardrails, list) else 0
        versions_count = len(versions) if isinstance(versions, list) else 0
        changelog_count = len(changelog) if isinstance(changelog, list) else 0
        
        has_all = assumptions_count > 0 and guardrails_count > 0 and versions_count > 0
        
        status = "✅" if has_all else "⚠️"
        results.append({
            'policy_id': policy_id,
            'assumptions': assumptions_count,
            'guardrails': guardrails_count,
            'versions': versions_count,
            'changelog': changelog_count,
            'has_all': has_all
        })
        
        print(f"{status} {policy_id:30} | A:{assumptions_count:2} G:{guardrails_count:2} V:{versions_count:2} C:{changelog_count:2}")
    except Exception as e:
        print(f"❌ {policy_file.name:30} | ERROR: {e}")

print()
print("=" * 70)
print("📊 Summary:")
print()

total = len(results)
with_all = sum(1 for r in results if r['has_all'])
missing_assumptions = sum(1 for r in results if r['assumptions'] == 0)
missing_guardrails = sum(1 for r in results if r['guardrails'] == 0)
missing_versions = sum(1 for r in results if r['versions'] == 0)
missing_changelog = sum(1 for r in results if r['changelog'] == 0)

print(f"Total policies: {total}")
print(f"✅ Policies with all data (A+G+V): {with_all} ({with_all*100//total if total > 0 else 0}%)")
print(f"⚠️  Missing assumptions: {missing_assumptions}")
print(f"⚠️  Missing guardrails: {missing_guardrails}")
print(f"⚠️  Missing versions: {missing_versions}")
print(f"⚠️  Missing changelog: {missing_changelog}")

if missing_assumptions > 0 or missing_guardrails > 0 or missing_versions > 0:
    print()
    print("📋 Policies missing data:")
    for r in results:
        if not r['has_all']:
            missing = []
            if r['assumptions'] == 0:
                missing.append('assumptions')
            if r['guardrails'] == 0:
                missing.append('guardrails')
            if r['versions'] == 0:
                missing.append('versions')
            print(f"  - {r['policy_id']}: missing {', '.join(missing)}")

