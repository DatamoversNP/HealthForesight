"""
Policy Similarity / De-dup Detection
Near-duplicate detection to avoid multiple versions stored incorrectly
"""
from typing import List, Tuple, Dict, Any
from uuid import UUID
import hashlib
import json

from ..data_contracts.policy_logic import PolicyLogic, PolicyLever
from ..data_contracts.policy_metadata import LeverType


class PolicySimilarityDetector:
    """Detects similar/duplicate policies"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize similarity detector
        
        Args:
            similarity_threshold: Threshold for considering policies similar (0-1)
        """
        self.similarity_threshold = similarity_threshold
    
    def find_similar_policies(
        self,
        policy: PolicyLogic,
        candidate_policies: List[PolicyLogic]
    ) -> List[Tuple[PolicyLogic, float]]:
        """
        Find policies similar to the given policy
        
        Returns:
            List of (similar_policy, similarity_score) tuples
        """
        similar = []
        
        for candidate in candidate_policies:
            if candidate.policy_id == policy.policy_id:
                continue  # Skip self
            
            score = self.calculate_similarity(policy, candidate)
            if score >= self.similarity_threshold:
                similar.append((candidate, score))
        
        # Sort by similarity score (descending)
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar
    
    def calculate_similarity(self, policy1: PolicyLogic, policy2: PolicyLogic) -> float:
        """
        Calculate similarity score between two policies (0-1)
        
        Factors:
        - Name similarity (0.2)
        - Scope similarity (0.3)
        - Lever similarity (0.4)
        - Effective date overlap (0.1)
        """
        score = 0.0
        
        # Name similarity (0.2)
        name_sim = self._text_similarity(policy1.policy_name, policy2.policy_name)
        score += name_sim * 0.2
        
        # Scope similarity (0.3)
        scope_sim = self._scope_similarity(policy1.scope, policy2.scope)
        score += scope_sim * 0.3
        
        # Lever similarity (0.4)
        lever_sim = self._lever_similarity(policy1.levers, policy2.levers)
        score += lever_sim * 0.4
        
        # Effective date overlap (0.1)
        date_sim = self._date_overlap_similarity(
            policy1.effective_start, policy1.effective_end,
            policy2.effective_start, policy2.effective_end
        )
        score += date_sim * 0.1
        
        return min(score, 1.0)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple word overlap"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _scope_similarity(self, scope1, scope2) -> float:
        """Calculate scope similarity"""
        score = 0.0
        factors = 0
        
        # LOB similarity
        if scope1.line_of_business or scope2.line_of_business:
            factors += 1
            lob1 = set(scope1.line_of_business or [])
            lob2 = set(scope2.line_of_business or [])
            if lob1 and lob2:
                score += len(lob1.intersection(lob2)) / len(lob1.union(lob2))
            elif lob1 == lob2:  # Both empty
                score += 1.0
        
        # Markets similarity
        if scope1.markets or scope2.markets:
            factors += 1
            markets1 = set(scope1.markets or [])
            markets2 = set(scope2.markets or [])
            if markets1 and markets2:
                score += len(markets1.intersection(markets2)) / len(markets1.union(markets2))
            elif markets1 == markets2:
                score += 1.0
        
        # Network similarity
        if scope1.network_id or scope2.network_id:
            factors += 1
            if scope1.network_id == scope2.network_id:
                score += 1.0
        
        return score / factors if factors > 0 else 0.5  # Default to 0.5 if no scope defined
    
    def _lever_similarity(self, levers1: List[PolicyLever], levers2: List[PolicyLever]) -> float:
        """Calculate lever similarity"""
        if not levers1 or not levers2:
            return 0.0
        
        # Compare lever types
        types1 = {lever.lever_type for lever in levers1}
        types2 = {lever.lever_type for lever in levers2}
        
        type_similarity = len(types1.intersection(types2)) / len(types1.union(types2)) if types1.union(types2) else 0.0
        
        # Compare lever parameters (simplified - compare parameter keys)
        param_similarity = 0.0
        param_count = 0
        for lever1 in levers1:
            for lever2 in levers2:
                if lever1.lever_type == lever2.lever_type:
                    params1 = set(lever1.parameters.keys())
                    params2 = set(lever2.parameters.keys())
                    if params1 or params2:
                        param_similarity += len(params1.intersection(params2)) / len(params1.union(params2)) if params1.union(params2) else 0.0
                        param_count += 1
        
        param_sim = param_similarity / param_count if param_count > 0 else 0.0
        
        # Weighted average
        return (type_similarity * 0.7) + (param_sim * 0.3)
    
    def _date_overlap_similarity(
        self,
        start1, end1,
        start2, end2
    ) -> float:
        """Calculate date overlap similarity"""
        if not start1 or not start2:
            return 0.0
        
        # Check if dates overlap
        if end1 and end2:
            if start1 <= end2 and start2 <= end1:
                # Calculate overlap percentage
                overlap_start = max(start1, start2)
                overlap_end = min(end1, end2)
                overlap_days = (overlap_end - overlap_start).days
                period1_days = (end1 - start1).days
                period2_days = (end2 - start2).days
                if period1_days > 0 and period2_days > 0:
                    return min(overlap_days / period1_days, overlap_days / period2_days)
        elif start1 == start2:
            return 1.0
        
        return 0.0
    
    def generate_policy_hash(self, policy: PolicyLogic) -> str:
        """
        Generate a hash for policy content (for exact duplicate detection)
        
        This ignores policy_id, version, and timestamps
        """
        # Create a normalized representation
        normalized = {
            "name": policy.policy_name.lower().strip(),
            "scope": {
                "lob": sorted(policy.scope.line_of_business or []),
                "markets": sorted(policy.scope.markets or []),
                "network_id": policy.scope.network_id,
            },
            "levers": sorted([
                {
                    "type": lever.lever_type.value,
                    "name": lever.name.lower().strip(),
                    "parameters": json.dumps(lever.parameters, sort_keys=True),
                }
                for lever in policy.levers
            ], key=lambda x: x["type"]),
            "effective_start": policy.effective_start.isoformat() if policy.effective_start else None,
        }
        
        # Generate hash
        content = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def is_exact_duplicate(self, policy1: PolicyLogic, policy2: PolicyLogic) -> bool:
        """Check if two policies are exact duplicates (ignoring IDs and timestamps)"""
        return self.generate_policy_hash(policy1) == self.generate_policy_hash(policy2)

