"""Prompt template library for Conversational AI"""
from typing import Dict, Any, List, Optional
from enum import Enum

from uepi_api.models.conversational_ai import ConversationMode, ConversationDomain


class PromptTemplate:
    """Prompt template with variables"""
    
    def __init__(self, name: str, template: str, variables: List[str]):
        self.name = name
        self.template = template
        self.variables = variables
    
    def render(self, **kwargs) -> str:
        """Render template with provided variables"""
        result = self.template
        for var in self.variables:
            value = kwargs.get(var, f"{{{var}}}")
            result = result.replace(f"{{{var}}}", str(value))
        return result


# Policy Domain Templates
POLICY_TEMPLATES = {
    "CREATE_POLICY": PromptTemplate(
        name="create_policy",
        template="""You are a Policy Intelligence Assistant helping to create healthcare utilization management policies.

USER CONTEXT:
- Roles: {user_roles}
- Permissions: {permissions}

TASK: Create a {policy_type} policy based on the user's request.

USER REQUEST: {user_prompt}

RELEVANT CONTEXT:
{policy_context}

INSTRUCTIONS:
1. Parse the user's intent carefully
2. Extract key information:
   - Policy type (Prior Auth, Step Therapy, Site of Care, Quantity Limit, etc.)
   - Line of Business (Commercial, Medicare, Medicaid, MA)
   - Geography/Markets (states, regions, or "ALL")
   - Target services (CPT codes, HCPCS codes, service categories)
   - Conditions and exceptions
   - Effective date
3. Ask clarifying questions ONLY if critical information is missing
4. Generate a complete policy JSON structure

OUTPUT FORMAT (JSON):
{{
  "natural_language": "Human-readable explanation of the policy created",
  "structured_output": {{
    "action_type": "POLICY_DRAFT",
    "policy_name": "Descriptive policy name",
    "policy_type": "PRIOR AUTH|STEP THERAPY|SITE OF CARE|QUANTITY LIMIT|COMPOSITE",
    "description": "Detailed policy description",
    "status": "DRAFT",
    "scope": {{
      "lob": ["COMMERCIAL"],
      "markets": ["TX"],
      "network": ["IN"]
    }},
    "enforcement": {{
      "mechanism": "HARD|SOFT|PASSIVE",
      "touchpoint": ["PA_WORKFLOW"],
      "override_allowed": true
    }},
    "policy_levers": [
      {{
        "lever_type": "PRIOR_AUTH|STEP_THERAPY|SITE_OF_CARE|QUANTITY_LIMIT",
        "parameters": {{}}
      }}
    ],
    "exceptions": ["ONCOLOGY", "EMERGENCY"],
    "effective_date": "2025-07-01"
  }},
  "next_steps": ["Review policy draft", "Edit details", "Submit for approval"],
  "confidence": "HIGH|MEDIUM|LOW",
  "requires_clarification": false,
  "clarification_questions": []
}}

IMPORTANT:
- Always create policies as DRAFT status
- Never auto-approve or execute policies
- Include all relevant exceptions and conditions
- Use realistic CPT/HCPCS codes when possible""",
        variables=["user_roles", "permissions", "policy_type", "user_prompt", "policy_context"]
    ),
    
    "MODIFY_POLICY": PromptTemplate(
        name="modify_policy",
        template="""You are helping to modify an existing policy.

POLICY TO MODIFY:
{policy_details}

USER REQUEST: {user_prompt}

Generate the modified policy structure. Maintain existing elements unless explicitly changed.""",
        variables=["policy_details", "user_prompt"]
    ),
}

# Data Domain Templates
DATA_TEMPLATES = {
    "CREATE_PIPELINE": PromptTemplate(
        name="create_pipeline",
        template="""You are a Data Engineering Assistant helping to set up data ingestion pipelines.

USER REQUEST: {user_prompt}

RELEVANT CONTEXT:
{pipeline_context}

INSTRUCTIONS:
1. Extract pipeline configuration details:
   - Source type (S3, SFTP, API, Database, File)
   - Frequency (Daily, Weekly, Monthly, Real-time)
   - Data type (Claims, Member, Provider, Enrollment, Pharmacy)
   - File format (CSV, Parquet, JSON)
   - Schema information
2. Ask clarifying questions about:
   - Primary key fields
   - Date fields for partitioning
   - Data quality rules
3. Generate pipeline configuration

OUTPUT FORMAT (JSON):
{{
  "natural_language": "Explanation of pipeline configuration",
  "structured_output": {{
    "action_type": "PIPELINE_CONFIG",
    "pipeline_name": "Descriptive name",
    "source_type": "S3|SFTP|API|DATABASE|FILE",
    "frequency": "DAILY|WEEKLY|MONTHLY|REAL_TIME",
    "data_type": "CLAIMS|MEMBER|PROVIDER|ENROLLMENT|PHARMACY",
    "schema_mapping": {{}},
    "data_quality_checks": [],
    "status": "DRAFT"
  }},
  "next_steps": ["Review configuration", "Specify schema mapping", "Submit to Data Ops"],
  "confidence": "HIGH|MEDIUM|LOW",
  "requires_clarification": true,
  "clarification_questions": ["What are the primary key fields?", "What date fields should be used?"]
}}

IMPORTANT:
- NEVER deploy pipelines automatically
- Only propose configurations
- Submit to Data Ops queue for review""",
        variables=["user_prompt", "pipeline_context"]
    ),
}

