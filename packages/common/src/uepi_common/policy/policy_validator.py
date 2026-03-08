"""
PolicyLogic Validator
Validates policy schema (scope/levers/conditions/exceptions) against metadata
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from ..data_contracts.policy_logic import PolicyLogic, PolicyLever, PolicyScope, ConditionGroup, ExceptionGroup
from ..data_contracts.policy_metadata import (
    get_policy_type_metadata,
    LeverType,
    POLICY_TYPE_CATALOG,
    ConditionType,
    ExceptionType,
)


class ValidationError(BaseException):
    """Policy validation error"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class PolicyValidator:
    """Validates PolicyLogic structure against metadata schemas"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, policy: PolicyLogic) -> tuple[bool, List[str], List[str]]:
        """
        Validate a policy
        
        Returns:
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Validate policy container
        self._validate_policy_container(policy)
        
        # Validate scope
        self._validate_scope(policy.scope)
        
        # Validate levers
        if not policy.levers:
            self.errors.append("Policy must have at least one lever")
        else:
            for i, lever in enumerate(policy.levers):
                self._validate_lever(lever, i)
        
        # Validate global conditions
        if policy.global_conditions:
            self._validate_condition_group(policy.global_conditions)
        
        # Validate global exceptions
        if policy.global_exceptions:
            self._validate_exception_group(policy.global_exceptions)
        
        # Validate effective dates
        self._validate_effective_dates(policy)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_policy_container(self, policy: PolicyLogic) -> None:
        """Validate policy container metadata"""
        if not policy.policy_name or not policy.policy_name.strip():
            self.errors.append("Policy name is required")
        
        if not policy.policy_owner or not policy.policy_owner.strip():
            self.errors.append("Policy owner is required")
        
        if not policy.scope:
            self.errors.append("Policy scope is required")
    
    def _validate_scope(self, scope: PolicyScope) -> None:
        """Validate policy scope"""
        if not scope.line_of_business and not scope.markets and not scope.network_id:
            self.warnings.append("Policy scope is very broad - consider specifying LOB, markets, or network")
    
    def _validate_lever(self, lever: PolicyLever, index: int) -> None:
        """Validate a policy lever"""
        # Get metadata for this lever type
        metadata = get_policy_type_metadata(lever.lever_type)
        if not metadata:
            self.errors.append(f"Lever {index}: Unknown lever type {lever.lever_type}")
            return
        
        # Validate lever name
        if not lever.name or not lever.name.strip():
            self.errors.append(f"Lever {index}: Lever name is required")
        
        # Validate required parameters
        for param in metadata.supported_parameters:
            if param.required and param.name not in lever.parameters:
                self.errors.append(
                    f"Lever {index} ({lever.lever_type.value}): Required parameter '{param.name}' is missing"
                )
        
        # Validate parameter values
        for param_name, param_value in lever.parameters.items():
            param_def = next((p for p in metadata.supported_parameters if p.name == param_name), None)
            if param_def:
                # Validate against allowed values
                if param_def.allowed_values and param_value not in param_def.allowed_values:
                    self.errors.append(
                        f"Lever {index} ({lever.lever_type.value}): Parameter '{param_name}' has invalid value. "
                        f"Allowed: {param_def.allowed_values}"
                    )
            else:
                self.warnings.append(
                    f"Lever {index} ({lever.lever_type.value}): Unknown parameter '{param_name}'"
                )
        
        # Validate conditions
        if lever.conditions:
            self._validate_condition_group(lever.conditions, metadata.supported_conditions, f"Lever {index}")
        
        # Validate exceptions
        if lever.exceptions:
            self._validate_exception_group(lever.exceptions, metadata.supported_exceptions, f"Lever {index}")
    
    def _validate_condition_group(
        self,
        condition_group: ConditionGroup,
        allowed_types: Optional[List[ConditionType]] = None,
        context: str = "Global"
    ) -> None:
        """Validate a condition group"""
        if condition_group.logic not in ["AND", "OR"]:
            self.errors.append(f"{context}: Condition group logic must be AND or OR")
        
        for condition in condition_group.conditions:
            if isinstance(condition, ConditionGroup):
                # Recursive validation
                self._validate_condition_group(condition, allowed_types, context)
            else:
                # Validate condition rule
                if allowed_types and condition.type not in allowed_types:
                    self.warnings.append(
                        f"{context}: Condition type {condition.type.value} may not be supported for this lever"
                    )
    
    def _validate_exception_group(
        self,
        exception_group: ExceptionGroup,
        allowed_types: Optional[List[ExceptionType]] = None,
        context: str = "Global"
    ) -> None:
        """Validate an exception group"""
        if exception_group.logic not in ["AND", "OR"]:
            self.errors.append(f"{context}: Exception group logic must be AND or OR")
        
        for exception in exception_group.exceptions:
            if isinstance(exception, ExceptionGroup):
                # Recursive validation
                self._validate_exception_group(exception, allowed_types, context)
            else:
                # Validate exception rule
                if allowed_types and exception.type not in allowed_types:
                    self.warnings.append(
                        f"{context}: Exception type {exception.type.value} may not be supported for this lever"
                    )
    
    def _validate_effective_dates(self, policy: PolicyLogic) -> None:
        """Validate effective dates"""
        if policy.effective_end and policy.effective_end < policy.effective_start:
            self.errors.append("Effective end date must be after start date")
    
    def calculate_readiness_score(self, policy: PolicyLogic) -> tuple[float, List[str]]:
        """
        Calculate policy readiness score (0-1) and list issues
        
        Factors:
        - Has scope defined (0.2)
        - Has at least one lever (0.2)
        - All required parameters present (0.2)
        - Has conditions/exceptions defined (0.2)
        - Effective dates valid (0.1)
        - Has description/notes (0.1)
        """
        score = 0.0
        issues = []
        
        # Scope (0.2)
        if policy.scope and (policy.scope.line_of_business or policy.scope.markets or policy.scope.network_id):
            score += 0.2
        else:
            issues.append("Scope not fully defined")
        
        # Levers (0.2)
        if policy.levers:
            score += 0.2
        else:
            issues.append("No levers defined")
        
        # Required parameters (0.2)
        all_params_present = True
        for lever in policy.levers:
            metadata = get_policy_type_metadata(lever.lever_type)
            if metadata:
                for param in metadata.supported_parameters:
                    if param.required and param.name not in lever.parameters:
                        all_params_present = False
                        issues.append(f"Lever {lever.lever_type.value}: Missing required parameter '{param.name}'")
        
        if all_params_present and policy.levers:
            score += 0.2
        
        # Conditions/Exceptions (0.2)
        has_conditions = (
            (policy.global_conditions is not None) or
            any(lever.conditions is not None for lever in policy.levers)
        )
        has_exceptions = (
            (policy.global_exceptions is not None) or
            any(lever.exceptions is not None for lever in policy.levers)
        )
        if has_conditions or has_exceptions:
            score += 0.2
        else:
            issues.append("No conditions or exceptions defined")
        
        # Effective dates (0.1)
        if policy.effective_start:
            score += 0.1
        else:
            issues.append("Effective start date not set")
        
        # Description/Notes (0.1)
        if policy.policy_description or any(lever.notes for lever in policy.levers):
            score += 0.1
        else:
            issues.append("Policy description or notes missing")
        
        return min(score, 1.0), issues

