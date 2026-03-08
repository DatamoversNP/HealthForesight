"""File-based storage for Conversational AI - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from uepi_api.models.conversational_ai import (
    Conversation,
    ConversationMessage,
    ConversationArtifact,
    ConversationAuditLog,
    ConversationMode,
    ConversationDomain,
    ConversationStatus,
)
from sqlalchemy import desc


def create_conversation(
    tenant_id: UUID,
    user_id: UUID,
    mode: ConversationMode,
    domain: Optional[ConversationDomain] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new conversation - stored in database"""
    return _create_conversation(tenant_id, user_id, mode, domain, title)


def _create_conversation(
    tenant_id: UUID,
    user_id: UUID,
    mode: ConversationMode,
    domain: Optional[ConversationDomain] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Create conversation in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        conversation_id = uuid4()
        
        conversation_db = Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=title or f"Conversation - {mode.value}",
            mode=mode.value,
            domain=domain.value if domain else None,
            status=ConversationStatus.ACTIVE.value,
        )
        
        db.add(conversation_db)
        db.commit()
        db.refresh(conversation_db)
        
        return {
            "id": str(conversation_db.id),
            "tenant_id": str(conversation_db.tenant_id),
            "user_id": str(conversation_db.user_id),
            "title": conversation_db.title,
            "mode": conversation_db.mode,
            "domain": conversation_db.domain,
            "status": conversation_db.status,
            "messages": [],
            "artifacts": [],
            "created_at": conversation_db.created_at.isoformat() if conversation_db.created_at else None,
            "updated_at": conversation_db.updated_at.isoformat() if conversation_db.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create conversation: {e}")
    finally:
        db.close()


def get_conversation(tenant_id: UUID, conversation_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a conversation by ID - from database"""
    return _get_conversation(tenant_id, conversation_id)


def _get_conversation(tenant_id: UUID, conversation_id: UUID) -> Optional[Dict[str, Any]]:
    """Get conversation from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        conversation_db = db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id,
            Conversation.id == conversation_id
        ).first()
        
        if not conversation_db:
            return None
        
        messages = []
        for msg_db in conversation_db.messages:
            messages.append({
                "id": str(msg_db.id),
                "role": msg_db.role,
                "content": msg_db.content,
                "structured_data": msg_db.structured_data,
                "message_metadata": msg_db.message_metadata,
                "metadata": msg_db.message_metadata,  # Backward compatibility
                "created_at": msg_db.created_at.isoformat() if msg_db.created_at else None,
            })
        
        artifacts = []
        for art_db in conversation_db.artifacts:
            artifacts.append({
                "id": str(art_db.id),
                "artifact_type": art_db.artifact_type,
                "artifact_data": art_db.artifact_data,
                "status": art_db.status,
                "workflow_entry_id": str(art_db.workflow_entry_id) if art_db.workflow_entry_id else None,
                "created_at": art_db.created_at.isoformat() if art_db.created_at else None,
                "updated_at": art_db.updated_at.isoformat() if art_db.updated_at else None,
            })
        
        return {
            "id": str(conversation_db.id),
            "tenant_id": str(conversation_db.tenant_id),
            "user_id": str(conversation_db.user_id),
            "title": conversation_db.title,
            "mode": conversation_db.mode,
            "domain": conversation_db.domain,
            "status": conversation_db.status,
            "messages": messages,
            "artifacts": artifacts,
            "created_at": conversation_db.created_at.isoformat() if conversation_db.created_at else None,
            "updated_at": conversation_db.updated_at.isoformat() if conversation_db.updated_at else None,
        }
        
    except Exception as e:
        print(f"ERROR get_conversation (DB): {e}")
        return None
    finally:
        db.close()


def list_conversations(
    tenant_id: UUID,
    user_id: Optional[UUID] = None,
    status: Optional[ConversationStatus] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """List conversations for a tenant - from database"""
    return _list_conversations(tenant_id, user_id, status, limit)


def _list_conversations(
    tenant_id: UUID,
    user_id: Optional[UUID] = None,
    status: Optional[ConversationStatus] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """List conversations from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(Conversation).filter(Conversation.tenant_id == tenant_id)
        
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        
        if status:
            query = query.filter(Conversation.status == status.value)
        
        conversations_db = query.order_by(desc(Conversation.updated_at)).limit(limit).all()
        
        result = []
        for conversation_db in conversations_db:
            messages = []
            for msg_db in conversation_db.messages:
                messages.append({
                    "id": str(msg_db.id),
                    "role": msg_db.role,
                    "content": msg_db.content,
                    "structured_data": msg_db.structured_data,
                    "message_metadata": msg_db.message_metadata,
                    "metadata": msg_db.message_metadata,
                    "created_at": msg_db.created_at.isoformat() if msg_db.created_at else None,
                })
            
            artifacts = []
            for art_db in conversation_db.artifacts:
                artifacts.append({
                    "id": str(art_db.id),
                    "artifact_type": art_db.artifact_type,
                    "artifact_data": art_db.artifact_data,
                    "status": art_db.status,
                    "workflow_entry_id": str(art_db.workflow_entry_id) if art_db.workflow_entry_id else None,
                    "created_at": art_db.created_at.isoformat() if art_db.created_at else None,
                    "updated_at": art_db.updated_at.isoformat() if art_db.updated_at else None,
                })
            
            result.append({
                "id": str(conversation_db.id),
                "tenant_id": str(conversation_db.tenant_id),
                "user_id": str(conversation_db.user_id),
                "title": conversation_db.title,
                "mode": conversation_db.mode,
                "domain": conversation_db.domain,
                "status": conversation_db.status,
                "messages": messages,
                "artifacts": artifacts,
                "created_at": conversation_db.created_at.isoformat() if conversation_db.created_at else None,
                "updated_at": conversation_db.updated_at.isoformat() if conversation_db.updated_at else None,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_conversations (DB): {e}")
        return []
    finally:
        db.close()


def add_message(
    tenant_id: UUID,
    conversation_id: UUID,
    role: str,
    content: str,
    structured_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Add a message to a conversation - stored in database"""
    return _add_message(tenant_id, conversation_id, role, content, structured_data, metadata)


def _add_message(
    tenant_id: UUID,
    conversation_id: UUID,
    role: str,
    content: str,
    structured_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Add message to conversation in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        conversation_db = db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id,
            Conversation.id == conversation_id
        ).first()
        
        if not conversation_db:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        message_db = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            structured_data=structured_data,
            message_metadata=metadata,
        )
        
        db.add(message_db)
        
        if not conversation_db.title or conversation_db.title.startswith("Conversation -"):
            if role == "user" and len(conversation_db.messages) == 0:
                conversation_db.title = content[:50] + ("..." if len(content) > 50 else "")
        
        db.commit()
        db.refresh(message_db)
        
        return {
            "id": str(message_db.id),
            "role": message_db.role,
            "content": message_db.content,
            "structured_data": message_db.structured_data,
            "message_metadata": message_db.message_metadata,
            "metadata": message_db.message_metadata,
            "created_at": message_db.created_at.isoformat() if message_db.created_at else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to add message: {e}")
    finally:
        db.close()


def create_artifact(
    tenant_id: UUID,
    conversation_id: UUID,
    artifact_type: str,
    artifact_data: Dict[str, Any],
    workflow_entry_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Create an artifact from a conversation - stored in database"""
    return _create_artifact(tenant_id, conversation_id, artifact_type, artifact_data, workflow_entry_id)


def _create_artifact(
    tenant_id: UUID,
    conversation_id: UUID,
    artifact_type: str,
    artifact_data: Dict[str, Any],
    workflow_entry_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Create artifact in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        conversation_db = db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id,
            Conversation.id == conversation_id
        ).first()
        
        if not conversation_db:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        artifact_db = ConversationArtifact(
            conversation_id=conversation_id,
            artifact_type=artifact_type,
            artifact_data=artifact_data,
            status="DRAFT",
            workflow_entry_id=workflow_entry_id,
        )
        
        db.add(artifact_db)
        db.commit()
        db.refresh(artifact_db)
        
        return {
            "id": str(artifact_db.id),
            "artifact_type": artifact_db.artifact_type,
            "artifact_data": artifact_db.artifact_data,
            "status": artifact_db.status,
            "workflow_entry_id": str(artifact_db.workflow_entry_id) if artifact_db.workflow_entry_id else None,
            "created_at": artifact_db.created_at.isoformat() if artifact_db.created_at else None,
            "updated_at": artifact_db.updated_at.isoformat() if artifact_db.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create artifact: {e}")
    finally:
        db.close()


def log_audit_event(
    tenant_id: UUID,
    user_id: UUID,
    user_roles: List[str],
    action_type: str,
    conversation_id: Optional[UUID] = None,
    prompt: Optional[str] = None,
    ai_response: Optional[str] = None,
    structured_output: Optional[Dict[str, Any]] = None,
    generated_artifacts: Optional[List[UUID]] = None,
    downstream_workflow_entry: Optional[UUID] = None
) -> Dict[str, Any]:
    """Log an audit event for conversational AI - stored in database"""
    return _log_audit_event(tenant_id, user_id, user_roles, action_type, conversation_id, prompt, ai_response, structured_output, generated_artifacts, downstream_workflow_entry)


def _log_audit_event(
    tenant_id: UUID,
    user_id: UUID,
    user_roles: List[str],
    action_type: str,
    conversation_id: Optional[UUID] = None,
    prompt: Optional[str] = None,
    ai_response: Optional[str] = None,
    structured_output: Optional[Dict[str, Any]] = None,
    generated_artifacts: Optional[List[UUID]] = None,
    downstream_workflow_entry: Optional[UUID] = None
) -> Dict[str, Any]:
    """Log audit event in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        audit_log_db = ConversationAuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            user_roles=user_roles,
            conversation_id=conversation_id,
            action_type=action_type,
            prompt=prompt,
            ai_response=ai_response,
            structured_output=structured_output,
            generated_artifacts=[str(aid) for aid in (generated_artifacts or [])],
            downstream_workflow_entry=downstream_workflow_entry,
        )
        
        db.add(audit_log_db)
        db.commit()
        db.refresh(audit_log_db)
        
        return {
            "id": str(audit_log_db.id),
            "tenant_id": str(audit_log_db.tenant_id),
            "user_id": str(audit_log_db.user_id),
            "user_roles": audit_log_db.user_roles,
            "conversation_id": str(audit_log_db.conversation_id) if audit_log_db.conversation_id else None,
            "action_type": audit_log_db.action_type,
            "prompt": audit_log_db.prompt,
            "ai_response": audit_log_db.ai_response,
            "structured_output": audit_log_db.structured_output,
            "generated_artifacts": audit_log_db.generated_artifacts,
            "downstream_workflow_entry": str(audit_log_db.downstream_workflow_entry) if audit_log_db.downstream_workflow_entry else None,
            "timestamp": audit_log_db.timestamp.isoformat() if audit_log_db.timestamp else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to log audit event: {e}")
    finally:
        db.close()
