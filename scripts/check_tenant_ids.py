#!/usr/bin/env python3
"""Check tenant IDs in database vs what the API expects"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
db_url = "postgresql://postgres:postgres@localhost:5432/uepi_db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def check_tenant_ids():
    """Check tenant IDs in policies and users"""
    print("="*80)
    print("CHECKING TENANT IDs")
    print("="*80)
    print()
    
    db = SessionLocal()
    try:
        # Check tenant IDs in policies
        print("Step 1: Checking tenant_ids in policies table...")
        result = db.execute(text("""
            SELECT DISTINCT tenant_id, COUNT(*) as count 
            FROM policies 
            GROUP BY tenant_id 
            ORDER BY count DESC
        """))
        policy_tenants = result.fetchall()
        print(f"Found {len(policy_tenants)} unique tenant_ids in policies:")
        for tenant_id, count in policy_tenants:
            print(f"   - {tenant_id}: {count} policies")
        
        # Check tenant IDs in users
        print()
        print("Step 2: Checking tenant_ids in users table...")
        result = db.execute(text("""
            SELECT DISTINCT tenant_id, COUNT(*) as count 
            FROM users 
            GROUP BY tenant_id 
            ORDER BY count DESC
        """))
        user_tenants = result.fetchall()
        print(f"Found {len(user_tenants)} unique tenant_ids in users:")
        for tenant_id, count in user_tenants:
            print(f"   - {tenant_id}: {count} users")
        
        # Check demo tenant/user
        print()
        print("Step 3: Checking demo tenant and user...")
        result = db.execute(text("""
            SELECT id, name, tenant_id 
            FROM tenants 
            WHERE name LIKE '%Demo%' OR name LIKE '%demo%'
        """))
        demo_tenants = result.fetchall()
        if demo_tenants:
            print("Demo tenants found:")
            for tenant_id, name, _ in demo_tenants:
                print(f"   - {tenant_id}: {name}")
        else:
            print("   No demo tenants found")
        
        result = db.execute(text("""
            SELECT id, email, tenant_id 
            FROM users 
            WHERE email LIKE '%demo%' OR email LIKE '%Demo%'
        """))
        demo_users = result.fetchall()
        if demo_users:
            print("Demo users found:")
            for user_id, email, tenant_id in demo_users:
                print(f"   - {user_id}: {email} (tenant: {tenant_id})")
        else:
            print("   No demo users found")
        
        # Check what tenant_id the demo user should have
        print()
        print("Step 4: Expected demo tenant/user ID...")
        print("   Expected demo tenant ID: 00000000-0000-0000-0000-000000000001")
        print("   Expected demo user ID: 00000000-0000-0000-0000-000000000001")
        
        # Check if policies have this tenant_id
        print()
        print("Step 5: Checking if policies match demo tenant_id...")
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM policies 
            WHERE tenant_id = '00000000-0000-0000-0000-000000000001'::uuid
        """))
        matching_count = result.scalar()
        print(f"   Policies with demo tenant_id: {matching_count}")
        
        if matching_count == 0 and policy_tenants:
            print()
            print("="*80)
            print("⚠️  ISSUE FOUND!")
            print("="*80)
            print("Policies have different tenant_ids than the demo user.")
            print("Options:")
            print("  1. Update policies to use demo tenant_id")
            print("  2. Update demo user to use the tenant_id from policies")
            print()
            if policy_tenants:
                print(f"Suggested fix: Update policies to use tenant_id: {policy_tenants[0][0]}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_tenant_ids()
