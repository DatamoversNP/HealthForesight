"""Policy mapper - maps external policy formats to UEPI canonical format"""
from typing import Any, Optional
from enum import Enum
from datetime import datetime

from uepi_common.models import (
    PolicyType,
    PolicyScope,
    EffectivePeriod,
    Enforcement,
    PolicyLever,
    EnforcementMechanism,
    PolicyTouchpoint,
    CodeType,
)


class ExternalPolicyFormat(str, Enum):
    """External policy format types"""
    JSON = "JSON"
    CSV = "CSV"
    EXCEL = "EXCEL"


class PolicyMapper:
    """Maps external policy formats to UEPI canonical format"""
    
    # Policy type mapping (external system → UEPI)
    POLICY_TYPE_MAP = {
        "prior_authorization": PolicyType.PRIOR_AUTH,
        "prior_auth": PolicyType.PRIOR_AUTH,
        "pre_auth": PolicyType.PRIOR_AUTH,
        "site_of_care": PolicyType.SITE_OF_CARE,
        "site_of_service": PolicyType.SITE_OF_CARE,
        "frequency_limit": PolicyType.DURATION_FREQUENCY_LIMIT,
        "duration_limit": PolicyType.DURATION_FREQUENCY_LIMIT,
        "visit_limit": PolicyType.DURATION_FREQUENCY_LIMIT,
        "cost_sharing": PolicyType.COST_SHARING,
        "copay": PolicyType.COST_SHARING,
        "coinsurance": PolicyType.COST_SHARING,
        "network_restriction": PolicyType.NETWORK_RESTRICTION,
        "referral_requirement": PolicyType.REFERRAL_REQUIREMENT,
        "clinical_criteria": PolicyType.CLINICAL_CRITERIA,
        "composite": PolicyType.COMPOSITE,
        "bundle": PolicyType.COMPOSITE,
    }
    
    def map_policy_type(self, external_type: str) -> PolicyType:
        """Map external policy type to UEPI PolicyType
        
        Args:
            external_type: External policy type string
            
        Returns:
            UEPI PolicyType
        """
        if not external_type:
            return PolicyType.PRIOR_AUTH  # Default
        
        normalized = external_type.lower().replace(" ", "_").replace("-", "_")
        
        # Direct match
        if normalized in self.POLICY_TYPE_MAP:
            return self.POLICY_TYPE_MAP[normalized]
        
        # Partial match
        for key, policy_type in self.POLICY_TYPE_MAP.items():
            if key in normalized or normalized in key:
                return policy_type
        
        # Default fallback
        return PolicyType.PRIOR_AUTH
    
    def map_scope(self, external_scope: dict[str, Any]) -> PolicyScope:
        """Map external scope to UEPI PolicyScope
        
        Args:
            external_scope: External scope dictionary
            
        Returns:
            UEPI PolicyScope
        """
        if not external_scope:
            return PolicyScope(lob=None, markets=None, network=None)
        
        # Map LOB
        lob = external_scope.get("lob") or external_scope.get("line_of_business") or external_scope.get("product")
        
        # Map markets
        markets = external_scope.get("markets") or external_scope.get("market") or external_scope.get("states")
        if isinstance(markets, str):
            markets = [markets]
        elif not isinstance(markets, list):
            markets = None
        
        # Map network
        network = external_scope.get("network") or external_scope.get("network_tier") or external_scope.get("tier")
        if isinstance(network, str):
            network = [network]
        elif not isinstance(network, list):
            network = None
        
        return PolicyScope(
            lob=lob,
            markets=markets,
            network=network,
        )
    
    def map_effective_period(self, external_period: dict[str, Any] | str) -> EffectivePeriod:
        """Map external effective period to UEPI EffectivePeriod
        
        Args:
            external_period: External period (dict or ISO date string)
            
        Returns:
            UEPI EffectivePeriod
        """
        if isinstance(external_period, str):
            # Try to parse as date string
            try:
                start_date = datetime.fromisoformat(external_period.replace("Z", "+00:00"))
                return EffectivePeriod(start_date=start_date, end_date=None)
            except Exception:
                return EffectivePeriod(start_date=datetime.utcnow(), end_date=None)
        
        if not external_period or not isinstance(external_period, dict):
            return EffectivePeriod(start_date=datetime.utcnow(), end_date=None)
        
        # Map start date
        start_date_str = (
            external_period.get("start_date") or
            external_period.get("effective_date") or
            external_period.get("start") or
            external_period.get("begin_date")
        )
        if isinstance(start_date_str, str):
            try:
                start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            except Exception:
                start_date = datetime.utcnow()
        else:
            start_date = datetime.utcnow()
        
        # Map end date
        end_date_str = (
            external_period.get("end_date") or
            external_period.get("expiration_date") or
            external_period.get("end") or
            external_period.get("termination_date")
        )
        end_date = None
        if end_date_str:
            if isinstance(end_date_str, str):
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                except Exception:
                    end_date = None
        
        return EffectivePeriod(start_date=start_date, end_date=end_date)
    
    def map_enforcement(self, external_enforcement: dict[str, Any]) -> Enforcement:
        """Map external enforcement to UEPI Enforcement
        
        Args:
            external_enforcement: External enforcement dictionary
            
        Returns:
            UEPI Enforcement
        """
        if not external_enforcement:
            return Enforcement(
                mechanism=EnforcementMechanism.HARD,
                touchpoint=[PolicyTouchpoint.CLAIM_EDIT],
                override_allowed=False,
            )
        
        # Map mechanism
        mechanism_str = external_enforcement.get("mechanism") or external_enforcement.get("type") or "hard"
        mechanism_map = {
            "hard": EnforcementMechanism.HARD,
            "soft": EnforcementMechanism.SOFT,
            "advisory": EnforcementMechanism.ADVISORY,
        }
        mechanism = mechanism_map.get(mechanism_str.lower(), EnforcementMechanism.HARD)
        
        # Map touchpoint
        touchpoint_str = external_enforcement.get("touchpoint") or external_enforcement.get("point") or ["claim_edit"]
        if isinstance(touchpoint_str, str):
            touchpoint_str = [touchpoint_str]
        elif not isinstance(touchpoint_str, list):
            touchpoint_str = ["claim_edit"]
        
        touchpoint_map = {
            "claim_edit": PolicyTouchpoint.CLAIM_EDIT,
            "pre_claim": PolicyTouchpoint.PRE_CLAIM,
            "real_time": PolicyTouchpoint.REAL_TIME,
        }
        touchpoints = [
            touchpoint_map.get(tp.lower().replace(" ", "_"), PolicyTouchpoint.CLAIM_EDIT)
            for tp in touchpoint_str
        ]
        if not touchpoints:
            touchpoints = [PolicyTouchpoint.CLAIM_EDIT]
        
        # Map override
        override_allowed = external_enforcement.get("override_allowed") or external_enforcement.get("can_override") or False
        
        return Enforcement(
            mechanism=mechanism,
            touchpoint=touchpoints,
            override_allowed=override_allowed,
        )
    
    def map_policy_levers(self, external_levers: list[dict[str, Any]]) -> list[PolicyLever]:
        """Map external policy levers to UEPI PolicyLever list
        
        Args:
            external_levers: List of external lever dictionaries
            
        Returns:
            List of UEPI PolicyLever objects
        """
        if not external_levers or not isinstance(external_levers, list):
            return []
        
        mapped_levers = []
        
        for lever_dict in external_levers:
            try:
                lever_type_str = lever_dict.get("lever_type") or lever_dict.get("type") or "prior_auth"
                
                # Map lever type (simplified - full mapping would be more complex)
                lever_type_map = {
                    "prior_auth": "PRIOR_AUTH",
                    "site_of_care": "SITE_OF_CARE",
                    "frequency_limit": "DURATION_FREQUENCY_LIMIT",
                    "cost_sharing": "COST_SHARING",
                }
                lever_type = lever_type_map.get(lever_type_str.lower(), "PRIOR_AUTH")
                
                # Map targets (code sets)
                targets = lever_dict.get("targets") or lever_dict.get("codes") or []
                if isinstance(targets, str):
                    targets = [targets]
                
                # Build simplified lever - PolicyLever uses parameters dict
                # Map targets to parameters
                parameters: dict[str, Any] = {}
                if targets:
                    parameters["codes"] = targets if isinstance(targets, list) else [targets]
                if lever_dict.get("hcpcs_codes"):
                    parameters["hcpcs_codes"] = lever_dict["hcpcs_codes"]
                if lever_dict.get("drg_codes"):
                    parameters["drg_codes"] = lever_dict["drg_codes"]
                
                # Add other lever-specific parameters
                if lever_dict.get("config"):
                    parameters.update(lever_dict["config"])
                
                # Map policy type enum
                try:
                    lever_type_enum = PolicyType(lever_type)
                except (ValueError, TypeError):
                    # Fallback to PRIOR_AUTH if type not recognized
                    lever_type_enum = PolicyType.PRIOR_AUTH
                
                lever = PolicyLever(
                    lever_type=lever_type_enum,
                    parameters=parameters,
                )
                mapped_levers.append(lever)
            except Exception as e:
                # Skip invalid levers but continue processing
                continue
        
        return mapped_levers

