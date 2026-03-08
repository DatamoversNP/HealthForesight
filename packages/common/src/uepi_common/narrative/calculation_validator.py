"""
Validation functions for baseline analysis calculations
Ensures calculations follow standard healthcare analytics formulas
"""

from typing import Dict, Any, List, Optional, Tuple
import math


class CalculationValidator:
    """
    Validate calculations to ensure they follow standard formulas
    and are defensible to clients
    """
    
    @staticmethod
    def validate_utilization_rate(
        total_claims: int,
        member_months: float,
        calculated_rate: float,
        tolerance: float = 0.01,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate utilization rate calculation
        
        Formula: (Total claims / Member-months) × 1,000
        
        Args:
            total_claims: Total number of claim lines
            member_months: Total member-months
            calculated_rate: The calculated rate to validate
            tolerance: Acceptable difference (default 0.01 = 1%)
            
        Returns:
            (is_valid, error_message)
        """
        if member_months <= 0:
            return False, "Member-months must be greater than 0"
        
        expected_rate = (total_claims / member_months) * 1000
        difference = abs(calculated_rate - expected_rate)
        relative_error = difference / expected_rate if expected_rate > 0 else float('inf')
        
        if relative_error > tolerance:
            return False, (
                f"Utilization rate validation failed: "
                f"Expected {expected_rate:.2f}, got {calculated_rate:.2f} "
                f"(difference: {difference:.2f}, relative error: {relative_error*100:.2f}%)"
            )
        
        return True, None
    
    @staticmethod
    def validate_cost_pmpm(
        total_cost: float,
        member_months: float,
        calculated_pmpm: float,
        tolerance: float = 0.01,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate cost PMPM calculation
        
        Formula: Total cost / Member-months
        
        Args:
            total_cost: Total allowed/paid amount
            member_months: Total member-months
            calculated_pmpm: The calculated PMPM to validate
            tolerance: Acceptable difference (default 0.01 = 1%)
            
        Returns:
            (is_valid, error_message)
        """
        if member_months <= 0:
            return False, "Member-months must be greater than 0"
        
        expected_pmpm = total_cost / member_months
        difference = abs(calculated_pmpm - expected_pmpm)
        relative_error = difference / abs(expected_pmpm) if expected_pmpm != 0 else float('inf')
        
        if relative_error > tolerance:
            return False, (
                f"Cost PMPM validation failed: "
                f"Expected ${expected_pmpm:.2f}, got ${calculated_pmpm:.2f} "
                f"(difference: ${difference:.2f}, relative error: {relative_error*100:.2f}%)"
            )
        
        return True, None
    
    @staticmethod
    def validate_avg_cost_per_claim(
        total_cost: float,
        total_claims: int,
        calculated_avg: float,
        tolerance: float = 0.01,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate average cost per claim
        
        Formula: Total cost / Total claims
        
        Args:
            total_cost: Total allowed/paid amount
            total_claims: Total number of claim lines
            calculated_avg: The calculated average to validate
            tolerance: Acceptable difference (default 0.01 = 1%)
            
        Returns:
            (is_valid, error_message)
        """
        if total_claims <= 0:
            return False, "Total claims must be greater than 0"
        
        expected_avg = total_cost / total_claims
        difference = abs(calculated_avg - expected_avg)
        relative_error = difference / abs(expected_avg) if expected_avg != 0 else float('inf')
        
        if relative_error > tolerance:
            return False, (
                f"Average cost per claim validation failed: "
                f"Expected ${expected_avg:.2f}, got ${calculated_avg:.2f} "
                f"(difference: ${difference:.2f}, relative error: {relative_error*100:.2f}%)"
            )
        
        return True, None
    
    @staticmethod
    def validate_claims_per_member(
        total_claims: int,
        unique_members: int,
        calculated_rate: float,
        tolerance: float = 0.01,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate claims per member
        
        Formula: Total claims / Unique members
        
        Args:
            total_claims: Total number of claim lines
            unique_members: Number of unique members
            calculated_rate: The calculated rate to validate
            tolerance: Acceptable difference (default 0.01 = 1%)
            
        Returns:
            (is_valid, error_message)
        """
        if unique_members <= 0:
            return False, "Unique members must be greater than 0"
        
        expected_rate = total_claims / unique_members
        difference = abs(calculated_rate - expected_rate)
        relative_error = difference / expected_rate if expected_rate > 0 else float('inf')
        
        if relative_error > tolerance:
            return False, (
                f"Claims per member validation failed: "
                f"Expected {expected_rate:.2f}, got {calculated_rate:.2f} "
                f"(difference: {difference:.2f}, relative error: {relative_error*100:.2f}%)"
            )
        
        return True, None
    
    @staticmethod
    def validate_provider_archetype_metrics(
        archetype: Dict[str, Any],
        all_providers_data: List[Dict[str, Any]],
    ) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Validate all metrics for a provider archetype
        
        Args:
            archetype: Archetype with characteristics
            all_providers_data: List of provider-level data for validation
            
        Returns:
            Dict mapping metric names to (is_valid, error_message)
        """
        results = {}
        characteristics = archetype.get("characteristics", {})
        provider_count = archetype.get("provider_count", 0)
        
        # Filter providers in this archetype
        archetype_providers = [
            p for p in all_providers_data
            if p.get("archetype_id") == archetype.get("archetype_id")
        ]
        
        if len(archetype_providers) != provider_count:
            results["provider_count"] = (
                False,
                f"Provider count mismatch: expected {provider_count}, found {len(archetype_providers)}"
            )
        
        # Validate total_claims
        if "total_claims" in characteristics:
            expected_total_claims = sum(p.get("total_claims", 0) for p in archetype_providers)
            if provider_count > 0:
                expected_avg = expected_total_claims / provider_count
                calculated_avg = characteristics.get("total_claims", 0)
                if abs(calculated_avg - expected_avg) > 0.01:
                    results["total_claims"] = (
                        False,
                        f"Total claims average mismatch: expected {expected_avg:.2f}, got {calculated_avg:.2f}"
                    )
                else:
                    results["total_claims"] = (True, None)
        
        # Validate total_cost
        if "total_cost" in characteristics:
            expected_total_cost = sum(p.get("total_cost", 0) for p in archetype_providers)
            if provider_count > 0:
                expected_avg = expected_total_cost / provider_count
                calculated_avg = characteristics.get("total_cost", 0)
                if abs(calculated_avg - expected_avg) > 0.01:
                    results["total_cost"] = (
                        False,
                        f"Total cost average mismatch: expected ${expected_avg:.2f}, got ${calculated_avg:.2f}"
                    )
                else:
                    results["total_cost"] = (True, None)
        
        # Validate avg_cost_per_claim
        if "avg_cost_per_claim" in characteristics and "total_claims" in characteristics:
            total_cost = characteristics.get("total_cost", 0)
            total_claims = characteristics.get("total_claims", 0)
            is_valid, error = CalculationValidator.validate_avg_cost_per_claim(
                total_cost, int(total_claims), characteristics.get("avg_cost_per_claim", 0)
            )
            results["avg_cost_per_claim"] = (is_valid, error)
        
        return results
    
    @staticmethod
    def validate_hhi(
        provider_shares: Dict[str, float],
        calculated_hhi: float,
        tolerance: float = 0.01,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate Herfindahl-Hirschman Index (HHI) calculation
        
        Formula: Sum of (provider_share^2) × 10,000
        
        Args:
            provider_shares: Dict mapping provider_id to market share (0-1)
            calculated_hhi: The calculated HHI to validate
            tolerance: Acceptable difference (default 0.01 = 1%)
            
        Returns:
            (is_valid, error_message)
        """
        expected_hhi = sum(share ** 2 for share in provider_shares.values()) * 10000
        difference = abs(calculated_hhi - expected_hhi)
        relative_error = difference / expected_hhi if expected_hhi > 0 else float('inf')
        
        if relative_error > tolerance:
            return False, (
                f"HHI validation failed: "
                f"Expected {expected_hhi:.2f}, got {calculated_hhi:.2f} "
                f"(difference: {difference:.2f}, relative error: {relative_error*100:.2f}%)"
            )
        
        return True, None
    
    @staticmethod
    def validate_percentage(
        numerator: float,
        denominator: float,
        calculated_pct: float,
        tolerance: float = 0.01,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate percentage calculation
        
        Formula: (Numerator / Denominator) × 100
        
        Args:
            numerator: Numerator value
            denominator: Denominator value
            calculated_pct: The calculated percentage to validate
            tolerance: Acceptable difference (default 0.01 = 1%)
            
        Returns:
            (is_valid, error_message)
        """
        if denominator <= 0:
            return False, "Denominator must be greater than 0"
        
        expected_pct = (numerator / denominator) * 100
        difference = abs(calculated_pct - expected_pct)
        relative_error = difference / abs(expected_pct) if expected_pct != 0 else float('inf')
        
        if relative_error > tolerance:
            return False, (
                f"Percentage validation failed: "
                f"Expected {expected_pct:.2f}%, got {calculated_pct:.2f}% "
                f"(difference: {difference:.2f}%, relative error: {relative_error*100:.2f}%)"
            )
        
        return True, None
    
    @staticmethod
    def generate_validation_report(
        validation_results: Dict[str, Tuple[bool, Optional[str]]],
    ) -> Dict[str, Any]:
        """
        Generate a validation report from validation results
        
        Args:
            validation_results: Dict mapping metric names to (is_valid, error_message)
            
        Returns:
            Validation report with summary and details
        """
        total = len(validation_results)
        passed = sum(1 for is_valid, _ in validation_results.values() if is_valid)
        failed = total - passed
        
        report = {
            "summary": {
                "total_metrics": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": (passed / total * 100) if total > 0 else 0,
            },
            "details": {},
        }
        
        for metric_name, (is_valid, error_message) in validation_results.items():
            report["details"][metric_name] = {
                "status": "PASS" if is_valid else "FAIL",
                "error": error_message,
            }
        
        return report

