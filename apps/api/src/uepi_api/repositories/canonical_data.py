"""Repository layer for canonical data database operations"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import pandas as pd

from uepi_api.models.canonical_data import ClaimsLineDB, EnrollmentRecordDB, ProviderRecordDB
from uepi_common.data_contracts.claims import ClaimsLine
from uepi_common.data_contracts.enrollment import EnrollmentRecord
from uepi_common.data_contracts.providers import ProviderRecord


class CanonicalDataRepository:
    """Repository for canonical data database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== ClaimsLine Operations ==========
    
    def bulk_insert_claims_lines(
        self,
        tenant_id: UUID,
        claims_data: List[Dict[str, Any]],
        source_system: str,
        source_file_id: str,
        ingestion_id: UUID,
    ) -> int:
        """Bulk insert claims lines into database"""
        records = []
        for claim_dict in claims_data:
            # Convert Pydantic model to dict if needed
            if isinstance(claim_dict, ClaimsLine):
                claim_dict = claim_dict.model_dump()
            
            # Convert dates
            service_date = claim_dict.get('service_date')
            if isinstance(service_date, str):
                service_date = date.fromisoformat(service_date)
            
            paid_date = claim_dict.get('paid_date')
            if paid_date and isinstance(paid_date, str):
                paid_date = date.fromisoformat(paid_date)
            
            adjudication_date = claim_dict.get('adjudication_date')
            if adjudication_date and isinstance(adjudication_date, str):
                adjudication_date = date.fromisoformat(adjudication_date)
            
            # Convert Decimal
            def to_decimal(v):
                if v is None:
                    return Decimal('0')
                if isinstance(v, (int, float)):
                    return Decimal(str(v))
                if isinstance(v, str):
                    return Decimal(v)
                return v
            
            record = ClaimsLineDB(
                tenant_id=tenant_id,
                claim_id=str(claim_dict.get('claim_id', '')),
                claim_line_id=str(claim_dict.get('claim_line_id', '')),
                member_id=str(claim_dict.get('member_id', '')),
                provider_id=str(claim_dict.get('provider_id', '')),
                service_date=service_date,
                paid_date=paid_date,
                adjudication_date=adjudication_date,
                lob=str(claim_dict.get('lob', '')),
                market=str(claim_dict.get('market', '')),
                cpt_code=claim_dict.get('cpt_code'),
                hcpcs_code=claim_dict.get('hcpcs_code'),
                drg_code=claim_dict.get('drg_code'),
                icd10_diagnosis_codes=claim_dict.get('icd10_diagnosis_codes'),
                icd10_procedure_codes=claim_dict.get('icd10_procedure_codes'),
                service_category=str(claim_dict.get('service_category', '')),
                place_of_service=str(claim_dict.get('place_of_service', '')),
                units=to_decimal(claim_dict.get('units', 0)),
                allowed_amount=to_decimal(claim_dict.get('allowed_amount', 0)),
                paid_amount=to_decimal(claim_dict.get('paid_amount', 0)),
                member_cost_share=to_decimal(claim_dict.get('member_cost_share', 0)),
                in_network=bool(claim_dict.get('in_network', True)),
                requires_prior_auth=bool(claim_dict.get('requires_prior_auth', False)),
                prior_auth_approved=claim_dict.get('prior_auth_approved'),
                prior_auth_id=claim_dict.get('prior_auth_id'),
                facility_type=claim_dict.get('facility_type'),
                system_affiliation=claim_dict.get('system_affiliation'),
                rendering_provider_id=claim_dict.get('rendering_provider_id'),
                billing_provider_id=claim_dict.get('billing_provider_id'),
                referring_provider_id=claim_dict.get('referring_provider_id'),
                source_system=source_system,
                source_file_id=source_file_id,
                ingestion_id=ingestion_id,
                record_hash=claim_dict.get('record_hash'),
            )
            records.append(record)
        
        # Bulk insert using add_all; on duplicate (tenant_id, claim_line_id) rollback and return 0 so caller can continue
        try:
            self.db.add_all(records)
            self.db.commit()
            return len(records)
        except Exception as e:
            self.db.rollback()
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError):
                # Duplicate (tenant_id, claim_line_id): skip this batch so re-loading same CSV doesn't fail
                return 0
            raise
    
    def get_claims_lines(
        self,
        tenant_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        lob: Optional[str] = None,
        market: Optional[str] = None,
        limit: Optional[int] = None,
        cpt_codes: Optional[List[str]] = None,
        hcpcs_codes: Optional[List[str]] = None,
        service_categories: Optional[List[str]] = None,
        diagnosis_codes: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Get claims lines from database as DataFrame
        
        Optimized to filter at database level before loading into memory.
        """
        from sqlalchemy import or_
        
        query = self.db.query(ClaimsLineDB).filter(ClaimsLineDB.tenant_id == tenant_id)
        
        if start_date:
            query = query.filter(ClaimsLineDB.service_date >= start_date)
        if end_date:
            query = query.filter(ClaimsLineDB.service_date <= end_date)
        if lob:
            if isinstance(lob, list):
                query = query.filter(ClaimsLineDB.lob.in_(lob))
            else:
                query = query.filter(ClaimsLineDB.lob == lob)
        if market:
            if isinstance(market, list):
                query = query.filter(ClaimsLineDB.market.in_(market))
            else:
                query = query.filter(ClaimsLineDB.market == market)
        
        # Filter by CPT codes at database level (much faster)
        # Check both CPT and HCPCS columns since codes can be in either
        if cpt_codes:
            from sqlalchemy import or_
            # Code can be in either cpt_code or hcpcs_code column
            code_filter = or_(
                ClaimsLineDB.cpt_code.in_(cpt_codes),
                ClaimsLineDB.hcpcs_code.in_(cpt_codes)
            )
            query = query.filter(code_filter)
        
        # Filter by HCPCS codes at database level
        if hcpcs_codes:
            from sqlalchemy import or_
            # Code can be in either cpt_code or hcpcs_code column
            code_filter = or_(
                ClaimsLineDB.cpt_code.in_(hcpcs_codes),
                ClaimsLineDB.hcpcs_code.in_(hcpcs_codes)
            )
            query = query.filter(code_filter)
        
        # Filter by service categories at database level
        if service_categories:
            query = query.filter(ClaimsLineDB.service_category.in_(service_categories))
        
        # Filter by diagnosis codes (ICD-10 overlap)
        if diagnosis_codes:
            try:
                query = query.filter(ClaimsLineDB.icd10_diagnosis_codes.overlap(diagnosis_codes))
            except Exception:
                pass
        
        # For baseline computation, we need all records but process efficiently
        # Use yield_per to avoid loading everything into memory at once
        records = []
        try:
            chunk_size = 50000  # Process 50k records at a time
            max_records = 1_000_000  # Safety limit
            record_count = 0
            for record in query.yield_per(chunk_size):
                records.append(record)
                record_count += 1
                if record_count >= max_records:
                    print(f"⚠️  Reached safety limit of {max_records} records")
                    break
        except Exception as e:
            print(f"⚠️  Error in yield_per: {e}")
            # Fallback to all() for smaller result sets
            if limit and limit < 10000:
                records = query.limit(limit).all()
            else:
                records = []
        
        if limit:
            records = records[:limit]
        
        if not records:
            return pd.DataFrame()
        
        data = []
        for r in records:
            data.append({
                'claim_id': r.claim_id,
                'claim_line_id': r.claim_line_id,
                'member_id': r.member_id,
                'provider_id': r.provider_id,
                'service_date': r.service_date,
                'paid_date': r.paid_date,
                'adjudication_date': r.adjudication_date,
                'lob': r.lob,
                'market': r.market,
                'cpt_code': r.cpt_code,
                'hcpcs_code': r.hcpcs_code,
                'drg_code': r.drg_code,
                'procedure_code': r.cpt_code or r.hcpcs_code,  # Alias for compatibility
                'icd10_diagnosis_codes': r.icd10_diagnosis_codes,
                'icd10_procedure_codes': r.icd10_procedure_codes,
                'primary_diagnosis_code': r.icd10_diagnosis_codes[0] if r.icd10_diagnosis_codes and len(r.icd10_diagnosis_codes) > 0 else None,
                'secondary_diagnosis_code': r.icd10_diagnosis_codes[1] if r.icd10_diagnosis_codes and len(r.icd10_diagnosis_codes) > 1 else None,
                'service_category': r.service_category,
                'system_affiliation': r.system_affiliation,  # Required for baseline analysis
                'place_of_service': r.place_of_service,
                'units': float(r.units) if r.units else 0,
                'allowed_amount': float(r.allowed_amount) if r.allowed_amount else 0,
                'paid_amount': float(r.paid_amount) if r.paid_amount else 0,
                'member_cost_share': float(r.member_cost_share) if r.member_cost_share else 0,
                'in_network': r.in_network,
                'requires_prior_auth': r.requires_prior_auth,
                'prior_auth_approved': r.prior_auth_approved,
                'prior_auth_id': r.prior_auth_id,
                'facility_type': r.facility_type,
                'system_affiliation': r.system_affiliation,
                'rendering_provider_id': r.rendering_provider_id,
                'billing_provider_id': r.billing_provider_id,
                'referring_provider_id': r.referring_provider_id,
            })
        
        return pd.DataFrame(data)
    
    def count_claims_lines(self, tenant_id: UUID) -> int:
        """Count total claims lines for tenant"""
        return self.db.query(func.count(ClaimsLineDB.id)).filter(
            ClaimsLineDB.tenant_id == tenant_id
        ).scalar() or 0

    def count_claims_for_filters(
        self,
        tenant_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        lob: Optional[Any] = None,
        market: Optional[Any] = None,
        cpt_codes: Optional[List[str]] = None,
        hcpcs_codes: Optional[List[str]] = None,
        service_categories: Optional[List[str]] = None,
    ) -> int:
        """Count claims matching filters (same as get_claims_lines but COUNT only, no row load)."""
        from sqlalchemy import or_
        query = self.db.query(func.count(ClaimsLineDB.id)).filter(
            ClaimsLineDB.tenant_id == tenant_id
        )
        if start_date:
            query = query.filter(ClaimsLineDB.service_date >= start_date)
        if end_date:
            query = query.filter(ClaimsLineDB.service_date <= end_date)
        if lob is not None:
            if isinstance(lob, list):
                query = query.filter(ClaimsLineDB.lob.in_(lob))
            else:
                query = query.filter(ClaimsLineDB.lob == lob)
        if market is not None:
            if isinstance(market, list):
                query = query.filter(ClaimsLineDB.market.in_(market))
            else:
                query = query.filter(ClaimsLineDB.market == market)
        if cpt_codes:
            query = query.filter(
                or_(
                    ClaimsLineDB.cpt_code.in_(cpt_codes),
                    ClaimsLineDB.hcpcs_code.in_(cpt_codes),
                )
            )
        if hcpcs_codes:
            query = query.filter(
                or_(
                    ClaimsLineDB.cpt_code.in_(hcpcs_codes),
                    ClaimsLineDB.hcpcs_code.in_(hcpcs_codes),
                )
            )
        if service_categories:
            query = query.filter(ClaimsLineDB.service_category.in_(service_categories))
        return query.scalar() or 0

    def aggregate_claims_for_baseline(
        self,
        tenant_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        lob: Optional[Any] = None,
        market: Optional[Any] = None,
        cpt_codes: Optional[List[str]] = None,
        hcpcs_codes: Optional[List[str]] = None,
        service_categories: Optional[List[str]] = None,
        diagnosis_codes: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Compute baseline aggregates in the database (no row limit). Use for production-scale claim volumes.
        Returns dict with total_claims, total_paid, total_allowed, unique_members, or None if no rows."""
        from sqlalchemy import or_

        base = self.db.query(
            func.count(ClaimsLineDB.id).label("total_claims"),
            func.coalesce(func.sum(ClaimsLineDB.paid_amount), 0).label("total_paid"),
            func.coalesce(func.sum(ClaimsLineDB.allowed_amount), 0).label("total_allowed"),
            func.count(func.distinct(ClaimsLineDB.member_id)).label("unique_members"),
        ).filter(ClaimsLineDB.tenant_id == tenant_id)

        if start_date:
            base = base.filter(ClaimsLineDB.service_date >= start_date)
        if end_date:
            base = base.filter(ClaimsLineDB.service_date <= end_date)
        if lob is not None:
            if isinstance(lob, list):
                base = base.filter(ClaimsLineDB.lob.in_(lob))
            else:
                base = base.filter(ClaimsLineDB.lob == lob)
        if market is not None:
            if isinstance(market, list):
                base = base.filter(ClaimsLineDB.market.in_(market))
            else:
                base = base.filter(ClaimsLineDB.market == market)
        if cpt_codes:
            base = base.filter(
                or_(
                    ClaimsLineDB.cpt_code.in_(cpt_codes),
                    ClaimsLineDB.hcpcs_code.in_(cpt_codes),
                )
            )
        if hcpcs_codes:
            base = base.filter(
                or_(
                    ClaimsLineDB.cpt_code.in_(hcpcs_codes),
                    ClaimsLineDB.hcpcs_code.in_(hcpcs_codes),
                )
            )
        if service_categories:
            base = base.filter(ClaimsLineDB.service_category.in_(service_categories))
        if diagnosis_codes:
            try:
                base = base.filter(ClaimsLineDB.icd10_diagnosis_codes.overlap(diagnosis_codes))
            except Exception:
                pass

        row = base.first()
        if not row or (row.total_claims or 0) == 0:
            return None
        return {
            "total_claims": int(row.total_claims),
            "total_paid": float(row.total_paid),
            "total_allowed": float(row.total_allowed),
            "unique_members": int(row.unique_members),
        }

    # ========== EnrollmentRecord Operations ==========
    
    def bulk_insert_enrollment_records(
        self,
        tenant_id: UUID,
        enrollment_data: List[Dict[str, Any]],
        source_system: str,
        source_file_id: str,
        ingestion_id: UUID,
    ) -> int:
        """Bulk insert enrollment records into database"""
        records = []
        for enroll_dict in enrollment_data:
            if isinstance(enroll_dict, EnrollmentRecord):
                enroll_dict = enroll_dict.model_dump()
            
            enrollment_month = enroll_dict.get('enrollment_month')
            if isinstance(enrollment_month, str):
                enrollment_month = date.fromisoformat(enrollment_month)
            
            enrollment_start_date = enroll_dict.get('enrollment_start_date')
            if enrollment_start_date and isinstance(enrollment_start_date, str):
                enrollment_start_date = date.fromisoformat(enrollment_start_date)
            
            enrollment_end_date = enroll_dict.get('enrollment_end_date')
            if enrollment_end_date and isinstance(enrollment_end_date, str):
                enrollment_end_date = date.fromisoformat(enrollment_end_date)
            
            def to_decimal(v):
                if v is None:
                    return Decimal('0')
                if isinstance(v, (int, float)):
                    return Decimal(str(v))
                if isinstance(v, str):
                    return Decimal(v)
                return v
            
            record = EnrollmentRecordDB(
                tenant_id=tenant_id,
                member_id=str(enroll_dict.get('member_id', '')),
                enrollment_month=enrollment_month,
                lob=str(enroll_dict.get('lob', '')),
                market=str(enroll_dict.get('market', '')),
                age_band=str(enroll_dict.get('age_band', '')),
                gender=str(enroll_dict.get('gender', '')),
                risk_score=to_decimal(enroll_dict.get('risk_score', 0)),
                network_tier=str(enroll_dict.get('network_tier', '')),
                enrolled_flag=bool(enroll_dict.get('enrolled_flag', True)),
                enrollment_start_date=enrollment_start_date,
                enrollment_end_date=enrollment_end_date,
                product_type=enroll_dict.get('product_type'),
                segment=enroll_dict.get('segment'),
                source_system=source_system,
                source_file_id=source_file_id,
                ingestion_id=ingestion_id,
                record_hash=enroll_dict.get('record_hash'),
            )
            records.append(record)
        
        self.db.add_all(records)
        self.db.commit()
        return len(records)
    
    def get_enrollment_records(
        self,
        tenant_id: UUID,
        start_month: Optional[date] = None,
        end_month: Optional[date] = None,
        lob: Optional[str] = None,
        market: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get enrollment records from database as DataFrame"""
        query = self.db.query(EnrollmentRecordDB).filter(EnrollmentRecordDB.tenant_id == tenant_id)
        
        if start_month:
            query = query.filter(EnrollmentRecordDB.enrollment_month >= start_month)
        if end_month:
            query = query.filter(EnrollmentRecordDB.enrollment_month <= end_month)
        if lob:
            query = query.filter(EnrollmentRecordDB.lob == lob)
        if market:
            query = query.filter(EnrollmentRecordDB.market == market)
        
        if limit:
            query = query.limit(limit)
        
        records = query.all()
        if not records:
            return pd.DataFrame()
        
        data = []
        for r in records:
            data.append({
                'member_id': r.member_id,
                'enrollment_month': r.enrollment_month,
                'lob': r.lob,
                'market': r.market,
                'age_band': r.age_band,
                'gender': r.gender,
                'risk_score': float(r.risk_score) if r.risk_score else 0,
                'network_tier': r.network_tier,
                'enrolled_flag': r.enrolled_flag,
                'enrollment_start_date': r.enrollment_start_date,
                'enrollment_end_date': r.enrollment_end_date,
                'product_type': r.product_type,
                'segment': r.segment,
            })
        
        return pd.DataFrame(data)
    
    def count_enrollment_records(self, tenant_id: UUID) -> int:
        """Count total enrollment records for tenant"""
        return self.db.query(func.count(EnrollmentRecordDB.id)).filter(
            EnrollmentRecordDB.tenant_id == tenant_id
        ).scalar() or 0
    
    # ========== ProviderRecord Operations ==========
    
    def bulk_insert_provider_records(
        self,
        tenant_id: UUID,
        provider_data: List[Dict[str, Any]],
        source_system: str,
        source_file_id: str,
        ingestion_id: UUID,
    ) -> int:
        """Bulk insert provider records into database"""
        records = []
        for provider_dict in provider_data:
            if isinstance(provider_dict, ProviderRecord):
                provider_dict = provider_dict.model_dump()
            
            effective_date = provider_dict.get('effective_date')
            if isinstance(effective_date, str):
                effective_date = date.fromisoformat(effective_date)
            
            termination_date = provider_dict.get('termination_date')
            if termination_date and isinstance(termination_date, str):
                termination_date = date.fromisoformat(termination_date)
            
            record = ProviderRecordDB(
                tenant_id=tenant_id,
                provider_id=str(provider_dict.get('provider_id', '')),
                npi=provider_dict.get('npi'),
                provider_type=str(provider_dict.get('provider_type', '')),
                specialty=provider_dict.get('specialty'),
                facility_type=provider_dict.get('facility_type'),
                market=str(provider_dict.get('market', '')),
                state=provider_dict.get('state'),
                zip_code=provider_dict.get('zip_code'),
                network_status=str(provider_dict.get('network_status', '')),
                effective_date=effective_date,
                termination_date=termination_date,
                system_affiliation=provider_dict.get('system_affiliation'),
                system_id=provider_dict.get('system_id'),
                provider_name=provider_dict.get('provider_name'),
                tax_id=provider_dict.get('tax_id'),
                source_system=source_system,
                source_file_id=source_file_id,
                ingestion_id=ingestion_id,
                record_hash=provider_dict.get('record_hash'),
            )
            records.append(record)
        
        self.db.add_all(records)
        self.db.commit()
        return len(records)
    
    def get_provider_records(
        self,
        tenant_id: UUID,
        market: Optional[str] = None,
        network_status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get provider records from database as DataFrame"""
        query = self.db.query(ProviderRecordDB).filter(ProviderRecordDB.tenant_id == tenant_id)
        
        if market:
            query = query.filter(ProviderRecordDB.market == market)
        if network_status:
            query = query.filter(ProviderRecordDB.network_status == network_status)
        
        if limit:
            query = query.limit(limit)
        
        records = query.all()
        if not records:
            return pd.DataFrame()
        
        data = []
        for r in records:
            data.append({
                'provider_id': r.provider_id,
                'npi': r.npi,
                'provider_type': r.provider_type,
                'specialty': r.specialty,
                'facility_type': r.facility_type,
                'market': r.market,
                'state': r.state,
                'zip_code': r.zip_code,
                'network_status': r.network_status,
                'effective_date': r.effective_date,
                'termination_date': r.termination_date,
                'system_affiliation': r.system_affiliation,
                'system_id': r.system_id,
                'provider_name': r.provider_name,
                'tax_id': r.tax_id,
            })
        
        return pd.DataFrame(data)
    
    def count_provider_records(self, tenant_id: UUID) -> int:
        """Count total provider records for tenant"""
        return self.db.query(func.count(ProviderRecordDB.id)).filter(
            ProviderRecordDB.tenant_id == tenant_id
        ).scalar() or 0

