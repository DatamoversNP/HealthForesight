#!/usr/bin/env python3
"""Create observations directly from claims data without requiring API/database"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, UTC
from uuid import UUID
import polars as pl

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
POLICY_EFFECTIVE_DATE = datetime(2024, 12, 1)


def load_claims_data():
    """Load claims data from CSV"""
    claims_file = project_root / "apps" / "data" / "target_data_model" / str(DEFAULT_TENANT_ID) / "CLAIMS_LINES" / "claims_lines.csv"
    
    if not claims_file.exists():
        print(f"❌ Claims file not found: {claims_file}")
        return None
    
    print(f"✅ Loading claims from: {claims_file}")
    print(f"   File size: {claims_file.stat().st_size / (1024*1024):.2f} MB")
    
    try:
        # Load with polars (more efficient for large files)
        df = pl.scan_csv(str(claims_file), try_parse_dates=True).collect()
        print(f"✅ Loaded {len(df):,} claims")
        return df
    except Exception as e:
        print(f"❌ Error loading claims: {e}")
        return None


def compute_metrics_from_claims(df: pl.DataFrame, start_date: datetime, end_date: datetime):
    """Compute metrics from claims data for a date range"""
    # Filter by date - use service_from_date which exists in the CSV
    date_col = "service_from_date"
    
    if date_col not in df.columns:
        print(f"⚠️  Date column '{date_col}' not found. Available columns: {df.columns[:10].to_list()}")
        return {
            "utilization_per_1k": 0.0,
            "allowed_pmpm": 0.0,
            "paid_pmpm": 0.0,
            "total_claims": 0,
            "total_allowed": 0.0,
            "total_paid": 0.0,
            "member_months": 0,
        }
    
    # Filter by date range - handle different date formats
    start_date_date = start_date.date() if isinstance(start_date, datetime) else start_date
    end_date_date = end_date.date() if isinstance(end_date, datetime) else end_date
    
    print(f"   Filtering claims: {date_col} between {start_date_date} and {end_date_date}")
    
    # Check the actual dtype of the date column
    date_dtype = df[date_col].dtype
    print(f"   Date column dtype: {date_dtype}")
    
    # Try different filtering approaches based on dtype
    filtered_df = None
    try:
        if date_dtype == pl.Date:
            # Already a date type - direct comparison
            filtered_df = df.filter(
                (pl.col(date_col) >= start_date_date) & 
                (pl.col(date_col) < end_date_date)
            )
            print(f"   ✅ Filtered to {len(filtered_df):,} claims (Date type)")
        elif date_dtype == pl.Datetime:
            # Datetime type - convert to date for comparison
            filtered_df = df.filter(
                (pl.col(date_col).cast(pl.Date) >= start_date_date) & 
                (pl.col(date_col).cast(pl.Date) < end_date_date)
            )
            print(f"   ✅ Filtered to {len(filtered_df):,} claims (Datetime type)")
        elif date_dtype == pl.Utf8 or date_dtype == pl.String:
            # String type - parse and compare
            start_date_str = start_date_date.strftime("%Y-%m-%d")
            end_date_str = end_date_date.strftime("%Y-%m-%d")
            filtered_df = df.filter(
                (pl.col(date_col) >= start_date_str) & 
                (pl.col(date_col) < end_date_str)
            )
            print(f"   ✅ Filtered to {len(filtered_df):,} claims (String type)")
        else:
            # Unknown type - try parsing
            filtered_df = df.with_columns([
                pl.col(date_col).str.strptime(pl.Date, format="%Y-%m-%d", strict=False).alias("_date")
            ]).filter(
                (pl.col("_date") >= start_date_date) & 
                (pl.col("_date") < end_date_date)
            ).drop("_date")
            print(f"   ✅ Filtered to {len(filtered_df):,} claims (parsed)")
    except Exception as e:
        print(f"   ⚠️  Date filtering error: {e}")
        print(f"   Trying fallback: using all claims in date range")
        # Last resort: use string comparison
        try:
            start_date_str = start_date_date.strftime("%Y-%m-%d")
            end_date_str = end_date_date.strftime("%Y-%m-%d")
            filtered_df = df.filter(
                (pl.col(date_col) >= start_date_str) & 
                (pl.col(date_col) < end_date_str)
            )
            print(f"   ✅ Filtered to {len(filtered_df):,} claims (fallback string)")
        except Exception as e2:
            print(f"   ❌ All date filtering failed: {e2}")
            print(f"   Using all claims (no date filter)")
            filtered_df = df
    
    if filtered_df.is_empty():
        return {
            "utilization_per_1k": 0.0,
            "allowed_pmpm": 0.0,
            "paid_pmpm": 0.0,
            "total_claims": 0,
            "total_allowed": 0.0,
            "total_paid": 0.0,
            "member_months": 0,
        }
    
    # Get unique members
    member_count = filtered_df["member_id"].n_unique() if "member_id" in filtered_df.columns else 1
    
    # Calculate months in period
    months = (end_date - start_date).days / 30.0
    member_months = member_count * max(1.0, months)
    
    # Get cost columns
    allowed_col = "allowed_amount" if "allowed_amount" in filtered_df.columns else None
    paid_col = "paid_amount" if "paid_amount" in filtered_df.columns else None
    
    total_claims = len(filtered_df)
    total_allowed = float(filtered_df[allowed_col].sum()) if allowed_col else 0.0
    total_paid = float(filtered_df[paid_col].sum()) if paid_col else 0.0
    
    return {
        "utilization_per_1k": (total_claims / member_count * 1000) if member_count > 0 else 0.0,
        "allowed_pmpm": (total_allowed / member_months) if member_months > 0 else 0.0,
        "paid_pmpm": (total_paid / member_months) if member_months > 0 else 0.0,
        "total_claims": total_claims,
        "total_allowed": total_allowed,
        "total_paid": total_paid,
        "member_months": member_months,
    }


def create_observation_data(policy_id: str, policy_name: str, pre_metrics: dict, post_metrics: dict, effective_date=None):
    """Create observation data structure"""
    # Use provided effective date or default
    if effective_date is None:
        effective_date = POLICY_EFFECTIVE_DATE.date() if isinstance(POLICY_EFFECTIVE_DATE, datetime) else POLICY_EFFECTIVE_DATE
    elif isinstance(effective_date, datetime):
        effective_date = effective_date.date()
    
    # Calculate changes
    utilization_change = post_metrics["utilization_per_1k"] - pre_metrics["utilization_per_1k"]
    utilization_change_pct = (utilization_change / pre_metrics["utilization_per_1k"] * 100) if pre_metrics["utilization_per_1k"] > 0 else 0.0
    
    cost_change_pmpm = post_metrics["allowed_pmpm"] - pre_metrics["allowed_pmpm"]
    cost_change_pct = (cost_change_pmpm / pre_metrics["allowed_pmpm"] * 100) if pre_metrics["allowed_pmpm"] > 0 else 0.0
    
    # Create observation
    observation = {
        "tenant_id": str(DEFAULT_TENANT_ID),
        "policy_id": policy_id,
        "observation_type": "PERIODIC",
        "observation_period_start": effective_date.isoformat() if isinstance(effective_date, (datetime, type)) else str(effective_date),
        "observation_period_end": (effective_date + timedelta(days=30)).isoformat() if isinstance(effective_date, (datetime, type)) else str(effective_date + timedelta(days=30)),
        "computed_at": datetime.now(UTC).isoformat(),
        "metrics": {
            "utilization_per_1k": post_metrics["utilization_per_1k"],
            "cost_pmpm": post_metrics["allowed_pmpm"],
            "cost_per_member": post_metrics["allowed_pmpm"],
            "total_claims": post_metrics["total_claims"],
            "observed_effect_size": utilization_change / 100.0 if pre_metrics["utilization_per_1k"] > 0 else 0.0,
            "observed_percent_change": utilization_change_pct,
        },
        "comparisons": {
            "vs_baseline": {
                "baseline_utilization_per_1k": pre_metrics["utilization_per_1k"],
                "observed_utilization_per_1k": post_metrics["utilization_per_1k"],
                "utilization_change": utilization_change,
                "utilization_change_pct": utilization_change_pct,
                "baseline_cost_pmpm": pre_metrics["allowed_pmpm"],
                "observed_cost_pmpm": post_metrics["allowed_pmpm"],
                "cost_change_pmpm": cost_change_pmpm,
                "cost_change_pct": cost_change_pct,
            },
            "vs_predicted": {
                # Will be populated if predicted impact exists
            }
        },
        "behavioral_explanation": {
            "summary": f"Observed {abs(utilization_change_pct):.1f}% {'reduction' if utilization_change_pct < 0 else 'increase'} in utilization",
            "percent_change": utilization_change_pct,
            "effect_size": utilization_change / 100.0 if pre_metrics["utilization_per_1k"] > 0 else 0.0,
        }
    }
    
    return observation


def get_policies_from_database():
    """Get policies from database directly with their effective dates"""
    try:
        from uepi_api.database import SessionLocal
        from uepi_api.models.policy import Policy, PolicyVersion
        
        db = SessionLocal()
        try:
            policies = db.query(Policy).filter(
                Policy.tenant_id == DEFAULT_TENANT_ID
            ).limit(100).all()
            
            result = []
            for policy in policies:
                # Get the latest policy version to get effective date
                version = db.query(PolicyVersion).filter(
                    PolicyVersion.policy_id == policy.id,
                    PolicyVersion.tenant_id == DEFAULT_TENANT_ID
                ).order_by(PolicyVersion.version_number.desc()).first()
                
                effective_date = None
                if version and version.effective_start_date:
                    effective_date = version.effective_start_date.date() if hasattr(version.effective_start_date, 'date') else version.effective_start_date
                
                result.append({
                    "id": str(policy.id),
                    "name": policy.name,
                    "effective_date": effective_date,
                })
            return result
        except Exception as e:
            print(f"⚠️  Database error: {e}")
            return []
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️  Could not connect to database: {e}")
        return []


def get_policies_from_files():
    """Get policies from data files or create sample list"""
    # Try database first
    db_policies = get_policies_from_database()
    if db_policies:
        return db_policies
    
    # Try to find policy files
    policies_dir = project_root / "apps" / "api" / "src" / "data" / "policies"
    if policies_dir.exists():
        policy_files = list(policies_dir.glob("*.json"))
        if policy_files:
            policies = []
            for pf in policy_files[:10]:  # Limit to 10
                try:
                    with open(pf) as f:
                        policy = json.load(f)
                        policies.append({
                            "id": policy.get("id") or policy.get("policy_id") or str(UUID(int=hash(pf.name) % (2**128))),
                            "name": policy.get("name") or policy.get("policy_name") or pf.stem,
                        })
                except:
                    pass
            if policies:
                return policies
    
    # Fallback: create sample policies based on common policy types
    # Use default effective date for fallback policies
    default_eff_date = POLICY_EFFECTIVE_DATE.date() if isinstance(POLICY_EFFECTIVE_DATE, datetime) else POLICY_EFFECTIVE_DATE
    return [
        {"id": str(UUID("6744b13c-0000-0000-0000-000000000001")), "name": "Outpatient MRI Prior Authorization - Enhanced", "effective_date": default_eff_date},
        {"id": str(UUID("ae6ce8f3-0000-0000-0000-000000000002")), "name": "Outpatient MRI Prior Authorization - Standard", "effective_date": default_eff_date},
        {"id": str(UUID("a846516b-0000-0000-0000-000000000003")), "name": "Outpatient MRI Prior Authorization", "effective_date": default_eff_date},
    ]


def save_observation(observation: dict):
    """Save observation to file"""
    obs_dir = project_root / "apps" / "api" / "src" / "data" / "observations" / str(DEFAULT_TENANT_ID)
    obs_dir.mkdir(parents=True, exist_ok=True)
    
    obs_id = observation.get("observation_id") or str(UUID(int=hash(observation["policy_id"]) % (2**128)))
    obs_file = obs_dir / f"{obs_id}.json"
    
    observation["observation_id"] = obs_id
    
    with open(obs_file, 'w') as f:
        json.dump(observation, f, indent=2, default=str)
    
    return obs_file


def main():
    print("="*80)
    print("CREATE OBSERVATIONS DIRECTLY FROM CLAIMS DATA")
    print("="*80)
    print("This script bypasses the API and creates observations directly from claims data.")
    print()
    
    # Load claims
    print("Step 1: Loading claims data...")
    claims_df = load_claims_data()
    if claims_df is None:
        return 1
    
    # Check actual date range in data
    date_col = "service_from_date"
    if date_col in claims_df.columns:
        try:
            min_date = claims_df[date_col].min()
            max_date = claims_df[date_col].max()
            print(f"   📅 Date range in data: {min_date} to {max_date}")
            
            # Use actual data range for periods
            if isinstance(min_date, str):
                min_date = datetime.fromisoformat(min_date.split()[0]).date()
            if isinstance(max_date, str):
                max_date = datetime.fromisoformat(max_date.split()[0]).date()
            
            # Adjust policy effective date to be within data range
            policy_eff_date = POLICY_EFFECTIVE_DATE.date() if isinstance(POLICY_EFFECTIVE_DATE, datetime) else POLICY_EFFECTIVE_DATE
            if policy_eff_date > max_date:
                print(f"   ⚠️  Policy effective date ({policy_eff_date}) is after data range")
                print(f"   📅 Using {max_date} as policy effective date")
                effective_date = max_date
            elif policy_eff_date < min_date:
                print(f"   ⚠️  Policy effective date ({policy_eff_date}) is before data range")
                print(f"   📅 Using {min_date} as policy effective date")
                effective_date = min_date
            else:
                effective_date = policy_eff_date
        except Exception as e:
            print(f"   ⚠️  Could not determine date range: {e}")
            effective_date = POLICY_EFFECTIVE_DATE.date() if isinstance(POLICY_EFFECTIVE_DATE, datetime) else POLICY_EFFECTIVE_DATE
    else:
        effective_date = POLICY_EFFECTIVE_DATE.date() if isinstance(POLICY_EFFECTIVE_DATE, datetime) else POLICY_EFFECTIVE_DATE
    
    # Get policies
    print("\nStep 2: Getting policies...")
    policies = get_policies_from_files()
    print(f"✅ Found {len(policies)} policies to process")
    
    if len(policies) == 0:
        print("\n⚠️  No policies found! Creating observations for all policies anyway...")
        print("   (Using fallback policy IDs)")
        default_eff_date = effective_date if 'effective_date' in locals() else (POLICY_EFFECTIVE_DATE.date() if isinstance(POLICY_EFFECTIVE_DATE, datetime) else POLICY_EFFECTIVE_DATE)
        policies = [
            {"id": str(UUID("6744b13c-0000-0000-0000-000000000001")), "name": "Sample Policy 1", "effective_date": default_eff_date},
            {"id": str(UUID("ae6ce8f3-0000-0000-0000-000000000002")), "name": "Sample Policy 2", "effective_date": default_eff_date},
            {"id": str(UUID("a846516b-0000-0000-0000-000000000003")), "name": "Sample Policy 3", "effective_date": default_eff_date},
        ]
    
    print(f"\nStep 3: Computing metrics for each policy...")
    
    # Create observations for each policy (each with its own effective date)
    print(f"\nStep 4: Creating observations for {len(policies)} policies...")
    successful = 0
    failed = 0
    
    for policy in policies:
        policy_id = policy["id"]
        policy_name = policy["name"]
        policy_effective_date = policy.get("effective_date")
        
        # Use policy's effective date if available, otherwise use default
        if policy_effective_date:
            if isinstance(policy_effective_date, str):
                policy_effective_date = datetime.fromisoformat(policy_effective_date.split()[0]).date()
            elif isinstance(policy_effective_date, datetime):
                policy_effective_date = policy_effective_date.date()
            effective_date = policy_effective_date
            print(f"\n  📋 Policy: {policy_name}")
            print(f"      Effective date: {effective_date}")
        else:
            effective_date = effective_date if 'effective_date' in locals() else (POLICY_EFFECTIVE_DATE.date() if isinstance(POLICY_EFFECTIVE_DATE, datetime) else POLICY_EFFECTIVE_DATE)
            print(f"\n  📋 Policy: {policy_name}")
            print(f"      Effective date: {effective_date} (default - no policy date found)")
        
        # Calculate date ranges for this policy
        # Use 6 months pre and 1 month post, but adjust to fit data range
        pre_start = effective_date - timedelta(days=180)  # 6 months pre
        pre_end = effective_date
        post_start = effective_date
        post_end = min(effective_date + timedelta(days=30), max_date if 'max_date' in locals() else effective_date + timedelta(days=30))  # 1 month post
        
        # Ensure dates are within data range
        if 'min_date' in locals() and pre_start < min_date:
            pre_start = min_date
        if 'max_date' in locals() and post_end > max_date:
            post_end = max_date
        
        print(f"      Pre-period: {pre_start} to {pre_end}")
        print(f"      Post-period: {post_start} to {post_end}")
        
        try:
            # Compute baseline metrics for this policy's period
            print(f"      Computing pre-policy (baseline) metrics...")
            pre_metrics = compute_metrics_from_claims(claims_df, datetime.combine(pre_start, datetime.min.time()), datetime.combine(pre_end, datetime.min.time()))
            print(f"      ✅ Baseline: Utilization={pre_metrics['utilization_per_1k']:.2f}, Cost PMPM=${pre_metrics['allowed_pmpm']:.2f}")
            
            # Compute post-policy metrics for this policy's period
            print(f"      Computing post-policy (observed) metrics...")
            post_metrics = compute_metrics_from_claims(claims_df, datetime.combine(post_start, datetime.min.time()), datetime.combine(post_end, datetime.min.time()))
            print(f"      ✅ Observed: Utilization={post_metrics['utilization_per_1k']:.2f}, Cost PMPM=${post_metrics['allowed_pmpm']:.2f}")
            
            # Create observation with policy-specific effective date
            observation = create_observation_data(policy_id, policy_name, pre_metrics, post_metrics, effective_date)
            obs_file = save_observation(observation)
            
            print(f"    ✅ Observation created: {obs_file.name}")
            print(f"       Utilization: {observation['metrics']['utilization_per_1k']:.2f}")
            print(f"       Cost PMPM: ${observation['metrics']['cost_pmpm']:.2f}")
            print(f"       Change: {observation['comparisons']['vs_baseline']['utilization_change_pct']:.1f}%")
            
            successful += 1
        except Exception as e:
            print(f"    ❌ Error creating observation: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Successful observations: {successful}")
    print(f"❌ Failed observations: {failed}")
    
    if successful > 0:
        print(f"\n✅ {successful} observations created with actual data!")
        print(f"   Location: apps/api/src/data/observations/{DEFAULT_TENANT_ID}/")
        print(f"\n   Next steps:")
        print(f"   1. These observations have actual observed values from claims data")
        print(f"   2. You can import them into the database via API when database is working")
        print(f"   3. Or the API can read them from files if file storage is enabled")
    else:
        print("\n⚠️  No observations were created. Check errors above.")
    
    return 0 if successful > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
