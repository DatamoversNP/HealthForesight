#!/usr/bin/env python3
"""Test policies query directly"""

import sys
from uuid import UUID
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import models
sys.path.insert(0, '/Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api/src')
sys.path.insert(0, '/Users/nilesh/Downloads/uepi-migration-20260123-151729/packages/common/src')

from uepi_api.models.policy import Policy

# Database connection
db_url = "postgresql://postgres:postgres@localhost:5432/uepi_db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def test_policies_query():
    """Test querying policies"""
    print("="*80)
    print("TESTING POLICIES QUERY")
    print("="*80)
    print()
    
    db = SessionLocal()
    try:
        demo_tenant_id = UUID("00000000-0000-0000-0000-000000000001")
        
        # Test 1: Count all policies
        print("Test 1: Count all policies...")
        total = db.query(Policy).count()
        print(f"   Total policies: {total}")
        
        # Test 2: Count policies for demo tenant
        print()
        print("Test 2: Count policies for demo tenant...")
        count = db.query(Policy).filter(Policy.tenant_id == demo_tenant_id).count()
        print(f"   Policies for tenant {demo_tenant_id}: {count}")
        
        # Test 3: Get first few policies
        print()
        print("Test 3: Get first 5 policies...")
        policies = db.query(Policy).filter(Policy.tenant_id == demo_tenant_id).limit(5).all()
        print(f"   Found {len(policies)} policies:")
        for p in policies:
            print(f"      - {p.id}: {p.name} (tenant: {p.tenant_id})")
        
        # Test 4: Check tenant_id types
        print()
        print("Test 4: Check tenant_id types in database...")
        result = db.execute(text("""
            SELECT tenant_id, pg_typeof(tenant_id) as type
            FROM policies 
            LIMIT 1
        """))
        row = result.fetchone()
        if row:
            print(f"   tenant_id type in DB: {row[1]}")
            print(f"   tenant_id value: {row[0]} (type: {type(row[0])})")
        
        # Test 5: Try the exact query from the API
        print()
        print("Test 5: Try exact API query...")
        query = db.query(Policy).filter(Policy.tenant_id == demo_tenant_id)
        policies = query.order_by(Policy.created_at.desc()).limit(10).all()
        print(f"   Found {len(policies)} policies with exact API query")
        
        if policies:
            print("   First policy:")
            p = policies[0]
            print(f"      id: {p.id} (type: {type(p.id)})")
            print(f"      tenant_id: {p.tenant_id} (type: {type(p.tenant_id)})")
            print(f"      name: {p.name}")
            print(f"      policy_type: {p.policy_type}")
            print(f"      status: {getattr(p, 'status', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_policies_query()
