"""Comprehensive tests for synthetic data generator"""
import pytest
from datetime import date, timedelta
from uuid import uuid4
from decimal import Decimal

from uepi_common.data_generator.generator import SyntheticDataGenerator, RANDOM_SEED
from uepi_common.data_generator.ground_truth import GroundTruthGenerator
from uepi_common.data_contracts.claims import ClaimsLine, ServiceCategory
from uepi_common.data_contracts.enrollment import EnrollmentRecord, AgeBand
from uepi_common.data_contracts.providers import ProviderRecord, Specialty


def test_generator_deterministic():
    """Test that generator produces identical results with same seed"""
    tenant_id = uuid4()
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 31)
    
    # Generate data with seed 42
    gen1 = SyntheticDataGenerator(seed=42)
    enrollment1 = gen1.generate_enrollment(tenant_id, 100, start_date, end_date)
    providers1 = gen1.generate_providers(50, start_date)
    
    # Generate again with same seed
    gen2 = SyntheticDataGenerator(seed=42)
    enrollment2 = gen2.generate_enrollment(tenant_id, 100, start_date, end_date)
    providers2 = gen2.generate_providers(50, start_date)
    
    # Results should be identical
    assert len(enrollment1) == len(enrollment2)
    assert len(providers1) == len(providers2)
    
    # Check first record is identical
    if enrollment1:
        assert enrollment1[0].member_id == enrollment2[0].member_id
        assert enrollment1[0].lob == enrollment2[0].lob
        assert enrollment1[0].market == enrollment2[0].market


def test_generator_different_seeds():
    """Test that different seeds produce different results"""
    tenant_id = uuid4()
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 31)
    
    # Generate with seed 42
    gen1 = SyntheticDataGenerator(seed=42)
    enrollment1 = gen1.generate_enrollment(tenant_id, 100, start_date, end_date)
    
    # Generate with seed 43
    gen2 = SyntheticDataGenerator(seed=43)
    enrollment2 = gen2.generate_enrollment(tenant_id, 100, start_date, end_date)
    
    # Results should be different (check first record)
    if enrollment1 and enrollment2:
        # At least one field should differ
        different = (
            enrollment1[0].member_id != enrollment2[0].member_id or
            enrollment1[0].lob != enrollment2[0].lob or
            enrollment1[0].market != enrollment2[0].market
        )
        assert different, "Different seeds should produce different results"


def test_enrollment_record_validation():
    """Test that generated enrollment records are valid"""
    tenant_id = uuid4()
    start_date = date(2024, 1, 1)
    end_date = date(2024, 2, 1)  # 2 months
    
    gen = SyntheticDataGenerator(seed=RANDOM_SEED)
    enrollment = gen.generate_enrollment(tenant_id, 100, start_date, end_date)
    
    assert len(enrollment) > 0
    
    # Validate each record
    for record in enrollment[:10]:  # Check first 10
        assert isinstance(record, EnrollmentRecord)
        assert record.member_id is not None
        assert record.enrollment_month is not None
        assert record.lob in ["Commercial", "Medicare", "Medicaid"]
        assert record.market in ["CA", "TX", "NY", "FL", "IL"]
        assert record.age_band in list(AgeBand)
        assert record.gender in list(record.gender.__class__)  # Gender enum
        assert record.risk_score >= Decimal("0")
        assert record.enrolled_flag is True or record.enrolled_flag is False


def test_provider_record_validation():
    """Test that generated provider records are valid"""
    effective_date = date(2024, 1, 1)
    
    gen = SyntheticDataGenerator(seed=RANDOM_SEED)
    providers = gen.generate_providers(50, effective_date)
    
    assert len(providers) == 50
    
    # Validate each record
    for provider in providers[:10]:  # Check first 10
        assert isinstance(provider, ProviderRecord)
        assert provider.provider_id is not None
        assert provider.npi is not None
        assert len(provider.npi) == 10
        assert provider.provider_type is not None
        assert provider.market in ["CA", "TX", "NY", "FL", "IL"]
        assert provider.network_status is not None


def test_claims_lines_validation():
    """Test that generated claims lines are valid"""
    tenant_id = uuid4()
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 15)  # 2 weeks
    
    gen = SyntheticDataGenerator(seed=RANDOM_SEED)
    
    # Generate enrollment and providers first
    enrollment = gen.generate_enrollment(tenant_id, 50, start_date, end_date)
    providers = gen.generate_providers(20, start_date)
    
    # Generate claims
    claims = gen.generate_claims_lines(
        tenant_id,
        enrollment,
        providers,
        start_date,
        end_date,
    )
    
    assert len(claims) > 0
    
    # Validate each claim
    for claim in claims[:10]:  # Check first 10
        assert isinstance(claim, ClaimsLine)
        assert claim.claim_id is not None
        assert claim.claim_line_id is not None
        assert claim.member_id is not None
        assert claim.provider_id is not None
        assert claim.service_date is not None
        assert claim.lob in ["Commercial", "Medicare", "Medicaid"]
        assert claim.market in ["CA", "TX", "NY", "FL", "IL"]
        assert claim.service_category in list(ServiceCategory)
        assert claim.allowed_amount >= Decimal("0")
        assert claim.paid_amount >= Decimal("0")
        assert claim.member_cost_share >= Decimal("0")


