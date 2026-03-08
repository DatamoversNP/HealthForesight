#!/usr/bin/env python3
"""
Test script for Epic 3: Decision Audit & Defensibility
Tests decision creation, evidence linking, and audit trail
"""
import sys
import json
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_decisions import (
    create_decision,
    get_decision,
    list_decisions,
    update_decision,
    finalize_decision,
    add_approval,
)
from uepi_api.storage_audit_trail import (
    create_audit_entry,
    get_audit_trail,
    get_reproducibility_pack,
)
from uepi_api.storage_evidence import (
    get_evidence_links,
    get_evidence_for_decision,
    create_evidence_snapshot,
    link_evidence,
)
# Note: Not importing get_policy to avoid boto3 permission issues

# Demo tenant ID
DEMO_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def get_first_policy_id():
    """Get the first available policy ID for testing"""
    try:
        # Try to get a policy from storage
        policies_dir = project_root / "data" / "policies"
        tenant_dirs = [d for d in policies_dir.iterdir() if d.is_dir()]
        
        if tenant_dirs:
            tenant_dir = tenant_dirs[0]
            policy_files = list(tenant_dir.glob("policy-*.json"))
            if policy_files:
                # Read first policy file
                with open(policy_files[0], 'r') as f:
                    policy_data = json.load(f)
                    policy_id = policy_data.get("id") or policy_data.get("policy_id")
                    if policy_id:
                        return UUID(policy_id) if isinstance(policy_id, str) else policy_id
        
        # Fallback: try to get from API storage
        try:
            policies = []
            # Check index.json
            index_file = policies_dir / "index.json"
            if index_file.exists():
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
                    policies = index_data.get("policies", [])
            
            if policies:
                policy_id = policies[0].get("id") or policies[0].get("policy_id")
                if policy_id:
                    return UUID(policy_id) if isinstance(policy_id, str) else policy_id
        except Exception as e:
            print(f"  ⚠️  Could not read from index: {e}")
        
        # Return a test UUID if nothing found
        print("  ⚠️  No policies found, using test UUID")
        return UUID("10000000-0000-0000-0000-000000000001")
    except Exception as e:
        print(f"  ⚠️  Error getting policy ID: {e}")
        return UUID("10000000-0000-0000-0000-000000000001")


