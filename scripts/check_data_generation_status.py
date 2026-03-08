#!/usr/bin/env python3
"""Check data generation status by querying database directly"""
import sys
from pathlib import Path

# Add API source to path
api_src = Path(__file__).parent.parent / "apps" / "api" / "src"
sys.path.insert(0, str(api_src))

from uepi_api.database import SessionLocal
from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uuid import UUID
from datetime import date

def main():
    print("=" * 70)
    print("CHECKING DATA GENERATION STATUS")
    print("=" * 70)
    print()
    
    tenant_id = UUID('00000000-0000-0000-0000-000000000001')
    db = SessionLocal()
    
    try:
        repo = CanonicalDataRepository(db)
        
        # Check 1: Total claims count
        print("1️⃣  Total Claims in Database:")
        total_count = repo.count_claims_lines(tenant_id)
        print(f"   📊 Total claims: {total_count:,}")
        print()
        
        # Check 2: Claims for Feb 1 - Mar 2, 2024
        print("2️⃣  Claims for Observation Period (Feb 1 - Mar 2, 2024):")
        start_date = date(2024, 2, 1)
        end_date = date(2024, 3, 2)
        
        claims_df = repo.get_claims_lines(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        if not claims_df.empty:
            print(f"   ✅ Found {len(claims_df):,} claims in date range")
            print(f"   📊 Date range: {start_date} to {end_date}")
            
            # Check date distribution
            if 'service_date' in claims_df.columns:
                dates = claims_df['service_date'].value_counts().sort_index()
                print(f"   📅 Date distribution:")
                print(f"      First date: {dates.index.min()}")
                print(f"      Last date: {dates.index.max()}")
                print(f"      Unique dates: {len(dates)}")
                print(f"      Average claims per day: {len(claims_df) / max(1, len(dates)):.0f}")
            
            # Check totals
            if 'paid_amount' in claims_df.columns:
                total_paid = claims_df['paid_amount'].sum()
                print(f"   💰 Total paid amount: ${total_paid:,.2f}")
            
            if 'member_id' in claims_df.columns:
                unique_members = claims_df['member_id'].nunique()
                print(f"   👥 Unique members: {unique_members:,}")
        else:
            print(f"   ❌ No claims found for date range {start_date} to {end_date}")
            print()
            print("   📋 Checking if ANY claims exist in database...")
            
            # Check if any claims exist at all
            all_claims = repo.get_claims_lines(tenant_id=tenant_id, limit=100)
            if not all_claims.empty:
                print(f"   ⚠️  Found {len(all_claims)} claims in database, but none in observation period")
                if 'service_date' in all_claims.columns:
                    min_date = all_claims['service_date'].min()
                    max_date = all_claims['service_date'].max()
                    print(f"   📅 Available date range: {min_date} to {max_date}")
            else:
                print(f"   ❌ No claims found in database at all")
        
        print()
        
        # Check 3: Sample dates
        print("3️⃣  Checking sample dates:")
        sample_dates = [
            date(2024, 2, 1),
            date(2024, 2, 15),
            date(2024, 3, 1),
        ]
        
        for sample_date in sample_dates:
            sample_df = repo.get_claims_lines(
                tenant_id=tenant_id,
                start_date=sample_date,
                end_date=sample_date,
            )
            if not sample_df.empty:
                print(f"   ✅ {sample_date}: {len(sample_df):,} claims")
            else:
                print(f"   ❌ {sample_date}: No claims")
        
        print()
        
        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        if not claims_df.empty:
            print(f"✅ Data generation appears COMPLETE")
            print(f"   Found {len(claims_df):,} claims for observation period")
            print(f"   Ready to recreate observation")
        else:
            print(f"⚠️  Data generation may still be IN PROGRESS")
            print(f"   No claims found for observation period yet")
            print(f"   Check API logs for background job progress")
            print(f"   Or wait a few more minutes and check again")
        print()
        
    except Exception as e:
        import traceback
        print(f"❌ Error checking database: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
