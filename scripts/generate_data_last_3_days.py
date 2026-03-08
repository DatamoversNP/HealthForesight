#!/usr/bin/env python3
"""Generate claims data for last 3 days and load to database"""
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from sqlalchemy.orm import Session
from uepi_api.database import SessionLocal
from uepi_api.services.data_generation_service import generate_claims_data_for_date
from uepi_api.services.daily_pipeline_service import load_daily_data_from_source

def main():
    """Generate data for last 3 days"""
    tenant_id = UUID('00000000-0000-0000-0000-000000000001')
    db = SessionLocal()
    
    try:
        # Generate data for yesterday, 2 days ago, and 3 days ago
        today = datetime.now().date()
        dates_to_generate = [
            today - timedelta(days=1),  # Yesterday
            today - timedelta(days=2),  # 2 days ago
            today - timedelta(days=3),  # 3 days ago
        ]
        
        print("=" * 80)
        print("GENERATING CLAIMS DATA FOR LAST 3 DAYS")
        print("=" * 80)
        
        total_claims = 0
        for target_date in dates_to_generate:
            print(f"\n📅 Generating data for {target_date}...")
            
            result = generate_claims_data_for_date(
                tenant_id=tenant_id,
                target_date=target_date,
                member_count=10000,
                claims_per_member=2.5,
                db=db,
            )
            
            if result.get("success"):
                claims_count = result.get("claims_loaded", 0)
                total_claims += claims_count
                print(f"✅ Generated and loaded {claims_count} claims for {target_date}")
                print(f"   - Members covered: {result.get('members_covered', 0)}")
            else:
                print(f"❌ Failed to generate data for {target_date}: {result.get('error', 'Unknown error')}")
                if 'traceback' in result:
                    print(f"   Traceback: {result['traceback']}")
        
        print("\n" + "=" * 80)
        print(f"✅ COMPLETE: Generated {total_claims} total claims across 3 days")
        print("=" * 80)
        
        # Now run daily pipeline to ensure data is properly loaded
        print("\n🔄 Running daily pipeline to load data...")
        for target_date in dates_to_generate:
            print(f"   Loading data for {target_date}...")
            load_result = load_daily_data_from_source(
                tenant_id=tenant_id,
                source_date=target_date,
                db=db,
            )
            if load_result.get("success"):
                print(f"   ✅ Loaded {load_result.get('claims_loaded', 0)} claims from source")
            else:
                print(f"   ⚠️  No source data found for {target_date} (data already in database)")
        
        print("\n✅ All data generation and loading complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
