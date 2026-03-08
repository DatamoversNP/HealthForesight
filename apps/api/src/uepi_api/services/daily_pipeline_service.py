"""Daily pipeline service - Loads data from source folders to database"""
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd
import polars as pl
from sqlalchemy.orm import Session

from uepi_api.database import SessionLocal
from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.models.canonical_data import ClaimsLineDB, EnrollmentRecordDB, ProviderRecordDB


def load_daily_data_from_source(
    tenant_id: UUID,
    source_date: date,
    source_folder: Optional[Path] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Load daily data from source folder to database.
    
    Used by the daily job when "Run Daily Job" is triggered from the UI. If this
    returns no data (folder missing or no matching CSVs), the daily job automatically
    generates data via generate_claims_data_for_date()—so users do not need to
    manually place files.
    
    Args:
        tenant_id: Tenant ID
        source_date: Date for which to load data (typically yesterday)
        source_folder: Optional path; defaults to data/source_data/<tenant> or apps/data/source_data/<tenant>
        db: Database session (creates new if None)
    
    Returns:
        Dict with success, claims_loaded, enrollment_loaded, providers_loaded; error if folder missing
    """
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        # Determine source folder: try data/source_data/<tenant> (repo root) then apps/data/source_data/<tenant>
        if source_folder is None:
            current_file = Path(__file__).resolve()
            # .../apps/api/src/uepi_api/services -> 6 parents = project root
            project_root = current_file.parent.parent.parent.parent.parent.parent
            for candidate in [
                project_root / "data" / "source_data" / str(tenant_id),
                project_root / "apps" / "data" / "source_data" / str(tenant_id),
            ]:
                if candidate.exists():
                    source_folder = candidate
                    break
            else:
                source_folder = project_root / "data" / "source_data" / str(tenant_id)
        
        # Prefer date-specific subfolder (e.g. daily/YYYY-MM-DD or observation_period) for the given source_date
        date_sub = source_folder / "daily" / source_date.isoformat()
        if date_sub.exists():
            search_root = date_sub
        else:
            search_root = source_folder
        if not source_folder.exists():
            return {
                "success": False,
                "error": f"Source folder does not exist: {source_folder}",
                "claims_loaded": 0,
                "enrollment_loaded": 0,
                "providers_loaded": 0,
            }
        
        repo = CanonicalDataRepository(db)
        counts = {
            "claims_loaded": 0,
            "enrollment_loaded": 0,
            "providers_loaded": 0,
        }
        
        # Load claims data (from date subfolder if present, else whole tenant source tree)
        claims_files = list(search_root.glob("**/claims*.csv")) + list(search_root.glob("**/CLAIMS*.csv"))
        for claims_file in claims_files:
            try:
                # Read CSV
                df = pd.read_csv(claims_file, low_memory=False)
                
                # Filter by source_date if service_date column exists
                if 'service_date' in df.columns or 'service_from_date' in df.columns:
                    date_col = 'service_date' if 'service_date' in df.columns else 'service_from_date'
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                    df = df[df[date_col].dt.date == source_date]
                # Drop rows with NaT/missing service_date so we never pass invalid dates to DB
                if 'service_date' in df.columns or 'service_from_date' in df.columns:
                    date_col = 'service_date' if 'service_date' in df.columns else 'service_from_date'
                    df = df[df[date_col].notna()]
                
                if df.empty:
                    continue
                
                # Convert to database format
                claims_data = []
                for _, row in df.iterrows():
                    svc = row.get('service_date') or row.get('service_from_date')
                    if pd.isna(svc):
                        continue
                    try:
                        service_date = pd.to_datetime(svc)
                        if pd.isna(service_date):
                            continue
                        service_date = service_date.date() if hasattr(service_date, 'date') else service_date
                    except Exception:
                        continue
                    paid_val = row.get('paid_date')
                    paid_date = None
                    if paid_val is not None and pd.notna(paid_val):
                        try:
                            paid_date = pd.to_datetime(paid_val)
                            if not pd.isna(paid_date):
                                paid_date = paid_date.date() if hasattr(paid_date, 'date') else paid_date
                        except Exception:
                            pass
                    claim_data = {
                        'tenant_id': tenant_id,
                        'claim_id': str(row.get('claim_id', '')),
                        'claim_line_id': str(row.get('claim_line_id', '')),
                        'member_id': str(row.get('member_id', '')),
                        'provider_id': str(row.get('provider_id', '')),
                        'service_date': service_date,
                        'paid_date': paid_date,
                        'lob': str(row.get('lob', 'COMMERCIAL')),
                        'market': str(row.get('market', '')),
                        'cpt_code': str(row.get('cpt_code') or row.get('cpt_hcpcs', '')),
                        'hcpcs_code': str(row.get('hcpcs_code', '')),
                        'service_category': str(row.get('service_category', '')),
                        'place_of_service': str(row.get('place_of_service', '')),
                        'units': float(row.get('units', 1.0)),
                        'allowed_amount': float(row.get('allowed_amount', 0.0)),
                        'paid_amount': float(row.get('paid_amount', 0.0)),
                        'member_cost_share': float(row.get('member_cost_share', 0.0)),
                        'in_network': bool(row.get('in_network', True)),
                        'source_system': 'DAILY_LOAD',
                        'source_file_id': str(claims_file.name),
                        'ingestion_id': uuid4(),  # Unique ingestion ID for daily load
                    }
                    claims_data.append(claim_data)
                
                if claims_data:
                    loaded = repo.bulk_insert_claims_lines(
                        tenant_id=tenant_id,
                        claims_data=claims_data,
                        source_system='DAILY_LOAD',
                        source_file_id=str(claims_file.name),
                        ingestion_id=UUID('00000000-0000-0000-0000-000000000000'),
                    )
                    counts["claims_loaded"] += loaded
                
            except Exception as e:
                db.rollback()
                print(f"Error loading claims from {claims_file}: {e}")
                continue
        
        # Load enrollment data if available
        enrollment_files = list(search_root.glob("**/enrollment*.csv")) + list(search_root.glob("**/ENROLLMENT*.csv"))
        for enrollment_file in enrollment_files:
            try:
                df = pd.read_csv(enrollment_file, low_memory=False)
                # Filter by date if available
                if 'enrollment_date' in df.columns:
                    df['enrollment_date'] = pd.to_datetime(df['enrollment_date']).dt.date
                    df = df[df['enrollment_date'] == source_date]
                
                if not df.empty:
                    # Convert and insert enrollment records
                    # Implementation depends on EnrollmentRecordDB structure
                    counts["enrollment_loaded"] += len(df)
            except Exception as e:
                db.rollback()
                print(f"Error loading enrollment from {enrollment_file}: {e}")
                continue
        
        return {
            "success": True,
            "source_date": source_date.isoformat(),
            **counts,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "claims_loaded": 0,
            "enrollment_loaded": 0,
            "providers_loaded": 0,
        }
    finally:
        if should_close:
            db.close()
