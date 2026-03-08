"""Safety guardrails for Conversational AI"""
from typing import Dict, Any, List, Optional
import re
import json


class SafetyGuardrails:
    """Content filtering and safety checks for LLM outputs"""
    
    def __init__(self):
        # Prohibited actions that should never be executed
        self.prohibited_actions = [
            r"approve.*policy",
            r"activate.*policy",
            r"delete.*policy",
            r"override.*approval",
            r"bypass.*workflow",
            r"execute.*directly",
            r"skip.*review",
            r"auto.*deploy",
            r"production.*config",
        ]
        
        # High-risk patterns
        self.high_risk_patterns = [
            r"delete.*all",
            r"remove.*data",
            r"drop.*table",
            r"truncate",
            r"production.*change",
        ]
        
        # Unauthorized access patterns
        self.unauthorized_patterns = [
            r"access.*admin",
            r"elevate.*privilege",
            r"grant.*role",
            r"bypass.*permission",
        ]
    
    def check_content(self, content: str, structured_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check content for safety violations
        
        Returns:
            {
                "safe": bool,
                "violations": List[str],
                "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
                "blocked": bool
            }
        """
        violations = []
        risk_level = "LOW"
        blocked = False
        
        content_lower = content.lower()
        output_str = json.dumps(structured_output).lower() if structured_output else ""
        combined = f"{content_lower} {output_str}"
        
        # Check for prohibited actions
        for pattern in self.prohibited_actions:
            if re.search(pattern, combined, re.I):
                violations.append(f"Prohibited action detected: {pattern}")
                risk_level = "HIGH"
                blocked = True
        
        # Check for high-risk patterns
        for pattern in self.high_risk_patterns:
            if re.search(pattern, combined, re.I):
                violations.append(f"High-risk pattern detected: {pattern}")
                if risk_level == "LOW":
                    risk_level = "MEDIUM"
        
        # Check for unauthorized access
        for pattern in self.unauthorized_patterns:
            if re.search(pattern, combined, re.I):
                violations.append(f"Unauthorized access pattern: {pattern}")
                risk_level = "HIGH"
                blocked = True
        
        # Check structured output for dangerous fields
        if structured_output:
            # Never allow auto-execution
            if structured_output.get("auto_execute") or structured_output.get("skip_approval"):
                violations.append("Auto-execution or skip-approval detected in structured output")
                risk_level = "CRITICAL"
                blocked = True
            
            # Ensure status is always DRAFT for new items
            if structured_output.get("action_type") in ["POLICY_DRAFT", "PIPELINE_CONFIG", "BASELINE_CONFIG"]:
                if structured_output.get("status") and structured_output["status"] != "DRAFT":
                    violations.append("Non-DRAFT status detected for new artifact")
                    risk_level = "HIGH"
                    # Force to DRAFT
                    structured_output["status"] = "DRAFT"
        
        return {
            "safe": len(violations) == 0,
            "violations": violations,
            "risk_level": risk_level,
            "blocked": blocked
        }
    
    def sanitize_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize output to ensure safety"""
        sanitized = output.copy()
        
        # Ensure structured_output never has dangerous fields
        if "structured_output" in sanitized:
            so = sanitized["structured_output"].copy()
            
            # Remove dangerous fields
            dangerous_fields = ["auto_execute", "skip_approval", "bypass_workflow", "production"]
            for field in dangerous_fields:
                so.pop(field, None)
            
            # Force DRAFT status for creation actions
            if so.get("action_type") in ["POLICY_DRAFT", "PIPELINE_CONFIG", "BASELINE_CONFIG"]:
                so["status"] = "DRAFT"
                so["confidence"] = "DRAFT_ONLY"
            
            sanitized["structured_output"] = so
        
        return sanitized
    
    def validate_role_permissions(
        self,
        user_roles: List[str],
        action_type: str,
        resource: str
    ) -> Dict[str, Any]:
        """Validate that user has permission for requested action"""
        from uepi_api.routers.access import ROLE_PERMISSIONS
        
        # Check if any role has required permission
        has_permission = False
        for role in user_roles:
            role_perms = ROLE_PERMISSIONS.get(role, {})
            if resource in role_perms:
                actions = role_perms[resource]
                if action_type.lower() in [a.lower() for a in actions]:
                    has_permission = True
                    break
        
        return {
            "allowed": has_permission,
            "roles": user_roles,
            "required_permission": f"{resource}:{action_type}",
            "message": "Permission granted" if has_permission else "Insufficient permissions"
        }

