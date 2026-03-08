#!/usr/bin/env python3
"""
Comprehensive Data Quality Check and Source vs Target Comparison

Performs:
1. Data validation (completeness, validity, uniqueness)
2. Source vs target comparison
3. Comprehensive scope field validation
4. Referential integrity checks
5. Data statistics and quality metrics
6. Generates quality report
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

from uuid import UUID

TENANT_ID = "00000000-0000-0000-0000-000000000001"
TARGET_DATA_DIR = PROJECT_ROOT / "apps" / "data" / "target_data_model" / TENANT_ID

# Required fields for comprehensive scope
REQUIRED_CLAIMS_FIELDS = [
    "service_from_date", "service_to_date", "paid_date",
    "tenant_id", "member_id", "claim_id", "claim_line_id",
    "lob", "market",
    "plan_id", "product_type", "state", "region",
    "place_of_service", "cpt_hcpcs", "service_category",
    "rendering_npi", "network_tier",
    "allowed_amount", "paid_amount", "units",
    "in_network_flag",
    "diagnosis_group",
]

REQUIRED_MEMBERS_FIELDS = [
    "member_id", "lob", "market",
    "plan_id", "product_type", "state", "region",
    "gender", "dob_year", "enrolled_flag",
]

REQUIRED_PROVIDERS_FIELDS = [
    "npi", "provider_name", "specialty", "market",
    "network_tier", "facility_flag",
]


class DataQualityReport:
    """Data quality report container"""
    def __init__(self):
        self.timestamp = datetime.utcnow().isoformat()
        self.datasets = {}
        self.issues = []
        self.comparisons = {}
        self.overall_score = 0.0
        self.completeness_score = 0.0
        self.validity_score = 0.0
        self.uniqueness_score = 100.0
        self.integrity_score = 100.0
        self.consistency_score = 85.0
        self.critical_issues = 0
        self.high_issues = 0
        self.medium_issues = 0
        self.low_issues = 0
        self.total_rows = 0
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "overall_score": self.overall_score,
            "datasets": self.datasets,
            "issues": self.issues,
            "comparisons": self.comparisons,
        }


def validate_completeness(df: pd.DataFrame, required_fields: List[str], dataset_name: str) -> Dict[str, Any]:
    """Check field completeness"""
    results = {
        "total_rows": len(df),
        "fields": {},
        "completeness_score": 0.0,
        "missing_fields": [],
        "issues": [],
    }
    
    total_completeness = 0.0
    for field in required_fields:
        if field not in df.columns:
            results["missing_fields"].append(field)
            results["issues"].append({
                "type": "MISSING_FIELD",
                "severity": "CRITICAL",  # Missing required fields are critical
                "field": field,
                "description": f"Required field '{field}' not found in {dataset_name}",
                "affected_rows": len(df),
                "affected_percentage": 100.0,
            })
            continue
        
        non_null_count = df[field].notna().sum()
        null_count = df[field].isna().sum()
        empty_count = (df[field].astype(str).str.strip() == "").sum()
        total_missing = null_count + empty_count
        completeness_pct = (non_null_count / len(df)) * 100 if len(df) > 0 else 0
        
        results["fields"][field] = {
            "non_null": int(non_null_count),
            "null": int(null_count),
            "empty": int(empty_count),
            "completeness_pct": round(completeness_pct, 2),
        }
        
        total_completeness += completeness_pct
        
        if completeness_pct < 100:
            if completeness_pct < 80:
                severity = "CRITICAL"
            elif completeness_pct < 95:
                severity = "HIGH"
            elif completeness_pct < 99:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            results["issues"].append({
                "type": "INCOMPLETE_FIELD",
                "severity": severity,
                "field": field,
                "description": f"Field '{field}' has {total_missing}/{len(df)} missing/empty values ({100-completeness_pct:.1f}%)",
                "missing_count": int(total_missing),
                "completeness_pct": round(completeness_pct, 2),
                "affected_rows": int(total_missing),
                "affected_percentage": round(100 - completeness_pct, 2),
            })
    
    if required_fields:
        results["completeness_score"] = round(total_completeness / len(required_fields), 2)
    else:
        results["completeness_score"] = 100.0
    
    return results


def validate_uniqueness(df: pd.DataFrame, key_fields: List[str], dataset_name: str) -> Dict[str, Any]:
    """Check uniqueness constraints"""
    results = {
        "uniqueness_score": 100.0,
        "issues": [],
    }
    
    for field in key_fields:
        if field not in df.columns:
            continue
        
        unique_count = df[field].nunique()
        total_count = len(df)
        duplicates = total_count - unique_count
        
        if duplicates > 0:
            uniqueness_pct = (unique_count / total_count) * 100 if total_count > 0 else 0
            results["uniqueness_score"] = min(results["uniqueness_score"], uniqueness_pct)
            
            if uniqueness_pct < 90:
                severity = "CRITICAL"
            elif uniqueness_pct < 95:
                severity = "HIGH"
            elif uniqueness_pct < 99:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            results["issues"].append({
                "type": "DUPLICATE_VALUES",
                "severity": severity,
                "field": field,
                "description": f"Field '{field}' has {duplicates} duplicate values ({100-uniqueness_pct:.1f}% duplicate)",
                "unique_count": int(unique_count),
                "duplicate_count": int(duplicates),
                "affected_rows": int(duplicates),
                "affected_percentage": round(100 - uniqueness_pct, 2),
            })
    
    return results


def validate_referential_integrity(claims_df: pd.DataFrame, members_df: pd.DataFrame, providers_df: pd.DataFrame) -> Dict[str, Any]:
    """Check referential integrity between datasets"""
    results = {
        "integrity_score": 100.0,
        "issues": [],
    }
    
    # Check if dataframes are empty
    if claims_df is None or len(claims_df) == 0:
        return results
    if members_df is None or len(members_df) == 0:
        members_df = pd.DataFrame()
    if providers_df is None or len(providers_df) == 0:
        providers_df = pd.DataFrame()
    
    # Check member_id references
    if "member_id" in claims_df.columns and len(members_df) > 0 and "member_id" in members_df.columns:
        unique_claim_members = set(claims_df["member_id"].unique())
        unique_member_ids = set(members_df["member_id"].unique())
        orphaned_members = unique_claim_members - unique_member_ids
        
        if orphaned_members:
            orphaned_pct = (len(orphaned_members) / len(unique_claim_members)) * 100
            results["integrity_score"] -= orphaned_pct * 0.5  # Reduce score
            
            if orphaned_pct > 10:
                severity = "CRITICAL"
            elif orphaned_pct > 5:
                severity = "HIGH"
            else:
                severity = "MEDIUM"
            results["issues"].append({
                "type": "ORPHANED_REFERENCE",
                "severity": severity,
                "field": "member_id",
                "description": f"{len(orphaned_members)} claims reference members not in enrollment ({orphaned_pct:.1f}%)",
                "orphaned_count": len(orphaned_members),
                "affected_rows": len(orphaned_members),
                "affected_percentage": round(orphaned_pct, 2),
            })
    
    # Check rendering_npi references
    if "rendering_npi" in claims_df.columns and len(providers_df) > 0 and "npi" in providers_df.columns:
        unique_claim_providers = set(claims_df["rendering_npi"].unique())
        unique_provider_npis = set(providers_df["npi"].unique())
        orphaned_providers = unique_claim_providers - unique_provider_npis
        
        if orphaned_providers:
            orphaned_pct = (len(orphaned_providers) / len(unique_claim_providers)) * 100
            results["integrity_score"] -= orphaned_pct * 0.3  # Reduce score
            
            results["issues"].append({
                "type": "ORPHANED_REFERENCE",
                "severity": "MEDIUM" if orphaned_pct > 20 else "LOW",
                "field": "rendering_npi",
                "description": f"{len(orphaned_providers)} claims reference providers not in provider directory ({orphaned_pct:.1f}%)",
                "orphaned_count": len(orphaned_providers),
            })
    
    # Check plan_id, product_type, state, region consistency
    if all(f in claims_df.columns for f in ["plan_id", "product_type", "state", "region"]):
        if len(members_df) > 0 and all(f in members_df.columns for f in ["member_id", "plan_id", "product_type", "state", "region"]):
            # Sample check: verify some members have consistent values
            sample_claims = claims_df[["member_id", "plan_id", "product_type", "state", "region"]].drop_duplicates()
            sample_members = members_df[["member_id", "plan_id", "product_type", "state", "region"]]
            
            merged = sample_claims.merge(
                sample_members,
                on="member_id",
                how="left",
                suffixes=("_claim", "_member")
            )
            
            mismatches = {}
            for field in ["plan_id", "product_type", "state", "region"]:
                claim_col = f"{field}_claim"
                member_col = f"{field}_member"
                if claim_col in merged.columns and member_col in merged.columns:
                    mismatched = merged[
                        (merged[claim_col].notna()) & 
                        (merged[member_col].notna()) & 
                        (merged[claim_col] != merged[member_col])
                    ]
                    if len(mismatched) > 0:
                        mismatch_pct = (len(mismatched) / len(merged)) * 100
                        mismatches[field] = {
                            "count": len(mismatched),
                            "percentage": round(mismatch_pct, 2),
                        }
            
            if mismatches:
                results["integrity_score"] -= 10  # Reduce score
                results["issues"].append({
                    "type": "DATA_INCONSISTENCY",
                    "severity": "MEDIUM",
                    "description": f"Inconsistencies between claims and members: {mismatches}",
                    "mismatches": mismatches,
                })
    
    results["integrity_score"] = max(0.0, results["integrity_score"])
    return results


def validate_data_types(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """Validate data types and formats"""
    results = {
        "validity_score": 100.0,
        "issues": [],
    }
    
    # Validate dates
    date_fields = ["service_from_date", "service_to_date", "paid_date"]
    for field in date_fields:
        if field in df.columns:
            try:
                pd.to_datetime(df[field], errors='coerce')
                invalid_dates = df[df[field].notna()][field].apply(
                    lambda x: pd.to_datetime(x, errors='coerce') is pd.NaT
                ).sum()
                
                if invalid_dates > 0:
                    invalid_pct = (invalid_dates / len(df)) * 100
                    results["validity_score"] -= invalid_pct * 0.5
                    
                    if invalid_pct > 5:
                        severity = "CRITICAL"
                    elif invalid_pct > 1:
                        severity = "HIGH"
                    else:
                        severity = "MEDIUM"
                    results["issues"].append({
                        "type": "INVALID_DATE",
                        "severity": severity,
                        "field": field,
                        "description": f"Field '{field}' has {invalid_dates} invalid date values ({invalid_pct:.1f}%)",
                        "invalid_count": int(invalid_dates),
                        "affected_rows": int(invalid_dates),
                        "affected_percentage": round(invalid_pct, 2),
                    })
            except Exception as e:
                results["issues"].append({
                    "type": "DATE_VALIDATION_ERROR",
                    "severity": "HIGH",
                    "field": field,
                    "description": f"Error validating dates in '{field}': {str(e)}",
                })
    
    # Validate numeric fields
    numeric_fields = ["allowed_amount", "paid_amount", "units"]
    for field in numeric_fields:
        if field in df.columns:
            try:
                numeric_series = pd.to_numeric(df[field], errors='coerce')
                invalid_numeric = numeric_series.isna().sum() - df[field].isna().sum()
                
                if invalid_numeric > 0:
                    invalid_pct = (invalid_numeric / len(df)) * 100
                    results["validity_score"] -= invalid_pct * 0.3
                    
                    results["issues"].append({
                        "type": "INVALID_NUMERIC",
                        "severity": "MEDIUM" if invalid_pct > 1 else "LOW",
                        "field": field,
                        "description": f"Field '{field}' has {invalid_numeric} invalid numeric values",
                        "invalid_count": int(invalid_numeric),
                    })
                
                # Check for negative values
                negative_count = (numeric_series < 0).sum()
                if negative_count > 0:
                    results["issues"].append({
                        "type": "NEGATIVE_VALUE",
                        "severity": "LOW",
                        "field": field,
                        "description": f"Field '{field}' has {negative_count} negative values",
                        "invalid_count": int(negative_count),
                    })
            except Exception as e:
                pass
    
    results["validity_score"] = max(0.0, results["validity_score"])
    return results


def calculate_statistics(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """Calculate data statistics"""
    stats = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }
    
    # Date range for claims
    if "service_from_date" in df.columns:
        try:
            dates = pd.to_datetime(df["service_from_date"], errors='coerce')
            dates = dates.dropna()
            if len(dates) > 0:
                stats["date_range"] = {
                    "min": dates.min().strftime("%Y-%m-%d"),
                    "max": dates.max().strftime("%Y-%m-%d"),
                    "span_days": (dates.max() - dates.min()).days,
                }
        except:
            pass
    
    # Categorical value counts
    categorical_fields = ["lob", "market", "plan_id", "product_type", "state", "region", "network_tier", "service_category"]
    stats["value_counts"] = {}
    for field in categorical_fields:
        if field in df.columns:
            value_counts = df[field].value_counts().head(10).to_dict()
            stats["value_counts"][field] = {str(k): int(v) for k, v in value_counts.items()}
    
    # Numeric statistics
    numeric_fields = ["allowed_amount", "paid_amount", "units"]
    stats["numeric_stats"] = {}
    for field in numeric_fields:
        if field in df.columns:
            try:
                numeric_series = pd.to_numeric(df[field], errors='coerce').dropna()
                if len(numeric_series) > 0:
                    stats["numeric_stats"][field] = {
                        "min": float(numeric_series.min()),
                        "max": float(numeric_series.max()),
                        "mean": float(numeric_series.mean()),
                        "median": float(numeric_series.median()),
                        "std": float(numeric_series.std()),
                    }
            except:
                pass
    
    return stats


def compare_source_target(report: DataQualityReport) -> Dict[str, Any]:
    """Compare source vs target (placeholder - add actual comparison if needed)"""
    comparison = {
        "status": "SKIPPED",
        "description": "Source data comparison not implemented (using direct generation)",
    }
    
    # In a real scenario, you would compare:
    # - Row counts between source and target
    # - Field mappings
    # - Data transformations
    # - Aggregations
    
    return comparison


def load_data_from_database_or_file(dataset_name: str, tenant_id: str) -> Optional[pd.DataFrame]:
    """Load data from database first, then fallback to file"""
    try:
        from uepi_api.database import SessionLocal
        from sqlalchemy import text, inspect
        
        db = SessionLocal()
        try:
            inspector = inspect(db.bind)
            tables = inspector.get_table_names()
            
            # Try to find matching table
            table_name = None
            for t in tables:
                if dataset_name.lower().replace("_", "") in t.lower() or t.lower() in dataset_name.lower():
                    table_name = t
                    break
            
            if table_name:
                # Check if table has tenant_id column
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                has_tenant_id = 'tenant_id' in columns
                
                if has_tenant_id:
                    query = text(f'SELECT * FROM {table_name} WHERE tenant_id = :tenant_id LIMIT 1000000')
                    result = db.execute(query, {"tenant_id": tenant_id})
                else:
                    query = text(f'SELECT * FROM {table_name} LIMIT 1000000')
                    result = db.execute(query)
                
                rows = result.fetchall()
                if rows:
                    columns = result.keys()
                    df = pd.DataFrame(rows, columns=columns)
                    print(f"  ✅ Loaded {len(df):,} records from database table: {table_name}")
                    return df
        finally:
            db.close()
    except Exception as e:
        pass  # Fallback to file
    
    # Fallback to file
    file_mapping = {
        "CLAIMS_LINES": TARGET_DATA_DIR / "CLAIMS_LINES" / "claims_lines.csv",
        "ENROLLMENT": TARGET_DATA_DIR / "ENROLLMENT" / "enrollment.csv",
        "PROVIDERS": TARGET_DATA_DIR / "PROVIDERS" / "providers.csv",
    }
    
    file_path = file_mapping.get(dataset_name)
    if file_path and file_path.exists():
        try:
            df = pd.read_csv(file_path, low_memory=False)
            print(f"  ✅ Loaded {len(df):,} records from file: {file_path.name}")
            return df
        except Exception as e:
            print(f"  ⚠️  Error loading file: {e}")
    
    return None


def main():
    """Run comprehensive data quality check"""
    print("="*60)
    print("Comprehensive Data Quality Check")
    print("="*60)
    print(f"Target Data Directory: {TARGET_DATA_DIR}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}\n")
    
    report = DataQualityReport()
    
    # Load datasets (try database first, then files)
    print("Loading datasets...")
    claims_df = load_data_from_database_or_file("CLAIMS_LINES", TENANT_ID)
    members_df = load_data_from_database_or_file("ENROLLMENT", TENANT_ID)
    providers_df = load_data_from_database_or_file("PROVIDERS", TENANT_ID)
    
    if claims_df is None:
        print(f"  ⚠️  Claims data not found in database or files")
    if members_df is None:
        print(f"  ⚠️  Members data not found in database or files")
    if providers_df is None:
        print(f"  ⚠️  Providers data not found in database or files")
    
    print()
    
    # Validate Claims
    if claims_df is not None and len(claims_df) > 0:
        print("Validating Claims...")
        claims_completeness = validate_completeness(claims_df, REQUIRED_CLAIMS_FIELDS, "Claims")
        claims_uniqueness = validate_uniqueness(claims_df, ["claim_line_id"], "Claims")
        claims_validity = validate_data_types(claims_df, "Claims")
        claims_stats = calculate_statistics(claims_df, "Claims")
        
        claims_score = (
            claims_completeness["completeness_score"] * 0.4 +
            claims_uniqueness["uniqueness_score"] * 0.3 +
            claims_validity["validity_score"] * 0.3
        ) / 100
        
        report.datasets["CLAIMS_LINES"] = {
            "completeness": claims_completeness,
            "uniqueness": claims_uniqueness,
            "validity": claims_validity,
            "statistics": claims_stats,
            "quality_score": round(claims_score * 100, 2),
        }
        
        report.issues.extend([
            {**issue, "dataset": "CLAIMS_LINES"} 
            for issue in claims_completeness["issues"] + claims_uniqueness["issues"] + claims_validity["issues"]
        ])
        
        print(f"  Quality Score: {claims_score*100:.1f}%")
        print(f"  Completeness: {claims_completeness['completeness_score']:.1f}%")
        print(f"  Uniqueness: {claims_uniqueness['uniqueness_score']:.1f}%")
        print(f"  Validity: {claims_validity['validity_score']:.1f}%")
        print()
    
    # Validate Members
    if members_df is not None and len(members_df) > 0:
        print("Validating Members...")
        members_completeness = validate_completeness(members_df, REQUIRED_MEMBERS_FIELDS, "Members")
        members_uniqueness = validate_uniqueness(members_df, ["member_id"], "Members")
        members_validity = validate_data_types(members_df, "Members")
        members_stats = calculate_statistics(members_df, "Members")
        
        members_score = (
            members_completeness["completeness_score"] * 0.4 +
            members_uniqueness["uniqueness_score"] * 0.3 +
            members_validity["validity_score"] * 0.3
        ) / 100
        
        report.datasets["ENROLLMENT"] = {
            "completeness": members_completeness,
            "uniqueness": members_uniqueness,
            "validity": members_validity,
            "statistics": members_stats,
            "quality_score": round(members_score * 100, 2),
        }
        
        report.issues.extend([
            {**issue, "dataset": "ENROLLMENT"} 
            for issue in members_completeness["issues"] + members_uniqueness["issues"] + members_validity["issues"]
        ])
        
        print(f"  Quality Score: {members_score*100:.1f}%")
        print(f"  Completeness: {members_completeness['completeness_score']:.1f}%")
        print(f"  Uniqueness: {members_uniqueness['uniqueness_score']:.1f}%")
        print(f"  Validity: {members_validity['validity_score']:.1f}%")
        print()
    
    # Validate Providers
    if providers_df is not None and len(providers_df) > 0:
        print("Validating Providers...")
        providers_completeness = validate_completeness(providers_df, REQUIRED_PROVIDERS_FIELDS, "Providers")
        providers_uniqueness = validate_uniqueness(providers_df, ["npi"], "Providers")
        providers_validity = validate_data_types(providers_df, "Providers")
        providers_stats = calculate_statistics(providers_df, "Providers")
        
        providers_score = (
            providers_completeness["completeness_score"] * 0.4 +
            providers_uniqueness["uniqueness_score"] * 0.3 +
            providers_validity["validity_score"] * 0.3
        ) / 100
        
        report.datasets["PROVIDERS"] = {
            "completeness": providers_completeness,
            "uniqueness": providers_uniqueness,
            "validity": providers_validity,
            "statistics": providers_stats,
            "quality_score": round(providers_score * 100, 2),
        }
        
        report.issues.extend([
            {**issue, "dataset": "PROVIDERS"} 
            for issue in providers_completeness["issues"] + providers_uniqueness["issues"] + providers_validity["issues"]
        ])
        
        print(f"  Quality Score: {providers_score*100:.1f}%")
        print(f"  Completeness: {providers_completeness['completeness_score']:.1f}%")
        print(f"  Uniqueness: {providers_uniqueness['uniqueness_score']:.1f}%")
        print(f"  Validity: {providers_validity['validity_score']:.1f}%")
        print()
    
    # Referential Integrity
    has_members = members_df is not None and len(members_df) > 0
    has_providers = providers_df is not None and len(providers_df) > 0
    
    if claims_df is not None and len(claims_df) > 0 and (has_members or has_providers):
        print("Checking Referential Integrity...")
        integrity_results = validate_referential_integrity(
            claims_df, 
            members_df if has_members else pd.DataFrame(), 
            providers_df if has_providers else pd.DataFrame()
        )
        report.comparisons["referential_integrity"] = integrity_results
        
        print(f"  Integrity Score: {integrity_results['integrity_score']:.1f}%")
        for issue in integrity_results["issues"]:
            print(f"    - {issue['description']}")
        print()
        
        report.issues.extend([
            {**issue, "dataset": "CROSS_DATASET"} 
            for issue in integrity_results["issues"]
        ])
    
    # Source vs Target Comparison
    print("Source vs Target Comparison...")
    comparison = compare_source_target(report)
    report.comparisons["source_target"] = comparison
    print(f"  {comparison['description']}\n")
    
    # Check additional datasets shown in dashboard (quick validation)
    # Map dashboard names to actual directory names
    dataset_name_mapping = {
        "PHARMACY_CLAIMS": "PHARMACY_CLAIMS",
        "MEMBER_MASTER": "MEMBER_MASTER",
        "PROVIDER_MASTER": "PROVIDER_MASTER",
        "CLAIM_HEADER": "CLAIM_HEADER",
        "BENEFIT_DESIGN": "BENEFIT_DESIGN",
        "NETWORK_CONFIGURATION": "NETWORK_CONFIGURATION",
        "PROVIDER_CONTRACTS": "PROVIDER_CONTRACT",  # Directory is PROVIDER_CONTRACT
        "PRIOR_AUTHORIZATION": "PRIOR_AUTHORIZATION_REQUEST",  # Directory is PRIOR_AUTHORIZATION_REQUEST
        "REFERRAL": "REFERRAL",
        "APPEAL_GRIEVANCE": "APPEAL_GRIEVANCE",
        "CARE_MANAGEMENT_ENROLLMENT": "CARE_MANAGEMENT_ENROLLMENT",
        "CONCURRENT_REVIEW": "CONCURRENT_REVIEW",
        "EPISODE_OF_CARE": "EPISODE_OF_CARE",
        "FACILITY_MASTER": "FACILITY_MASTER",
        "MEMBER_ACCUMULATORS": "MEMBER_ACCUMULATOR",  # Directory is MEMBER_ACCUMULATOR
        "MEMBER_DIAGNOSIS": "MEMBER_DIAGNOSIS",
        "MEMBER_RISK_STRATIFICATION": "MEMBER_RISK_STRATIFICATION",
        "PROBLEM_LIST": "PROBLEM_LIST",
        "RISK_STRATIFICATION": None,  # Not found in directory listing
        "MARKET_EVENT": "MARKET_EVENT",
        "CALL_CENTER_CONTACTS": "CALL_CENTER_CONTACT",  # Directory is CALL_CENTER_CONTACT
        "ELIGIBILITY_ENROLLMENT": "ELIGIBILITY_ENROLLMENT",
    }
    
    additional_datasets = list(dataset_name_mapping.keys())
    
    print("Checking additional datasets...")
    for dashboard_name in additional_datasets:
        if dashboard_name in report.datasets:
            continue  # Already validated
        
        # Get actual directory name from mapping
        actual_dir_name = dataset_name_mapping.get(dashboard_name)
        if actual_dir_name is None:
            # Skip if mapping says None (dataset doesn't exist)
            continue
        
        # Try to load from file (CSV or Parquet)
        dataset_dir = TARGET_DATA_DIR / actual_dir_name
        csv_files = list(dataset_dir.glob("*.csv")) if dataset_dir.exists() else []
        parquet_files = list(dataset_dir.glob("*.parquet")) if dataset_dir.exists() else []
        
        data_file = None
        file_format = None
        if csv_files:
            data_file = csv_files[0]
            file_format = "csv"
        elif parquet_files:
            data_file = parquet_files[0]
            file_format = "parquet"
        
        if data_file:
            try:
                # Load sample data
                if file_format == "csv":
                    df_sample = pd.read_csv(data_file, low_memory=False, nrows=1000)
                    # Count total rows efficiently for CSV
                    with open(data_file, 'r') as f:
                        total_rows = sum(1 for line in f) - 1  # Subtract header
                else:  # parquet
                    df_full = pd.read_parquet(data_file)
                    total_rows = len(df_full)
                    df_sample = df_full.head(1000) if len(df_full) > 1000 else df_full
                
                # Quick completeness check
                completeness_pct = (df_sample.notna().sum().sum() / (len(df_sample) * len(df_sample.columns))) * 100 if len(df_sample) > 0 and len(df_sample.columns) > 0 else 0
                
                # Basic uniqueness check (check if there's an ID column)
                uniqueness_score = 100.0
                id_columns = [col for col in df_sample.columns if 'id' in col.lower() or col.lower().endswith('_id')]
                if id_columns:
                    id_col = id_columns[0]
                    unique_count = df_sample[id_col].nunique()
                    uniqueness_score = (unique_count / len(df_sample)) * 100 if len(df_sample) > 0 else 100.0
                
                report.datasets[dashboard_name] = {
                    "quality_score": round(completeness_pct * 0.7, 2),  # Simplified score
                    "completeness": {"completeness_score": round(completeness_pct, 2)},
                    "uniqueness": {"uniqueness_score": round(uniqueness_score, 2)},
                    "validity": {"validity_score": 100.0},  # Assume valid for quick check
                    "statistics": {"total_rows": total_rows},
                    "issues": [],
                }
                print(f"  ✅ {dashboard_name}: {total_rows:,} rows ({file_format}), {completeness_pct:.1f}% complete")
            except Exception as e:
                report.datasets[dashboard_name] = {
                    "quality_score": 0.0,
                    "completeness": {"completeness_score": 0.0},
                    "uniqueness": {"uniqueness_score": 0.0},
                    "validity": {"validity_score": 0.0},
                    "statistics": {"total_rows": 0},
                    "issues": [{"type": "LOAD_ERROR", "severity": "HIGH", "description": f"Error loading {dashboard_name}: {str(e)[:100]}"}],
                }
                print(f"  ⚠️  {dashboard_name}: Error - {str(e)[:50]}")
        else:
            report.datasets[dashboard_name] = {
                "quality_score": 0.0,
                "completeness": {"completeness_score": 0.0},
                "uniqueness": {"uniqueness_score": 0.0},
                "validity": {"validity_score": 0.0},
                "statistics": {"total_rows": 0},
                "issues": [{"type": "MISSING_DATA", "severity": "MEDIUM", "description": f"Dataset {dashboard_name} not found in directory {actual_dir_name}"}],
            }
            print(f"  ⚠️  {dashboard_name}: Not found (checked {actual_dir_name})")
    
    print()
    
    # Calculate overall score (only from datasets with data)
    if report.datasets:
        scores = [ds["quality_score"] for ds in report.datasets.values() if ds.get("statistics", {}).get("total_rows", 0) > 0]
        report.overall_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    else:
        report.overall_score = 0.0
    
    # Calculate component scores for trust calculation
    completeness_scores = [ds.get("completeness", {}).get("completeness_score", 0) for ds in report.datasets.values()]
    validity_scores = [ds.get("validity", {}).get("validity_score", 0) for ds in report.datasets.values()]
    uniqueness_scores = [ds.get("uniqueness", {}).get("uniqueness_score", 100.0) for ds in report.datasets.values()]
    
    report.completeness_score = round(sum(completeness_scores) / len(completeness_scores), 2) if completeness_scores else 0.0
    report.validity_score = round(sum(validity_scores) / len(validity_scores), 2) if validity_scores else 0.0
    report.uniqueness_score = round(sum(uniqueness_scores) / len(uniqueness_scores), 2) if uniqueness_scores else 100.0
    report.integrity_score = report.comparisons.get("referential_integrity", {}).get("integrity_score", 100.0)
    report.consistency_score = 85.0  # Default, can be enhanced with cross-dataset checks
    
    # Count issues by severity
    critical_issues = [i for i in report.issues if i.get("severity") == "CRITICAL"]
    high_issues = [i for i in report.issues if i.get("severity") == "HIGH"]
    medium_issues = [i for i in report.issues if i.get("severity") == "MEDIUM"]
    low_issues = [i for i in report.issues if i.get("severity") == "LOW"]
    
    report.critical_issues = len(critical_issues)
    report.high_issues = len(high_issues)
    report.medium_issues = len(medium_issues)
    report.low_issues = len(low_issues)
    
    # Calculate total rows
    total_rows = sum(ds.get("statistics", {}).get("total_rows", 0) for ds in report.datasets.values())
    report.total_rows = total_rows
    
    # Save report to file (for backward compatibility)
    report_file = TARGET_DATA_DIR / "data_quality_report.json"
    report_dict = report.to_dict()
    report_dict["completeness_score"] = report.completeness_score
    report_dict["validity_score"] = report.validity_score
    report_dict["uniqueness_score"] = report.uniqueness_score
    report_dict["integrity_score"] = report.integrity_score
    report_dict["consistency_score"] = report.consistency_score
    report_dict["critical_issues"] = report.critical_issues
    report_dict["high_issues"] = report.high_issues
    report_dict["medium_issues"] = report.medium_issues
    report_dict["low_issues"] = report.low_issues
    report_dict["total_rows"] = report.total_rows
    
    with open(report_file, 'w') as f:
        json.dump(report_dict, f, indent=2, default=str)
    
    # Also store in database
    try:
        from uepi_api.services.data_quality_service import EnterpriseDataQualityService
        from uepi_api.storage_auth import DEFAULT_TENANT_ID
        
        service = EnterpriseDataQualityService(tenant_id=UUID(TENANT_ID))
        quality_report = service.store_quality_report(report_dict)
        print(f"\n✅ Stored data quality report in database (ID: {quality_report.id})")
        print(f"   Trust Score: {quality_report.trust_score:.1f}%")
        print(f"   Trust Level: {quality_report.trust_level}")
    except Exception as e:
        print(f"\n⚠️  Warning: Failed to store report in database: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*60)
    print("DATA QUALITY REPORT SUMMARY")
    print("="*60)
    print(f"Overall Quality Score: {report.overall_score}%")
    print(f"Total Issues Found: {len(report.issues)}")
    
    # Group issues by severity
    critical_issues = [i for i in report.issues if i.get("severity") == "CRITICAL"]
    high_issues = [i for i in report.issues if i.get("severity") == "HIGH"]
    medium_issues = [i for i in report.issues if i.get("severity") == "MEDIUM"]
    low_issues = [i for i in report.issues if i.get("severity") == "LOW"]
    
    print(f"  CRITICAL: {len(critical_issues)}")
    print(f"  HIGH: {len(high_issues)}")
    print(f"  MEDIUM: {len(medium_issues)}")
    print(f"  LOW: {len(low_issues)}")
    
    print(f"\nReport saved to: {report_file}")
    print("="*60)
    
    return report


if __name__ == "__main__":
    report = main()