def test_create_decision():
    """Test creating a decision"""
    print("\n" + "="*70)
    print("TEST 1: Create Decision")
    print("="*70)
    
    try:
        policy_id = get_first_policy_id()
        print(f"  Using policy ID: {policy_id}")
        
        decision_data = {
            "title": "Approve Outpatient MRI Prior Authorization Policy",
            "recommendation": "Approve policy for implementation based on strong predicted impact",
            "rationale": "Predicted impact shows 15% utilization reduction with minimal access risk. Confidence score of 0.85 based on historical data and elasticity models.",
            "confidence_score": 0.85,
            "uncertainty_range": {
                "p10": 0.10,
                "p50": 0.15,
                "p90": 0.20,
            },
            "confidence_interval": {
                "lower_bound": 0.12,
                "upper_bound": 0.18,
                "confidence_level": 0.95,
            },
            "policy_id": str(policy_id),
            "analysis_ids": [str(uuid4())],  # Mock analysis ID
            "evidence_links": [],
            "assumptions_snapshot": {
                "elasticity": -0.15,
                "substitution_rate": 0.3,
                "lag_months": 3,
            },
            "status": "DRAFT",
            "created_by": str(DEMO_USER_ID),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        decision = create_decision(DEMO_TENANT_ID, decision_data)
        print(f"  ✅ Decision created successfully!")
        print(f"     ID: {decision.id}")
        print(f"     Title: {decision.title}")
        print(f"     Status: {decision.status}")
        print(f"     Confidence: {decision.confidence_score}")
        
        return decision
    except Exception as e:
        print(f"  ❌ Failed to create decision: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_decision(decision_id: UUID):
    """Test retrieving a decision"""
    print("\n" + "="*70)
    print("TEST 2: Get Decision")
    print("="*70)
    
    try:
        decision = get_decision(DEMO_TENANT_ID, decision_id)
        if decision:
            print(f"  ✅ Decision retrieved successfully!")
            print(f"     ID: {decision.id}")
            print(f"     Title: {decision.title}")
            print(f"     Recommendation: {decision.recommendation[:50]}...")
            print(f"     Status: {decision.status}")
            return decision
        else:
            print(f"  ❌ Decision not found")
            return None
    except Exception as e:
        print(f"  ❌ Failed to get decision: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_list_decisions():
    """Test listing decisions"""
    print("\n" + "="*70)
    print("TEST 3: List Decisions")
    print("="*70)
    
    try:
        decisions = list_decisions(DEMO_TENANT_ID)
        print(f"  ✅ Found {len(decisions)} decisions")
        for decision in decisions[:5]:  # Show first 5
            print(f"     - {decision.title} ({decision.status})")
        return decisions
    except Exception as e:
        print(f"  ❌ Failed to list decisions: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_create_audit_entry(decision_id: UUID):
    """Test creating an audit trail entry"""
    print("\n" + "="*70)
    print("TEST 4: Create Audit Trail Entry")
    print("="*70)
    
    try:
        entry_data = {
            "step_type": "analysis",
            "step_id": str(uuid4()),
            "step_version": "1.0",
            "input_data": {
                "policy_id": str(decision_id),
                "method": "difference_in_differences",
            },
            "output_data": {
                "effect_size": -0.15,
                "p_value": 0.001,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "performed_by": str(DEMO_USER_ID),
        }
        
        entry = create_audit_entry(DEMO_TENANT_ID, decision_id, entry_data)
        print(f"  ✅ Audit entry created successfully!")
        print(f"     Entry ID: {entry.entry_id}")
        print(f"     Step Type: {entry.step_type}")
        print(f"     Input Hash: {entry.input_hash[:16]}...")
        print(f"     Output Hash: {entry.output_hash[:16]}...")
        return entry
    except Exception as e:
        print(f"  ❌ Failed to create audit entry: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_audit_trail(decision_id: UUID):
    """Test retrieving audit trail"""
    print("\n" + "="*70)
    print("TEST 5: Get Audit Trail")
    print("="*70)
    
    try:
        audit_trail = get_audit_trail(DEMO_TENANT_ID, decision_id)
        print(f"  ✅ Retrieved {len(audit_trail)} audit entries")
        for entry in audit_trail:
            print(f"     - {entry.step_type} at {entry.timestamp}")
            if entry.input_hash:
                print(f"       Input Hash: {entry.input_hash[:16]}...")
            if entry.output_hash:
                print(f"       Output Hash: {entry.output_hash[:16]}...")
        return audit_trail
    except Exception as e:
        print(f"  ❌ Failed to get audit trail: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_link_evidence(decision_id: UUID):
    """Test linking evidence to a decision"""
    print("\n" + "="*70)
    print("TEST 6: Link Evidence")
    print("="*70)
    
    try:
        # First, update the decision to add evidence link
        from uepi_common.models_enhanced import EvidenceLink
        
        evidence_link = EvidenceLink(
            evidence_type="analysis",
            evidence_id=uuid4(),
            evidence_version="1.0",
            description="Difference-in-Differences analysis showing 15% utilization reduction",
        )
        
        # Update decision with evidence link
        decision = get_decision(DEMO_TENANT_ID, decision_id)
        if decision:
            current_links = decision.evidence_links
            current_links.append(evidence_link)
            
            updated_decision = update_decision(
                DEMO_TENANT_ID,
                decision_id,
                {"evidence_links": [el.model_dump(mode='json', exclude_none=True) for el in current_links]}
            )
            
            if updated_decision:
                print(f"  ✅ Evidence linked successfully!")
                print(f"     Evidence Type: {evidence_link.evidence_type}")
                print(f"     Evidence ID: {evidence_link.evidence_id}")
                print(f"     Total Evidence Links: {len(updated_decision.evidence_links)}")
                return updated_decision
        
        print(f"  ❌ Failed to link evidence")
        return None
    except Exception as e:
        print(f"  ❌ Failed to link evidence: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_create_evidence_snapshot():
    """Test creating an evidence snapshot"""
    print("\n" + "="*70)
    print("TEST 7: Create Evidence Snapshot")
    print("="*70)
    
    try:
        evidence_id = uuid4()
        snapshot_data = {
            "analysis_id": str(uuid4()),
            "method": "difference_in_differences",
            "results": {
                "effect_size": -0.15,
                "p_value": 0.001,
                "confidence_interval": [0.12, 0.18],
            },
            "created_at": datetime.utcnow().isoformat(),
        }
        
        snapshot_hash = create_evidence_snapshot(
            DEMO_TENANT_ID,
            "analysis",
            evidence_id,
            snapshot_data,
            version="1.0"
        )
        
        print(f"  ✅ Evidence snapshot created!")
        print(f"     Evidence ID: {evidence_id}")
        print(f"     Snapshot Hash: {snapshot_hash[:32]}...")
        return snapshot_hash
    except Exception as e:
        print(f"  ❌ Failed to create evidence snapshot: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_add_approval(decision_id: UUID):
    """Test adding an approval to a decision"""
    print("\n" + "="*70)
    print("TEST 8: Add Approval")
    print("="*70)
    
    try:
        approval_data = {
            "role": "POLICY_OWNER",
            "comment": "Approved based on strong predicted impact and low risk profile",
        }
        
        decision = add_approval(DEMO_TENANT_ID, decision_id, approval_data)
        if decision:
            print(f"  ✅ Approval added successfully!")
            print(f"     Total Approvals: {len(decision.approvals)}")
            for approval in decision.approvals:
                print(f"     - {approval.get('role')} at {approval.get('approved_at')}")
            return decision
        else:
            print(f"  ❌ Failed to add approval")
            return None
    except Exception as e:
        print(f"  ❌ Failed to add approval: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_finalize_decision(decision_id: UUID):
    """Test finalizing a decision"""
    print("\n" + "="*70)
    print("TEST 9: Finalize Decision")
    print("="*70)
    
    try:
        decision = finalize_decision(DEMO_TENANT_ID, decision_id, DEMO_USER_ID)
        if decision:
            print(f"  ✅ Decision finalized successfully!")
            print(f"     Status: {decision.status}")
            print(f"     Finalized At: {decision.finalized_at}")
            print(f"     Finalized By: {decision.finalized_by}")
            return decision
        else:
            print(f"  ❌ Failed to finalize decision")
            return None
    except Exception as e:
        print(f"  ❌ Failed to finalize decision: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_reproducibility_pack(decision_id: UUID):
    """Test generating reproducibility pack"""
    print("\n" + "="*70)
    print("TEST 10: Generate Reproducibility Pack")
    print("="*70)
    
    try:
        pack = get_reproducibility_pack(DEMO_TENANT_ID, decision_id)
        if pack:
            print(f"  ✅ Reproducibility pack generated!")
            print(f"     Decision ID: {pack.get('decision_id')}")
            print(f"     Audit Trail Entries: {len(pack.get('audit_trail', []))}")
            print(f"     Steps: {len(pack.get('steps', []))}")
            print(f"     Evidence Links: {len(pack.get('evidence_links', []))}")
            print(f"     Generated At: {pack.get('generated_at')}")
            return pack
        else:
            print(f"  ❌ Failed to generate reproducibility pack")
            return None
    except Exception as e:
        print(f"  ❌ Failed to generate reproducibility pack: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("EPIC 3: DECISION AUDIT & DEFENSIBILITY - TEST SUITE")
    print("="*70)
    
    # Test 1: Create Decision
    decision = test_create_decision()
    if not decision:
        print("\n❌ Cannot continue tests - decision creation failed")
        return 1
    
    decision_id = decision.id
    
    # Test 2: Get Decision
    test_get_decision(decision_id)
    
    # Test 3: List Decisions
    test_list_decisions()
    
    # Test 4: Create Audit Entry
    test_create_audit_entry(decision_id)
    
    # Test 5: Get Audit Trail
    test_get_audit_trail(decision_id)
    
    # Test 6: Link Evidence
    test_link_evidence(decision_id)
    
    # Test 7: Create Evidence Snapshot
    test_create_evidence_snapshot()
    
    # Test 8: Add Approval
    test_add_approval(decision_id)
    
    # Test 9: Finalize Decision
    test_finalize_decision(decision_id)
    
    # Test 10: Generate Reproducibility Pack
    test_reproducibility_pack(decision_id)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("✅ All Epic 3 tests completed!")
    print(f"   Decision ID: {decision_id}")
    print(f"   Check data/decisions/{DEMO_TENANT_ID}/decision-{decision_id}.json")
    print(f"   Check data/audit_trail/{DEMO_TENANT_ID}/decision-{decision_id}/audit_trail.json")
    print("="*70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

