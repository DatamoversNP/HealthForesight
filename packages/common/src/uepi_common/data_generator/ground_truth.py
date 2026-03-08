"""Ground truth outcome generator for validation"""
from datetime import date
from typing import Any
from decimal import Decimal


class GroundTruthGenerator:
    """Generate ground truth expected outcomes for policy validation
    
    This generator creates expected outcomes that match the embedded
    behavioral patterns in the synthetic data generator.
    """
    
    @staticmethod
    def generate_expected_outcomes(
        policy_id: str,
        policy_type: str,
        effective_date: date,
        pre_window_months: int = 6,
        post_window_months: int = 6,
    ) -> dict[str, Any]:
        """Generate expected outcomes for a policy
        
        Args:
            policy_id: Policy ID
            policy_type: Policy type (e.g., 'PRIOR_AUTH', 'SITE_OF_CARE')
            effective_date: Policy effective date
            pre_window_months: Pre-policy window in months
            post_window_months: Post-policy window in months
            
        Returns:
            Dictionary with expected outcomes including:
            - expected_direction: Expected change direction (UP, DOWN, MIXED)
            - expected_magnitude: Expected percentage change
            - expected_substitution: Expected substitution codes/services
            - expected_cost_impact: Expected cost impact (UP, DOWN, MIXED)
        """
        # Policy-specific expected outcomes based on type
        outcomes = {
            "PRIOR_AUTH": {
                "expected_direction": {
                    "utilization": "DOWN",  # Prior auth reduces utilization
                    "cost": "MIXED",  # May increase due to ER substitution
                },
                "expected_magnitude": {
                    "utilization_change_pct": -25.0,  # -25% utilization
                    "cost_change_pct": 5.0,  # +5% cost (net increase from substitution)
                },
                "expected_substitution_codes": ["70450", "70460", "72141"],  # ER imaging codes
                "expected_substitution_category": "ER_IMAGING",
                "expected_lag_days": 30,  # Substitution occurs within 30 days
            },
            "SITE_OF_CARE": {
                "expected_direction": {
                    "utilization": "STABLE",  # Volume stays same
                    "cost": "DOWN",  # Cost decreases (freestanding cheaper)
                },
                "expected_magnitude": {
                    "utilization_change_pct": 0.0,
                    "cost_change_pct": -15.0,  # -15% cost
                },
                "expected_substitution_codes": [],
                "expected_substitution_category": None,
                "expected_lag_days": 0,
            },
            "DURATION_FREQUENCY_LIMIT": {
                "expected_direction": {
                    "utilization": "DOWN",  # Limits reduce utilization
                    "cost": "DOWN",  # Cost decreases
                },
                "expected_magnitude": {
                    "utilization_change_pct": -40.0,  # -40% utilization
                    "cost_change_pct": -35.0,  # -35% cost
                },
                "expected_substitution_codes": ["99213", "99214"],  # Office visits increase
                "expected_substitution_category": "PRIMARY_CARE",
                "expected_lag_days": 60,  # Substitution after limit is hit
            },
            "COST_SHARING": {
                "expected_direction": {
                    "utilization": "DOWN",  # Higher copay reduces utilization
                    "cost": "UP",  # ER visits increase (cost sharing backfire)
                },
                "expected_magnitude": {
                    "utilization_change_pct": -20.0,  # -20% utilization
                    "cost_change_pct": 10.0,  # +10% cost (ER substitution)
                },
                "expected_substitution_codes": ["99284", "99285"],  # ER visits
                "expected_substitution_category": "EMERGENCY",
                "expected_lag_days": 15,  # Quick substitution
            },
            "COMPOSITE": {
                "expected_direction": {
                    "utilization": "DOWN",
                    "cost": "MIXED",
                },
                "expected_magnitude": {
                    "utilization_change_pct": -30.0,
                    "cost_change_pct": 0.0,
                },
                "expected_substitution_codes": ["70450", "99284"],
                "expected_substitution_category": "MIXED",
                "expected_lag_days": 30,
            },
        }
        
        # Get base outcomes for policy type
        base_outcomes = outcomes.get(policy_type, {
            "expected_direction": {"utilization": "MIXED", "cost": "MIXED"},
            "expected_magnitude": {"utilization_change_pct": 0.0, "cost_change_pct": 0.0},
            "expected_substitution_codes": [],
            "expected_substitution_category": None,
            "expected_lag_days": 0,
        })
        
        return {
            "policy_id": policy_id,
            "policy_type": policy_type,
            "effective_date": effective_date.isoformat(),
            "pre_window_months": pre_window_months,
            "post_window_months": post_window_months,
            **base_outcomes,
            "confidence_level": "HIGH",  # High confidence for synthetic data
            "data_sufficiency": {
                "sufficient": True,
                "min_sample_size": 1000,
                "actual_sample_size": 5000,  # Synthetic data has sufficient samples
            },
        }
    
    @staticmethod
    def generate_policy_events(
        policies: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate policy events for embedding in synthetic data
        
        Args:
            policies: List of policy dictionaries with:
                - policy_id
                - policy_type
                - effective_date (date or ISO string)
                - service_category (ServiceCategory enum)
                
        Returns:
            List of policy event dictionaries with:
                - effective_date
                - service_category
                - volume_multiplier (0.0-1.0)
                - cost_multiplier (1.0+)
        """
        events = []
        
        for policy in policies:
            policy_type = policy.get("policy_type", "UNKNOWN")
            effective_date = policy.get("effective_date")
            if isinstance(effective_date, str):
                effective_date = date.fromisoformat(effective_date)
            
            service_category = policy.get("service_category")
            
            # Map policy type to impact multipliers
            impact_map = {
                "PRIOR_AUTH": {
                    "volume_multiplier": 0.75,  # 25% reduction
                    "cost_multiplier": 1.0,
                },
                "SITE_OF_CARE": {
                    "volume_multiplier": 1.0,  # Volume stable
                    "cost_multiplier": 0.85,  # 15% cost reduction
                },
                "DURATION_FREQUENCY_LIMIT": {
                    "volume_multiplier": 0.60,  # 40% reduction
                    "cost_multiplier": 0.65,  # 35% cost reduction
                },
                "COST_SHARING": {
                    "volume_multiplier": 0.80,  # 20% reduction
                    "cost_multiplier": 1.0,
                },
                "COMPOSITE": {
                    "volume_multiplier": 0.70,  # 30% reduction
                    "cost_multiplier": 1.0,
                },
            }
            
            impact = impact_map.get(policy_type, {
                "volume_multiplier": 1.0,
                "cost_multiplier": 1.0,
            })
            
            events.append({
                "policy_id": policy.get("policy_id"),
                "effective_date": effective_date,
                "service_category": service_category,
                **impact,
            })
        
        return events

