#!/usr/bin/env python3
"""Check what data actually exists in the database"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'common', 'src'))

from uepi_api.database import SessionLocal
from uepi_api.models.policy import Policy
from uepi_api.models.observation import Observation
from uepi_api.models.analysis import Analysis
from sqlalchemy import func, distinct
from uuid import UUID

def check_database_data():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("DATABASE DATA CHECK")
        print("=" * 60)
        print()
        
        # Check policies
        print("POLICIES:")
        print("-" * 60)
        total_policies = db.query(Policy).count()
        print(f"Total policies in database: {total_policies}")
        
        if total_policies > 0:
            # Get all tenant IDs
            tenant_ids = db.query(distinct(Policy.tenant_id)).all()
            print(f"Tenant IDs in policies table: {[str(t[0]) for t in tenant_ids]}")
            
            # Show policies per tenant
            for tenant_id_tuple in tenant_ids:
                tenant_id = tenant_id_tuple[0]
                count = db.query(Policy).filter(Policy.tenant_id == tenant_id).count()
                print(f"  Tenant {tenant_id}: {count} policies")
                
                # Show first few policy names
                policies = db.query(Policy).filter(Policy.tenant_id == tenant_id).limit(5).all()
                if policies:
                    print(f"    Sample policies:")
                    for p in policies:
                        print(f"      - {p.name} (ID: {p.id}, Status: {p.status})")
        print()
        
        # Check observations
        print("OBSERVATIONS:")
        print("-" * 60)
        total_observations = db.query(Observation).count()
        print(f"Total observations in database: {total_observations}")
        
        if total_observations > 0:
            # Get all tenant IDs
            tenant_ids = db.query(distinct(Observation.tenant_id)).all()
            print(f"Tenant IDs in observations table: {[str(t[0]) for t in tenant_ids]}")
            
            # Show observations per tenant
            for tenant_id_tuple in tenant_ids:
                tenant_id = tenant_id_tuple[0]
                count = db.query(Observation).filter(Observation.tenant_id == tenant_id).count()
                print(f"  Tenant {tenant_id}: {count} observations")
        print()
        
        # Check analyses
        print("ANALYSES:")
        print("-" * 60)
        total_analyses = db.query(Analysis).count()
        print(f"Total analyses in database: {total_analyses}")
        
        if total_analyses > 0:
            # Get all tenant IDs
            tenant_ids = db.query(distinct(Analysis.tenant_id)).all()
            print(f"Tenant IDs in analyses table: {[str(t[0]) for t in tenant_ids]}")
            
            # Show analyses per tenant
            for tenant_id_tuple in tenant_ids:
                tenant_id = tenant_id_tuple[0]
                count = db.query(Analysis).filter(Analysis.tenant_id == tenant_id).count()
                print(f"  Tenant {tenant_id}: {count} analyses")
        print()
        
        # Check demo tenant ID
        demo_tenant_id = UUID("00000000-0000-0000-0000-000000000001")
        print("DEMO TENANT CHECK:")
        print("-" * 60)
        print(f"Demo tenant ID: {demo_tenant_id}")
        
        demo_policies = db.query(Policy).filter(Policy.tenant_id == demo_tenant_id).count()
        demo_observations = db.query(Observation).filter(Observation.tenant_id == demo_tenant_id).count()
        demo_analyses = db.query(Analysis).filter(Analysis.tenant_id == demo_tenant_id).count()
        
        print(f"Policies for demo tenant: {demo_policies}")
        print(f"Observations for demo tenant: {demo_observations}")
        print(f"Analyses for demo tenant: {demo_analyses}")
        print()
        
        # Summary
        print("SUMMARY:")
        print("-" * 60)
        if total_policies == 0 and total_observations == 0 and total_analyses == 0:
            print("⚠️  Database appears to be EMPTY")
            print("   This could mean:")
            print("   1. Data was never loaded")
            print("   2. Data was deleted")
            print("   3. Wrong database connection")
        elif demo_policies == 0 and demo_observations == 0:
            print("⚠️  Data exists but NOT for demo tenant")
            print(f"   Demo tenant ID: {demo_tenant_id}")
            print("   This means tenant_id mismatch - data exists but for different tenant")
            print("   Solution: Check what tenant_id the data has and update queries")
        else:
            print("✅ Data exists for demo tenant")
            print(f"   Policies: {demo_policies}")
            print(f"   Observations: {demo_observations}")
            print(f"   Analyses: {demo_analyses}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_database_data()
