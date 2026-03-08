"""Conversational AI API router"""
from typing import Annotated, Optional, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import verify_token, CurrentUser
from uepi_api.models.conversational_ai import ConversationMode, ConversationDomain
from uepi_api.storage_conversational_ai import (
    create_conversation,
    get_conversation,
    list_conversations,
    add_message,
    create_artifact,
    log_audit_event
)
from uepi_api.services.conversational_ai_service import ConversationalAIService

router = APIRouter(prefix="/conversational-ai", tags=["Conversational AI"])

# Initialize service
ai_service = ConversationalAIService()


class ConversationCreate(BaseModel):
    """Create conversation request"""
    mode: ConversationMode
    domain: Optional[ConversationDomain] = None
    title: Optional[str] = None


class MessageCreate(BaseModel):
    """Create message request"""
    content: str
    conversation_id: UUID


class ConversationResponse(BaseModel):
    """Conversation response"""
    id: UUID
    tenant_id: UUID
    user_id: UUID
    title: str
    mode: str
    domain: Optional[str]
    status: str
    messages: List[dict]
    artifacts: List[dict]
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    role: str
    content: str
    structured_data: Optional[dict]
    metadata: Optional[dict]
    created_at: str


class AIResponse(BaseModel):
    """AI response"""
    natural_language: str
    structured_output: dict
    next_steps: List[str]
    confidence: str
    requires_clarification: bool
    clarification_questions: List[str]


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation_endpoint(
    conversation_data: ConversationCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Create a new conversation"""
    conversation = create_conversation(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        mode=conversation_data.mode,
        domain=conversation_data.domain,
        title=conversation_data.title
    )
    
    # Log audit event
    log_audit_event(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        user_roles=current_user.roles,
        action_type="CONVERSATION_CREATED",
        conversation_id=UUID(conversation["id"])
    )
    
    return conversation


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations_endpoint(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """List conversations for current user"""
    conversations = list_conversations(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        status=status,
        limit=limit
    )
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_endpoint(
    conversation_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get a conversation by ID"""
    conversation = get_conversation(current_user.tenant_id, conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check access
    if conversation["user_id"] != str(current_user.user_id):
        # Check if user has admin role
        if "POLICY_ADMIN" not in current_user.roles:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return conversation


@router.post("/conversations/{conversation_id}/messages", response_model=AIResponse)
async def send_message(
    conversation_id: UUID,
    message_data: MessageCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Send a message and get AI response"""
    
    # Get conversation
    conversation = get_conversation(current_user.tenant_id, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check access
    if conversation["user_id"] != str(current_user.user_id):
        if "POLICY_ADMIN" not in current_user.roles:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Add user message
    user_message = add_message(
        tenant_id=current_user.tenant_id,
        conversation_id=conversation_id,
        role="user",
        content=message_data.content
    )
    
    # Get conversation history
    history = conversation.get("messages", [])
    
    # Check rate limit
    from uepi_api.services.rate_limiter import RateLimiter
    rate_limiter = RateLimiter()
    allowed, error_msg = rate_limiter.check_rate_limit(current_user.user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail=error_msg)
    
    # Generate AI response
    mode = ConversationMode(conversation["mode"])
    domain = ConversationDomain(conversation["domain"]) if conversation.get("domain") else None
    
    ai_response = await ai_service.generate_response(
        prompt=message_data.content,
        mode=mode,
        domain=domain,
        user_roles=current_user.roles,
        tenant_id=current_user.tenant_id,
        conversation_history=history
    )
    
    # Track costs
    from uepi_api.services.cost_tracker import CostTracker
    from uepi_api.config import get_settings
    settings = get_settings()
    cost_tracker = CostTracker()
    
    if hasattr(ai_service.llm_client, 'last_token_usage') and ai_service.llm_client.last_token_usage:
        token_usage = ai_service.llm_client.last_token_usage
        model = settings.openai_model if settings.llm_provider == "openai" else settings.anthropic_model
        cost_tracker.track_request(
            user_id=current_user.user_id,
            provider=settings.llm_provider,
            model=model,
            input_tokens=token_usage.get("input_tokens", 0),
            output_tokens=token_usage.get("output_tokens", 0)
        )
    
    # Add AI message
    ai_message = add_message(
        tenant_id=current_user.tenant_id,
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response["natural_language"],
        structured_data=ai_response["structured_output"],
        metadata={
            "confidence": ai_response["confidence"],
            "requires_clarification": ai_response["requires_clarification"],
            "clarification_questions": ai_response["clarification_questions"]
        }
    )
    
    # Create artifact if structured output indicates one
    artifact = None
    if ai_response["structured_output"].get("action_type"):
        action_type = ai_response["structured_output"]["action_type"]
        if action_type in ["POLICY_DRAFT", "PIPELINE_CONFIG", "BASELINE_CONFIG"]:
            artifact = create_artifact(
                tenant_id=current_user.tenant_id,
                conversation_id=conversation_id,
                artifact_type=action_type,
                artifact_data=ai_response["structured_output"]
            )
    
    # Log audit event
    log_audit_event(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        user_roles=current_user.roles,
        action_type="MESSAGE_SENT",
        conversation_id=conversation_id,
        prompt=message_data.content,
        ai_response=ai_response["natural_language"],
        structured_output=ai_response["structured_output"],
        generated_artifacts=[UUID(artifact["id"])] if artifact else None
    )
    
    return ai_response


@router.post("/conversations/{conversation_id}/artifacts/{artifact_id}/submit")
async def submit_artifact(
    conversation_id: UUID,
    artifact_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Submit an artifact to workflow"""
    
    # Get conversation
    conversation = get_conversation(current_user.tenant_id, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Find artifact
    artifact = None
    for art in conversation.get("artifacts", []):
        if art["id"] == str(artifact_id):
            artifact = art
            break
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    if artifact["status"] != "DRAFT":
        raise HTTPException(status_code=400, detail="Artifact already submitted")
    
    # Route to appropriate workflow based on artifact type
    workflow_entry_id = None
    
    if artifact["artifact_type"] == "POLICY_DRAFT":
        # Route to policy creation workflow
        from uepi_api.storage_policies import create_policy
        try:
            policy_data = artifact["artifact_data"]
            # Convert to policy creation format
            created_policy = create_policy(
                tenant_id=current_user.tenant_id,
                policy_data=policy_data
            )
            workflow_entry_id = UUID(created_policy.get("id", created_policy.get("policy_id")))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to create policy: {str(e)}")
    
    elif artifact["artifact_type"] == "PIPELINE_CONFIG":
        # Route to pipeline creation workflow
        from uepi_api.storage_pipelines import create_pipeline
        try:
            pipeline_data = artifact["artifact_data"]
            # Convert artifact data to pipeline format
            pipeline_record = {
                "pipeline_name": pipeline_data.get("pipeline_name", "AI Generated Pipeline"),
                "source_type": pipeline_data.get("source_type", "FILE"),
                "frequency": pipeline_data.get("frequency", "DAILY"),
                "data_type": pipeline_data.get("data_type", "CLAIMS"),
                "schema_mapping": pipeline_data.get("schema_mapping", {}),
                "data_quality_checks": pipeline_data.get("data_quality_checks", []),
            }
            created_pipeline = create_pipeline(
                tenant_id=current_user.tenant_id,
                pipeline_data=pipeline_record
            )
            workflow_entry_id = UUID(created_pipeline.get("id"))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to create pipeline: {str(e)}")
    
    # Update artifact status in conversation
    for i, art in enumerate(conversation.get("artifacts", [])):
        if art["id"] == str(artifact_id):
            conversation["artifacts"][i]["status"] = "SUBMITTED"
            conversation["artifacts"][i]["workflow_entry_id"] = str(workflow_entry_id) if workflow_entry_id else None
            conversation["artifacts"][i]["updated_at"] = datetime.now(timezone.utc).isoformat()
            break
    
    # Save conversation
    from uepi_api.storage_conversational_ai import _get_conversation_file
    conversation_file = _get_conversation_file(current_user.tenant_id, conversation_id)
    with open(conversation_file, 'w') as f:
        import json
        json.dump(conversation, f, indent=2, default=str)
    
    # Log audit event
    log_audit_event(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        user_roles=current_user.roles,
        action_type="ARTIFACT_SUBMITTED",
        conversation_id=conversation_id,
        generated_artifacts=[artifact_id],
        downstream_workflow_entry=workflow_entry_id
    )
    
    return {
        "status": "submitted",
        "artifact_id": str(artifact_id),
        "workflow_entry_id": str(workflow_entry_id) if workflow_entry_id else None
    }


@router.get("/audit-logs")
async def get_audit_logs(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    limit: int = Query(100, ge=1, le=1000),
):
    """Get audit logs for conversational AI (admin only)"""
    
    if "POLICY_ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Load audit logs
    from pathlib import Path
    from datetime import datetime, timedelta
    import json
    
    audit_logs = []
    audit_dir = Path(f"data/conversation_audit_logs/{current_user.tenant_id}")
    
    if audit_dir.exists():
        # Get logs from last 7 days
        for i in range(7):
            date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            audit_file = audit_dir / f"audit-{date_str}.json"
            if audit_file.exists():
                try:
                    with open(audit_file, 'r') as f:
                        day_logs = json.load(f)
                        audit_logs.extend(day_logs)
                except Exception:
                    continue
    
    # Sort by timestamp descending
    audit_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return audit_logs[:limit]


@router.get("/rate-limit-status")
async def get_rate_limit_status(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get current rate limit status for user"""
    from uepi_api.services.rate_limiter import RateLimiter
    rate_limiter = RateLimiter()
    remaining = rate_limiter.get_remaining_requests(current_user.user_id)
    return {
        "remaining_minute": remaining["minute"],
        "remaining_hour": remaining["hour"],
        "limit_per_minute": rate_limiter.per_minute,
        "limit_per_hour": rate_limiter.per_hour
    }


@router.get("/costs")
async def get_costs(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    days: int = Query(30, ge=1, le=90),
):
    """Get cost tracking for user"""
    from uepi_api.services.cost_tracker import CostTracker
    from datetime import timedelta
    cost_tracker = CostTracker()
    
    # Users can only see their own costs unless admin
    if "POLICY_ADMIN" not in current_user.roles:
        return cost_tracker.get_user_costs(current_user.user_id, days)
    else:
        # Admin can see all costs
        daily_costs = []
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            costs = cost_tracker.get_daily_costs(date)
            daily_costs.append(costs)
        return {"daily_costs": daily_costs, "days": days}

