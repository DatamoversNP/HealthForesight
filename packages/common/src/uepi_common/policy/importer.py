"""Policy package importer - handles external policy formats"""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime
import json

from uepi_common.models import (
    CanonicalPolicy,
    PolicyType,
    PolicyStatus,
    PolicyScope,
    EffectivePeriod,
    Enforcement,
    PolicyLever,
    EnforcementMechanism,
    PolicyTouchpoint,
    ExpectedBehavioralResponse,
    AnalyticsExpectations,
    UIHints,
    CodeType,
)
from uepi_common.policy.mapper import PolicyMapper, ExternalPolicyFormat


class PolicyPackage:
    """Represents a policy package from an external system"""
    
    def __init__(
        self,
        source_system: str,
        source_format: ExternalPolicyFormat,
        raw_data: dict[str, Any],
    ):
        """Initialize policy package
        
        Args:
            source_system: Name of source system (e.g., "Epic UM", "HealthRules")
            source_format: Format of external policy (CSV, JSON, EXCEL)
            raw_data: Raw policy data from external system
        """
        self.source_system = source_system
        self.source_format = source_format
        self.raw_data = raw_data
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source_system": self.source_system,
            "source_format": self.source_format.value,
            "raw_data": self.raw_data,
        }


class PolicyMappingResult:
    """Result of mapping external policy to UEPI canonical format"""
    
    def __init__(
        self,
        success: bool,
        canonical_policy: Optional[CanonicalPolicy] = None,
        mapping_confidence: float = 0.0,  # 0.0 to 1.0
        unmapped_fields: list[str] = None,
        mapping_warnings: list[str] = None,
        mapping_errors: list[str] = None,
    ):
        """Initialize mapping result
        
        Args:
            success: Whether mapping was successful
            canonical_policy: Mapped canonical policy (if successful)
            mapping_confidence: Confidence score (0.0-1.0)
            unmapped_fields: List of fields that couldn't be mapped
            mapping_warnings: List of warnings during mapping
            mapping_errors: List of errors during mapping
        """
        self.success = success
        self.canonical_policy = canonical_policy
        self.mapping_confidence = mapping_confidence
        self.unmapped_fields = unmapped_fields or []
        self.mapping_warnings = mapping_warnings or []
        self.mapping_errors = mapping_errors or []
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            "success": self.success,
            "mapping_confidence": self.mapping_confidence,
            "unmapped_fields": self.unmapped_fields,
            "mapping_warnings": self.mapping_warnings,
            "mapping_errors": self.mapping_errors,
        }
        
        if self.canonical_policy:
            result["canonical_policy"] = {
                "policy_name": self.canonical_policy.policy_name,
                "policy_type": self.canonical_policy.policy_type.value if hasattr(self.canonical_policy.policy_type, "value") else str(self.canonical_policy.policy_type),
                "description": self.canonical_policy.description,
                "status": self.canonical_policy.status.value if hasattr(self.canonical_policy.status, "value") else str(self.canonical_policy.status),
                "scope": self.canonical_policy.scope.model_dump() if hasattr(self.canonical_policy.scope, "model_dump") else self.canonical_policy.scope.dict() if hasattr(self.canonical_policy.scope, "dict") else self.canonical_policy.scope,
                "effective_period": self.canonical_policy.effective_period.model_dump() if hasattr(self.canonical_policy.effective_period, "model_dump") else self.canonical_policy.effective_period.dict() if hasattr(self.canonical_policy.effective_period, "dict") else self.canonical_policy.effective_period,
                "enforcement": self.canonical_policy.enforcement.model_dump() if hasattr(self.canonical_policy.enforcement, "model_dump") else self.canonical_policy.enforcement.dict() if hasattr(self.canonical_policy.enforcement, "dict") else self.canonical_policy.enforcement,
                "policy_levers": [lever.model_dump() if hasattr(lever, "model_dump") else lever.dict() if hasattr(lever, "dict") else lever for lever in self.canonical_policy.policy_levers] if self.canonical_policy.policy_levers else [],
            }
        
        return result


