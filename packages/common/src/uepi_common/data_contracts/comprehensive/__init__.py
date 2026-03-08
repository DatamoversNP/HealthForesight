"""
Comprehensive Canonical Data Contracts
Wide schemas that accept maximum payer fields with partial availability support
"""
from uepi_common.data_contracts.canonical_base import CanonicalBase, CoverageStatus, DatasetCoverage

# Member & Eligibility Domain
from uepi_common.data_contracts.comprehensive.member import (
    MemberMaster,
    EligibilityEnrollment,
    MemberRiskStratification,
)

# Clinical Domain
from uepi_common.data_contracts.comprehensive.clinical import (
    MemberDiagnosis,
    ProblemList,
)

# Claims Domain
from uepi_common.data_contracts.comprehensive.claims import (
    ClaimHeader,
    ClaimLine,
    EpisodeOfCare,
)

# Pharmacy Domain
from uepi_common.data_contracts.comprehensive.pharmacy import (
    PharmacyClaim,
)

# Provider Domain
from uepi_common.data_contracts.comprehensive.provider import (
    ProviderMaster,
    FacilityMaster,
    NetworkConfiguration,
    ProviderContract,
)

# Benefits Domain
from uepi_common.data_contracts.comprehensive.benefits import (
    BenefitDesign,
    MemberAccumulator,
)

# UM Operations Domain
from uepi_common.data_contracts.comprehensive.um import (
    PriorAuthorizationRequest,
    ConcurrentReview,
    AppealGrievance,
)

# Referrals Domain
from uepi_common.data_contracts.comprehensive.referrals import (
    Referral,
)

# Care Management Domain
from uepi_common.data_contracts.comprehensive.care_management import (
    CareManagementEnrollment,
)

# Member Experience Domain
from uepi_common.data_contracts.comprehensive.member_experience import (
    CallCenterContact,
)

# Market Events Domain
from uepi_common.data_contracts.comprehensive.market_events import (
    MarketEvent,
)

__all__ = [
    "CanonicalBase",
    "CoverageStatus",
    "DatasetCoverage",
    # Member & Eligibility
    "MemberMaster",
    "EligibilityEnrollment",
    "MemberRiskStratification",
    # Clinical
    "MemberDiagnosis",
    "ProblemList",
    # Claims
    "ClaimHeader",
    "ClaimLine",
    "EpisodeOfCare",
    # Pharmacy
    "PharmacyClaim",
    # Provider
    "ProviderMaster",
    "FacilityMaster",
    "NetworkConfiguration",
    "ProviderContract",
    # Benefits
    "BenefitDesign",
    "MemberAccumulator",
    # UM
    "PriorAuthorizationRequest",
    "ConcurrentReview",
    "AppealGrievance",
    # Referrals
    "Referral",
    # Care Management
    "CareManagementEnrollment",
    # Member Experience
    "CallCenterContact",
    # Market Events
    "MarketEvent",
]

