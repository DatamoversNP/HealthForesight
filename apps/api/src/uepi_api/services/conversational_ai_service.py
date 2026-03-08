"""Conversational AI service - LLM integration and structured output generation"""
import json
import re
from typing import Dict, Any, Optional, List
from uuid import UUID

from uepi_api.models.conversational_ai import ConversationMode, ConversationDomain
from uepi_api.routers.access import ROLE_PERMISSIONS
from uepi_api.services.llm_client import get_llm_client
from uepi_api.services.rag_service import RAGService
from uepi_api.services.prompt_templates import get_template, format_context_for_prompt
from uepi_api.services.safety_guardrails import SafetyGuardrails
from uepi_api.services.query_cache import QueryCache
from uepi_api.services.rate_limiter import RateLimiter
from uepi_api.services.cost_tracker import CostTracker


class ConversationalAIService:
    """Service for handling conversational AI interactions"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.rag_service = RAGService()
        self.safety_guardrails = SafetyGuardrails()
        self.query_cache = QueryCache()
        self.rate_limiter = RateLimiter()
        self.cost_tracker = CostTracker()
    
    async def generate_response(
        self,
        prompt: str,
        mode: ConversationMode,
        domain: Optional[ConversationDomain],
        user_roles: List[str],
        tenant_id: UUID,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI response with structured output
        
        Returns:
            {
                "natural_language": str,
                "structured_output": Dict[str, Any],
                "next_steps": List[str],
                "confidence": str,
                "requires_clarification": bool,
                "clarification_questions": List[str]
            }
        """
        # Check cache first
        if settings.enable_query_cache:
            cached_result = self.query_cache.get(
                prompt, mode.value, domain.value if domain else None, tuple(user_roles)
            )
            if cached_result:
                return cached_result
        
        # Check rate limit
        from uepi_api.auth import CurrentUser
        # Note: We need user_id, but it's not in the signature. We'll handle this in the router.
        
        # Retrieve RAG context
        rag_context = await self.rag_service.retrieve_context(
            tenant_id=tenant_id,
            query=prompt,
            domain=domain.value if domain else None
        )
        
        # Get prompt template
        template = get_template(mode, domain)
        
        # Build system prompt
        if template:
            system_prompt = self._build_system_prompt_from_template(
                template, mode, domain, user_roles, rag_context
            )
        else:
            system_prompt = self._build_system_prompt(mode, domain, user_roles)
        
        # Build conversation context
        context = self._build_context(conversation_history or [])
        
        # Generate response using LLM
        try:
            response = await self.llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=prompt,
                context=context
            )
        except Exception as e:
            # Fallback to rule-based parsing if LLM fails
            print(f"LLM error: {e}. Falling back to rule-based parsing.")
            response = self._generate_structured_response(
                system_prompt,
                prompt,
                context,
                mode,
                domain,
                user_roles,
                rag_context
            )
        
        # Apply safety guardrails
        safety_check = self.safety_guardrails.check_content(
            response.get("natural_language", ""),
            response.get("structured_output", {})
        )
        
        if safety_check["blocked"]:
            return {
                "natural_language": f"Request blocked due to safety violations: {', '.join(safety_check['violations'])}",
                "structured_output": {},
                "next_steps": ["Review request", "Contact administrator if needed"],
                "confidence": "LOW",
                "requires_clarification": False,
                "clarification_questions": [],
                "safety_violations": safety_check["violations"]
            }
        
        # Sanitize output
        response = self.safety_guardrails.sanitize_output(response)
        
        # Validate role permissions
        if response.get("structured_output", {}).get("action_type"):
            action_type = response["structured_output"]["action_type"]
            resource_map = {
                "POLICY_DRAFT": ("policies", "create"),
                "PIPELINE_CONFIG": ("pipelines", "create"),
                "BASELINE_CONFIG": ("baselines", "create"),
            }
            
            if action_type in resource_map:
                resource, action = resource_map[action_type]
                perm_check = self.safety_guardrails.validate_role_permissions(
                    user_roles, action, resource
                )
                
                if not perm_check["allowed"]:
                    response["natural_language"] = f"Permission denied: {perm_check['message']}"
                    response["structured_output"] = {}
                    response["confidence"] = "LOW"
        
        # Cache result
        if settings.enable_query_cache:
            self.query_cache.set(
                prompt, mode.value, domain.value if domain else None, tuple(user_roles), response
            )
        
        # Track costs (if LLM was used)
        # Note: Token counts would come from LLM response metadata
        # This is a placeholder - actual implementation would extract from LLM response
        
        return response
    
    def _build_system_prompt_from_template(
        self,
        template,
        mode: ConversationMode,
        domain: Optional[ConversationDomain],
        user_roles: List[str],
        rag_context: Dict[str, Any]
    ) -> str:
        """Build system prompt from template"""
        role_context = self._get_role_context(user_roles)
        context_str = format_context_for_prompt(rag_context)
        
        return template.render(
            user_roles=", ".join(user_roles),
            permissions=role_context,
            policy_type="policy",
            user_prompt="",  # Will be provided separately
            policy_context=context_str,
            pipeline_context=context_str,
            baseline_context=context_str,
            impact_context=context_str
        )
    
    def _build_system_prompt(
        self,
        mode: ConversationMode,
        domain: Optional[ConversationDomain],
        user_roles: List[str]
    ) -> str:
        """Build system prompt based on mode, domain, and user roles"""
        
        role_context = self._get_role_context(user_roles)
        
        base_prompt = f"""You are a Conversational Policy Intelligence Assistant for HealthForesight, an enterprise healthcare policy management platform.

Your role is to translate natural language into structured system actions. You are NOT autonomous - you generate proposals that go through existing workflows and approvals.

USER CONTEXT:
- Roles: {', '.join(user_roles)}
- Permissions: {role_context}

MODE: {mode.value}
"""
        
        if domain:
            base_prompt += f"DOMAIN: {domain.value}\n"
        
        if mode == ConversationMode.DRAFT:
            base_prompt += """
Your task is to:
1. Parse user intent
2. Ask clarifying questions ONLY if critical information is missing
3. Generate structured configurations (policies, pipelines, baselines)
4. Output in the required structured format
5. NEVER execute actions - only propose drafts

OUTPUT FORMAT:
You must respond with a JSON object containing:
- natural_language: Human-readable explanation
- structured_output: The structured artifact (policy JSON, pipeline YAML, etc.)
- next_steps: Array of suggested actions (e.g., ["Review policy draft", "Submit for approval"])
- confidence: "HIGH", "MEDIUM", or "LOW"
- requires_clarification: boolean
- clarification_questions: Array of questions if clarification needed
"""
        
        elif mode == ConversationMode.EXPLAIN:
            base_prompt += """
Your task is to:
1. Explain system outputs using evidence
2. Reference observed impact results, baselines, models
3. Provide confidence scores and limitations
4. Cite sources (models, time windows, assumptions)

OUTPUT FORMAT:
- natural_language: Executive-ready explanation
- structured_output: Evidence breakdown with metrics, confidence intervals, limitations
- next_steps: Suggested follow-up actions
"""
        
        elif mode == ConversationMode.QUERY:
            base_prompt += """
Your task is to:
1. Translate natural language queries into system queries
2. Retrieve relevant data/models
3. Present results clearly
4. Never modify data - only query

OUTPUT FORMAT:
- natural_language: Query results explanation
- structured_output: Query results with data references
- next_steps: Suggested queries or actions
"""
        
        # Add domain-specific instructions
        if domain == ConversationDomain.POLICY:
            base_prompt += """
POLICY DOMAIN:
- Support policy creation and modification
- Generate policy JSON with scope, enforcement, levers, exceptions
- Handle complex policies (composite, nested, conditional)
- Always create as DRAFT status
"""
        
        elif domain == ConversationDomain.DATA:
            base_prompt += """
DATA DOMAIN:
- Support data onboarding and ingestion pipeline configuration
- Generate pipeline YAML/JSON specs
- Ask about frequency, format, schema
- NEVER deploy pipelines - only propose configs
"""
        
        elif domain == ConversationDomain.BASELINE:
            base_prompt += """
BASELINE DOMAIN:
- Support baseline creation and explanation
- Generate baseline configuration objects
- Explain what baselines are
- Propose time windows, exclusions, metrics
"""
        
        elif domain == ConversationDomain.IMPACT:
            base_prompt += """
IMPACT DOMAIN:
- Explain observed impact analysis results
- Reference Stage 4 observed impact models
- Compare predicted vs observed
- Provide evidence-based narratives
"""
        
        elif domain == ConversationDomain.GOVERNANCE:
            base_prompt += """
GOVERNANCE DOMAIN:
- Support policy lifecycle queries
- Translate queries into system queries
- Generate alerts and workflow actions
- NEVER bypass approvals
"""
        
        return base_prompt
    
    def _get_role_context(self, user_roles: List[str]) -> str:
        """Get role-based permission context"""
        permissions_summary = []
        for role in user_roles:
            role_perms = ROLE_PERMISSIONS.get(role, {})
            for resource, actions in role_perms.items():
                permissions_summary.append(f"{resource}: {', '.join(actions)}")
        
        return "; ".join(permissions_summary) if permissions_summary else "Read-only access"
    
    def _build_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Build context from conversation history"""
        if not conversation_history:
            return ""
        
        context_parts = []
        for msg in conversation_history[-10:]:  # Last 10 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Truncate long messages
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def _generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str,
        mode: ConversationMode,
        domain: Optional[ConversationDomain],
        user_roles: List[str],
        rag_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate structured response (fallback when LLM is not available)
        
        Uses rule-based parsing with RAG context enhancement.
        """
        
        # Check if this is a policy creation request
        if mode == ConversationMode.DRAFT and domain == ConversationDomain.POLICY:
            result = self._parse_policy_creation_prompt(user_prompt, user_roles)
            # Enhance with RAG context
            if rag_context and rag_context.get("policies"):
                similar = rag_context["policies"][:2]
                if similar:
                    result["natural_language"] += f"\n\nFound {len(similar)} similar policies for reference."
                    result["structured_output"]["similar_policies"] = [
                        {"id": p["id"], "name": p["name"]} for p in similar
                    ]
            return result
        
        # Check if this is a data pipeline request
        if mode == ConversationMode.DRAFT and domain == ConversationDomain.DATA:
            result = self._parse_data_pipeline_prompt(user_prompt, user_roles)
            # Enhance with RAG context
            if rag_context and rag_context.get("pipelines"):
                similar = rag_context["pipelines"][:2]
                if similar:
                    result["natural_language"] += f"\n\nFound {len(similar)} similar pipelines for reference."
            return result
        
        # Check if this is an explanation request
        if mode == ConversationMode.EXPLAIN:
            return self._parse_explanation_prompt(user_prompt, user_roles)
        
        # Check if this is a query request
        if mode == ConversationMode.QUERY:
            return self._parse_query_prompt(user_prompt, user_roles)
        
        # Default response
        return {
            "natural_language": "I understand your request. Let me help you with that.",
            "structured_output": {},
            "next_steps": ["Review the generated output", "Make any necessary edits"],
            "confidence": "MEDIUM",
            "requires_clarification": False,
            "clarification_questions": []
        }
    
    def _parse_policy_creation_prompt(self, prompt: str, user_roles: List[str]) -> Dict[str, Any]:
        """Parse policy creation prompt and generate structured policy"""
        
        # Extract key information using regex patterns
        policy_type_match = re.search(r'(prior auth|prior authorization|step therapy|site of care|quantity limit)', prompt, re.I)
        policy_type = "PRIOR AUTH"  # Default
        if policy_type_match:
            pt = policy_type_match.group(1).lower()
            if "prior auth" in pt:
                policy_type = "PRIOR AUTH"
            elif "step therapy" in pt:
                policy_type = "STEP THERAPY"
            elif "site of care" in pt:
                policy_type = "SITE OF CARE"
            elif "quantity limit" in pt:
                policy_type = "QUANTITY LIMIT"
        
        # Extract LOB
        lob_match = re.search(r'(commercial|medicare|medicaid|ma|medicare advantage)', prompt, re.I)
        lob = ["COMMERCIAL"]  # Default
        if lob_match:
            lob = [lob_match.group(1).upper().replace("MA", "MA").replace("MEDICARE ADVANTAGE", "MA")]
        
        # Extract geography
        geo_match = re.search(r'(texas|tx|florida|fl|california|ca|all states|nationwide)', prompt, re.I)
        markets = ["ALL"]  # Default
        if geo_match:
            geo = geo_match.group(1).lower()
            if "all" in geo or "nationwide" in geo:
                markets = ["ALL"]
            elif geo in ["tx", "texas"]:
                markets = ["TX"]
            elif geo in ["fl", "florida"]:
                markets = ["FL"]
            elif geo in ["ca", "california"]:
                markets = ["CA"]
        
        # Extract service/condition
        service_match = re.search(r'(mri|ct|imaging|surgery|therapy|drug)', prompt, re.I)
        service = service_match.group(1).upper() if service_match else "GENERAL"
        
        # Extract date
        date_match = re.search(r'(july 1|jul 1|2024|2025)', prompt, re.I)
        effective_date = "2025-01-01"  # Default
        if date_match:
            # Simple date parsing (in production, use proper date parser)
            effective_date = "2025-07-01" if "july" in date_match.group(1).lower() or "jul" in date_match.group(1).lower() else "2025-01-01"
        
        # Extract exceptions
        exceptions = []
        if re.search(r'exclud(e|ing).*oncology', prompt, re.I):
            exceptions.append("ONCOLOGY")
        if re.search(r'exclud(e|ing).*emergency', prompt, re.I):
            exceptions.append("EMERGENCY")
        
        # Generate structured policy
        policy_draft = {
            "action_type": "POLICY_DRAFT",
            "policy_name": f"{service} {policy_type} - {', '.join(markets)} {', '.join(lob)}",
            "policy_type": policy_type,
            "description": f"Policy created via conversational AI based on: {prompt[:100]}",
            "status": "DRAFT",
            "scope": {
                "lob": lob,
                "markets": markets,
                "network": ["IN"]
            },
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["PA_WORKFLOW"],
                "override_allowed": True
            },
            "policy_levers": [
                {
                    "lever_type": policy_type.replace(" ", "_"),
                    "parameters": {}
                }
            ],
            "exceptions": exceptions if exceptions else None,
            "effective_date": effective_date,
            "confidence": "DRAFT_ONLY"
        }
        
        return {
            "natural_language": f"I've created a draft {policy_type.lower()} policy for {', '.join(lob)} members in {', '.join(markets)}. The policy is set to take effect on {effective_date}. {'Exceptions have been added for: ' + ', '.join(exceptions) if exceptions else ''}Please review the policy details below and make any necessary adjustments before submitting for approval.",
            "structured_output": policy_draft,
            "next_steps": [
                "Review the policy draft",
                "Edit any details as needed",
                "Submit for approval"
            ],
            "confidence": "MEDIUM",
            "requires_clarification": False,
            "clarification_questions": []
        }
    
    def _parse_data_pipeline_prompt(self, prompt: str, user_roles: List[str]) -> Dict[str, Any]:
        """Parse data pipeline creation prompt"""
        
        # Extract source
        source_match = re.search(r'(s3|sftp|api|database|file)', prompt, re.I)
        source = source_match.group(1).upper() if source_match else "FILE"
        
        # Extract frequency
        freq_match = re.search(r'(daily|weekly|monthly|real.?time)', prompt, re.I)
        frequency = "WEEKLY"  # Default
        if freq_match:
            freq = freq_match.group(1).lower()
            if "daily" in freq:
                frequency = "DAILY"
            elif "weekly" in freq:
                frequency = "WEEKLY"
            elif "monthly" in freq:
                frequency = "MONTHLY"
            elif "real" in freq:
                frequency = "REAL_TIME"
        
        # Extract data type
        data_type_match = re.search(r'(claims|member|provider|enrollment|pharmacy)', prompt, re.I)
        data_type = data_type_match.group(1).upper() if data_type_match else "CLAIMS"
        
        pipeline_config = {
            "action_type": "PIPELINE_CONFIG",
            "pipeline_name": f"{data_type} Ingestion Pipeline - {source}",
            "source_type": source,
            "frequency": frequency,
            "data_type": data_type,
            "schema_mapping": {},
            "data_quality_checks": [],
            "status": "DRAFT"
        }
        
        return {
            "natural_language": f"I've created a draft ingestion pipeline configuration for {data_type.lower()} data from {source}. The pipeline is configured for {frequency.lower()} ingestion. Please review the configuration and specify the schema mapping and data quality checks before submitting.",
            "structured_output": pipeline_config,
            "next_steps": [
                "Review pipeline configuration",
                "Specify schema mapping",
                "Add data quality checks",
                "Submit to Data Ops queue"
            ],
            "confidence": "MEDIUM",
            "requires_clarification": True,
            "clarification_questions": [
                "What is the exact file format? (CSV, Parquet, JSON)",
                "What are the primary key fields?",
                "What date fields should be used for partitioning?",
                "What data quality rules should be applied?"
            ]
        }
    
    def _parse_explanation_prompt(self, prompt: str, user_roles: List[str]) -> Dict[str, Any]:
        """Parse explanation request"""
        
        return {
            "natural_language": "I'll analyze the observed impact results and provide an evidence-based explanation. Let me retrieve the relevant data and models.",
            "structured_output": {
                "action_type": "EXPLANATION_REQUEST",
                "query": prompt,
                "data_sources": ["observed_impact", "baseline", "predicted_impact"],
                "status": "PENDING"
            },
            "next_steps": [
                "Retrieve observed impact data",
                "Compare with baseline and predictions",
                "Generate evidence-based explanation"
            ],
            "confidence": "MEDIUM",
            "requires_clarification": False,
            "clarification_questions": []
        }
    
    def _parse_query_prompt(self, prompt: str, user_roles: List[str]) -> Dict[str, Any]:
        """Parse query request"""
        
        return {
            "natural_language": "I'll translate your query into system queries and retrieve the relevant information.",
            "structured_output": {
                "action_type": "QUERY",
                "query": prompt,
                "data_sources": [],
                "status": "PENDING"
            },
            "next_steps": [
                "Translate query to system queries",
                "Execute queries",
                "Present results"
            ],
            "confidence": "MEDIUM",
            "requires_clarification": False,
            "clarification_questions": []
        }