class PolicyPackageImporter:
    """Imports policy packages from external systems and maps to UEPI canonical format"""
    
    def __init__(self):
        """Initialize importer"""
        self.mapper = PolicyMapper()
    
    def import_package(
        self,
        package: PolicyPackage,
        auto_map: bool = True,
    ) -> PolicyMappingResult:
        """Import a policy package and map to canonical format
        
        Args:
            package: Policy package from external system
            auto_map: If True, automatically map fields; if False, return unmapped structure
            
        Returns:
            PolicyMappingResult with mapping status and canonical policy
        """
        try:
            # Map based on source format
            if package.source_format == ExternalPolicyFormat.JSON:
                return self._import_json_package(package, auto_map)
            elif package.source_format == ExternalPolicyFormat.CSV:
                return self._import_csv_package(package, auto_map)
            elif package.source_format == ExternalPolicyFormat.EXCEL:
                return self._import_excel_package(package, auto_map)
            else:
                return PolicyMappingResult(
                    success=False,
                    mapping_errors=[f"Unsupported source format: {package.source_format}"],
                )
        except Exception as e:
            return PolicyMappingResult(
                success=False,
                mapping_errors=[f"Import failed: {str(e)}"],
            )
    
    def _import_json_package(
        self,
        package: PolicyPackage,
        auto_map: bool,
    ) -> PolicyMappingResult:
        """Import JSON policy package"""
        raw_data = package.raw_data
        
        # Try to map common JSON structures
        policy_name = raw_data.get("policy_name") or raw_data.get("name") or raw_data.get("title") or "Imported Policy"
        policy_type_str = raw_data.get("policy_type") or raw_data.get("type") or "PRIOR_AUTH"
        
        # Map policy type
        policy_type = self.mapper.map_policy_type(policy_type_str)
        
        # Map scope
        scope = self.mapper.map_scope(raw_data.get("scope") or raw_data.get("applicable_to") or {})
        
        # Map effective period
        effective_period = self.mapper.map_effective_period(
            raw_data.get("effective_period") or raw_data.get("dates") or raw_data.get("effective_date") or {}
        )
        
        # Map enforcement
        enforcement = self.mapper.map_enforcement(raw_data.get("enforcement") or raw_data.get("enforcement_mechanism") or {})
        
        # Map policy levers
        levers = self.mapper.map_policy_levers(
            raw_data.get("levers") or raw_data.get("policy_levers") or raw_data.get("rules") or []
        )
        
        # Build canonical policy
        canonical_policy = CanonicalPolicy(
            policy_id=None,  # Will be assigned when saved
            policy_name=policy_name,
            policy_type=policy_type,
            description=raw_data.get("description") or raw_data.get("summary"),
            status=PolicyStatus.DRAFT,  # Start as draft for review
            scope=scope,
            effective_period=effective_period,
            enforcement=enforcement,
            policy_levers=levers,
            expected_behavioral_response=None,
            analytics_expectations=None,
            ui_hints=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Calculate confidence based on mapped fields
        mapped_fields = sum([
            1 if policy_name else 0,
            1 if policy_type else 0,
            1 if scope else 0,
            1 if effective_period else 0,
            1 if enforcement else 0,
            1 if levers else 0,
        ])
        total_fields = 6
        confidence = mapped_fields / total_fields if total_fields > 0 else 0.0
        
        # Identify unmapped fields
        unmapped_fields = []
        if not raw_data.get("policy_name") and not raw_data.get("name") and not raw_data.get("title"):
            unmapped_fields.append("policy_name")
        if not raw_data.get("policy_type") and not raw_data.get("type"):
            unmapped_fields.append("policy_type")
        if not raw_data.get("scope") and not raw_data.get("applicable_to"):
            unmapped_fields.append("scope")
        
        return PolicyMappingResult(
            success=True,
            canonical_policy=canonical_policy,
            mapping_confidence=confidence,
            unmapped_fields=unmapped_fields,
            mapping_warnings=[],
            mapping_errors=[],
        )
    
    def _import_csv_package(
        self,
        package: PolicyPackage,
        auto_map: bool,
    ) -> PolicyMappingResult:
        """Import CSV policy package"""
        # CSV import is more complex - would need header mapping
        # For MVP, return error suggesting JSON format
        return PolicyMappingResult(
            success=False,
            mapping_errors=["CSV import not yet supported. Please use JSON format."],
        )
    
    def _import_excel_package(
        self,
        package: PolicyPackage,
        auto_map: bool,
    ) -> PolicyMappingResult:
        """Import Excel policy package"""
        # Excel import would require pandas/openpyxl
        # For MVP, return error suggesting JSON format
        return PolicyMappingResult(
            success=False,
            mapping_errors=["Excel import not yet supported. Please use JSON format."],
        )