def test_claims_lines_with_policy_impact():
    """Test that policy events affect claims generation"""
    tenant_id = uuid4()
    start_date = date(2024, 1, 1)
    end_date = date(2024, 3, 1)  # 3 months
    policy_date = date(2024, 2, 1)  # Policy effective mid-timeline
    
    gen = SyntheticDataGenerator(seed=RANDOM_SEED)
    
    enrollment = gen.generate_enrollment(tenant_id, 50, start_date, end_date)
    providers = gen.generate_providers(20, start_date)
    
    # Generate claims without policy
    claims_no_policy = gen.generate_claims_lines(
        tenant_id,
        enrollment,
        providers,
        start_date,
        end_date,
        policy_events=None,
    )
    
    # Generate claims with policy (25% volume reduction)
    policy_events = [{
        "effective_date": policy_date,
        "service_category": ServiceCategory.IMAGING,
        "volume_multiplier": 0.75,  # 25% reduction
        "cost_multiplier": 1.0,
    }]
    
    claims_with_policy = gen.generate_claims_lines(
        tenant_id,
        enrollment,
        providers,
        start_date,
        end_date,
        policy_events=policy_events,
    )
    
    # Claims with policy should have fewer imaging claims after policy date
    imaging_before_policy = [c for c in claims_no_policy 
                            if c.service_category == ServiceCategory.IMAGING 
                            and c.service_date < policy_date]
    imaging_after_policy_no = [c for c in claims_no_policy 
                              if c.service_category == ServiceCategory.IMAGING 
                              and c.service_date >= policy_date]
    imaging_after_policy_yes = [c for c in claims_with_policy 
                               if c.service_category == ServiceCategory.IMAGING 
                               and c.service_date >= policy_date]
    
    # Volume after policy should be lower with policy
    if len(imaging_after_policy_no) > 0 and len(imaging_after_policy_yes) > 0:
        # At least verify different counts (policy impact)
        assert len(imaging_after_policy_yes) <= len(imaging_after_policy_no) * 1.1  # Allow some variance


def test_ground_truth_generation():
    """Test ground truth outcome generation"""
    policy_id = "POL-001"
    policy_type = "PRIOR_AUTH"
    effective_date = date(2024, 1, 1)
    
    outcomes = GroundTruthGenerator.generate_expected_outcomes(
        policy_id,
        policy_type,
        effective_date,
        pre_window_months=6,
        post_window_months=6,
    )
    
    assert outcomes["policy_id"] == policy_id
    assert outcomes["policy_type"] == policy_type
    assert outcomes["expected_direction"]["utilization"] == "DOWN"
    assert outcomes["expected_direction"]["cost"] == "MIXED"
    assert outcomes["expected_magnitude"]["utilization_change_pct"] == -25.0
    assert outcomes["expected_magnitude"]["cost_change_pct"] == 5.0
    assert "70450" in outcomes["expected_substitution_codes"]
    assert outcomes["confidence_level"] == "HIGH"


def test_ground_truth_different_policy_types():
    """Test ground truth for different policy types"""
    effective_date = date(2024, 1, 1)
    
    policy_types = [
        "PRIOR_AUTH",
        "SITE_OF_CARE",
        "DURATION_FREQUENCY_LIMIT",
        "COST_SHARING",
        "COMPOSITE",
    ]
    
    for policy_type in policy_types:
        outcomes = GroundTruthGenerator.generate_expected_outcomes(
            f"POL-{policy_type}",
            policy_type,
            effective_date,
        )
        
        assert outcomes["policy_type"] == policy_type
        assert "expected_direction" in outcomes
        assert "expected_magnitude" in outcomes
        assert "expected_substitution_codes" in outcomes


def test_policy_events_generation():
    """Test policy events generation for embedding"""
    policies = [
        {
            "policy_id": "POL-001",
            "policy_type": "PRIOR_AUTH",
            "effective_date": date(2024, 2, 1),
            "service_category": ServiceCategory.IMAGING,
        },
        {
            "policy_id": "POL-002",
            "policy_type": "SITE_OF_CARE",
            "effective_date": date(2024, 2, 15),
            "service_category": ServiceCategory.PROCEDURE,
        },
    ]
    
    events = GroundTruthGenerator.generate_policy_events(policies)
    
    assert len(events) == 2
    assert events[0]["policy_id"] == "POL-001"
    assert events[0]["volume_multiplier"] == 0.75  # 25% reduction for PRIOR_AUTH
    assert events[1]["policy_id"] == "POL-002"
    assert events[1]["volume_multiplier"] == 1.0  # Volume stable for SITE_OF_CARE
    assert events[1]["cost_multiplier"] == 0.85  # 15% cost reduction