# Baseline Domain Templates
BASELINE_TEMPLATES = {
    "CREATE_BASELINE": PromptTemplate(
        name="create_baseline",
        template="""You are helping to create a baseline for policy impact measurement.

USER REQUEST: {user_prompt}

RELEVANT CONTEXT:
{baseline_context}

Explain what a baseline is and generate baseline configuration.

OUTPUT FORMAT (JSON):
{{
  "natural_language": "Explanation of baseline and configuration",
  "structured_output": {{
    "action_type": "BASELINE_CONFIG",
    "baseline_name": "Descriptive name",
    "time_window": {{"start": "2024-01-01", "end": "2024-12-31"}},
    "exclusions": ["Q4"],
    "metrics": ["UTIL_PER_1K", "COST_PMPM"],
    "status": "DRAFT"
  }},
  "next_steps": ["Review configuration", "Confirm and trigger baseline job"],
  "confidence": "MEDIUM",
  "requires_clarification": false,
  "clarification_questions": []
}}""",
        variables=["user_prompt", "baseline_context"]
    ),
}

# Impact Domain Templates
IMPACT_TEMPLATES = {
    "EXPLAIN_IMPACT": PromptTemplate(
        name="explain_impact",
        template="""You are explaining observed policy impact using evidence.

USER QUESTION: {user_prompt}

RELEVANT DATA:
{impact_context}

Provide evidence-based explanation with:
- Observed impact results
- Comparison to baseline and predictions
- Confidence scores
- Limitations
- Supporting metrics

OUTPUT FORMAT (JSON):
{{
  "natural_language": "Executive-ready explanation",
  "structured_output": {{
    "action_type": "EXPLANATION",
    "explanation": "Detailed explanation",
    "evidence": {{
      "observed_impact": {{}},
      "baseline_comparison": {{}},
      "predicted_vs_observed": {{}},
      "confidence_score": 0.85,
      "limitations": []
    }},
    "metrics": {{}},
    "models_used": []
  }},
  "next_steps": ["Review explanation", "Export for presentation"],
  "confidence": "HIGH|MEDIUM|LOW",
  "requires_clarification": false,
  "clarification_questions": []
}}""",
        variables=["user_prompt", "impact_context"]
    ),
}

# Governance Domain Templates
GOVERNANCE_TEMPLATES = {
    "QUERY_POLICIES": PromptTemplate(
        name="query_policies",
        template="""You are helping to query and manage policy lifecycle.

USER QUERY: {user_prompt}

RELEVANT CONTEXT:
{policy_context}

Translate the query into system queries and present results.

OUTPUT FORMAT (JSON):
{{
  "natural_language": "Query results explanation",
  "structured_output": {{
    "action_type": "QUERY_RESULTS",
    "query": {user_prompt},
    "results": [],
    "data_sources": []
  }},
  "next_steps": ["Review results", "Take action if needed"],
  "confidence": "MEDIUM",
  "requires_clarification": false,
  "clarification_questions": []
}}

IMPORTANT:
- Never bypass approvals
- Only query and present data
- Suggest actions but don't execute""",
        variables=["user_prompt", "policy_context"]
    ),
}


def get_template(mode: ConversationMode, domain: Optional[ConversationDomain]) -> Optional[PromptTemplate]:
    """Get appropriate template based on mode and domain"""
    
    if mode == ConversationMode.DRAFT:
        if domain == ConversationDomain.POLICY:
            return POLICY_TEMPLATES.get("CREATE_POLICY")
        elif domain == ConversationDomain.DATA:
            return DATA_TEMPLATES.get("CREATE_PIPELINE")
        elif domain == ConversationDomain.BASELINE:
            return BASELINE_TEMPLATES.get("CREATE_BASELINE")
    
    elif mode == ConversationMode.EXPLAIN:
        if domain == ConversationDomain.IMPACT:
            return IMPACT_TEMPLATES.get("EXPLAIN_IMPACT")
    
    elif mode == ConversationMode.QUERY:
        if domain == ConversationDomain.GOVERNANCE:
            return GOVERNANCE_TEMPLATES.get("QUERY_POLICIES")
    
    return None


def format_context_for_prompt(context: Dict[str, Any]) -> str:
    """Format RAG context for inclusion in prompt"""
    parts = []
    
    if context.get("policies"):
        parts.append("RELEVANT POLICIES:")
        for policy in context["policies"][:3]:  # Top 3
            parts.append(f"- {policy['name']} ({policy['policy_type']}): {policy['description']}")
    
    if context.get("pipelines"):
        parts.append("\nRELEVANT PIPELINES:")
        for pipeline in context["pipelines"][:3]:
            parts.append(f"- {pipeline['name']} ({pipeline['source_type']}): {pipeline['description']}")
    
    if context.get("baselines"):
        parts.append("\nRELEVANT BASELINES:")
        for baseline in context["baselines"][:3]:
            parts.append(f"- {baseline['name']}")
    
    return "\n".join(parts) if parts else "No relevant context found."

