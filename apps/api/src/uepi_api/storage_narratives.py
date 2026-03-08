"""
Epic 7: Executive Narrative Layer - Storage Module
Database only
"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.analysis import AnalysisNarrative as AnalysisNarrativeDB
from sqlalchemy import desc
from uepi_common.models_enhanced import (
    NarrativeMode,
    ExportTemplate,
    ExportPack,
    ResourceType,
)


def _safe_uuid(value: Any) -> Optional[UUID]:
    """Safely convert value to UUID"""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return UUID(value)
        except (ValueError, AttributeError):
            return None
    return None


# Narratives
def create_narrative(
    tenant_id: UUID,
    narrative_data: Dict[str, Any]
) -> NarrativeMode:
    """Create a new narrative - stored in database"""
    return _create_narrative(tenant_id, narrative_data)


def _create_narrative(
    tenant_id: UUID,
    narrative_data: Dict[str, Any]
) -> NarrativeMode:
    """Create narrative in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        narrative_id = _safe_uuid(narrative_data.get("narrative_id")) or uuid4()
        resource_id = _safe_uuid(narrative_data.get("resource_id")) or uuid4()
        generated_by = _safe_uuid(narrative_data.get("generated_by")) or uuid4()
        generated_at = datetime.fromisoformat(narrative_data["generated_at"].replace("Z", "+00:00")) if isinstance(narrative_data.get("generated_at"), str) else narrative_data.get("generated_at", datetime.utcnow())
        
        content_md = f"""# Executive Summary

{narrative_data.get("executive_summary", "")}

## Key Findings

{chr(10).join([f"- {finding}" for finding in narrative_data.get("key_findings", [])])}

## Risks

{chr(10).join([f"- {risk}" for risk in narrative_data.get("risks", [])])}

## Recommended Action

{narrative_data.get("recommended_action", "")}
"""
        
        narrative_db = AnalysisNarrativeDB(
            tenant_id=tenant_id,
            id=narrative_id,
            analysis_id=resource_id,
            version=1,
            content_md=content_md,
            generated_by="SYSTEM",
            locked="false",
            created_by=generated_by,
        )
        
        db.add(narrative_db)
        db.commit()
        db.refresh(narrative_db)
        
        return NarrativeMode(
            narrative_id=narrative_id,
            resource_type=ResourceType(narrative_data.get("resource_type", "POLICY")),
            resource_id=resource_id,
            executive_summary=narrative_data.get("executive_summary", ""),
            key_findings=narrative_data.get("key_findings", []),
            risks=narrative_data.get("risks", []),
            recommended_action=narrative_data.get("recommended_action", ""),
            generated_at=generated_at,
            generated_by=generated_by,
        )
        
    except Exception as e:
        db.rollback()
        print(f"ERROR create_narrative (DB): {e}")
        raise ValueError(f"Failed to create narrative: {e}")
    finally:
        db.close()


def get_narrative(
    tenant_id: UUID,
    narrative_id: UUID
) -> Optional[NarrativeMode]:
    """Get narrative - from database"""
    return _get_narrative(tenant_id, narrative_id)


def _get_narrative(
    tenant_id: UUID,
    narrative_id: UUID
) -> Optional[NarrativeMode]:
    """Get narrative from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        narrative_db = db.query(AnalysisNarrativeDB).filter(
            AnalysisNarrativeDB.tenant_id == tenant_id,
            AnalysisNarrativeDB.id == narrative_id
        ).first()
        
        if not narrative_db:
            return None
        
        content_md = narrative_db.content_md or ""
        
        executive_summary = ""
        key_findings = []
        risks = []
        recommended_action = ""
        
        lines = content_md.split("\n")
        current_section = None
        for line in lines:
            if line.startswith("# Executive Summary"):
                current_section = "executive_summary"
            elif line.startswith("## Key Findings"):
                current_section = "key_findings"
            elif line.startswith("## Risks"):
                current_section = "risks"
            elif line.startswith("## Recommended Action"):
                current_section = "recommended_action"
            elif line.strip() and not line.startswith("#"):
                if current_section == "executive_summary":
                    executive_summary += line.strip() + " "
                elif current_section == "key_findings" and line.strip().startswith("-"):
                    key_findings.append(line.strip()[1:].strip())
                elif current_section == "risks" and line.strip().startswith("-"):
                    risks.append(line.strip()[1:].strip())
                elif current_section == "recommended_action":
                    recommended_action += line.strip() + " "
        
        return NarrativeMode(
            narrative_id=narrative_db.id,
            resource_type=ResourceType("POLICY"),
            resource_id=narrative_db.analysis_id,
            executive_summary=executive_summary.strip(),
            key_findings=key_findings,
            risks=risks,
            recommended_action=recommended_action.strip(),
            generated_at=narrative_db.created_at if narrative_db.created_at else datetime.utcnow(),
            generated_by=narrative_db.created_by or uuid4(),
        )
        
    except Exception as e:
        print(f"ERROR get_narrative (DB): {e}")
        return None
    finally:
        db.close()


def list_narratives(
    tenant_id: UUID,
    resource_type: Optional[ResourceType] = None,
    resource_id: Optional[UUID] = None
) -> List[NarrativeMode]:
    """List narratives - from database"""
    return _list_narratives(tenant_id, resource_type, resource_id)


def _list_narratives(
    tenant_id: UUID,
    resource_type: Optional[ResourceType] = None,
    resource_id: Optional[UUID] = None
) -> List[NarrativeMode]:
    """List narratives from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(AnalysisNarrativeDB).filter(
            AnalysisNarrativeDB.tenant_id == tenant_id
        )
        
        if resource_id:
            query = query.filter(AnalysisNarrativeDB.analysis_id == resource_id)
        
        narratives_db = query.order_by(desc(AnalysisNarrativeDB.created_at)).all()
        
        result = []
        for narrative_db in narratives_db:
            content_md = narrative_db.content_md or ""
            
            executive_summary = ""
            key_findings = []
            risks = []
            recommended_action = ""
            
            lines = content_md.split("\n")
            current_section = None
            for line in lines:
                if line.startswith("# Executive Summary"):
                    current_section = "executive_summary"
                elif line.startswith("## Key Findings"):
                    current_section = "key_findings"
                elif line.startswith("## Risks"):
                    current_section = "risks"
                elif line.startswith("## Recommended Action"):
                    current_section = "recommended_action"
                elif line.strip() and not line.startswith("#"):
                    if current_section == "executive_summary":
                        executive_summary += line.strip() + " "
                    elif current_section == "key_findings" and line.strip().startswith("-"):
                        key_findings.append(line.strip()[1:].strip())
                    elif current_section == "risks" and line.strip().startswith("-"):
                        risks.append(line.strip()[1:].strip())
                    elif current_section == "recommended_action":
                        recommended_action += line.strip() + " "
            
            if resource_id and narrative_db.analysis_id != resource_id:
                continue
            
            result.append(NarrativeMode(
                narrative_id=narrative_db.id,
                resource_type=ResourceType("POLICY"),
                resource_id=narrative_db.analysis_id,
                executive_summary=executive_summary.strip(),
                key_findings=key_findings,
                risks=risks,
                recommended_action=recommended_action.strip(),
                generated_at=narrative_db.created_at if narrative_db.created_at else datetime.utcnow(),
                generated_by=narrative_db.created_by or uuid4(),
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_narratives (DB): {e}")
        return []
    finally:
        db.close()


# Export Templates - delegate to storage_exports
def create_export_template(
    tenant_id: UUID,
    template_data: Dict[str, Any]
) -> ExportTemplate:
    """Create a new export template - stored in database"""
    from uepi_api.storage_exports import create_export_template as _create_export_template_db
    return _create_export_template_db(tenant_id, template_data)


def get_export_template(
    tenant_id: UUID,
    template_type: str
) -> Optional[ExportTemplate]:
    """Get export template - from database"""
    from uepi_api.storage_exports import get_export_template as _get_export_template_db
    return _get_export_template_db(tenant_id, template_type)


# Export Packs - delegate to storage_exports
def create_export_pack(
    tenant_id: UUID,
    pack_data: Dict[str, Any]
) -> ExportPack:
    """Create a new export pack - stored in database"""
    from uepi_api.storage_exports import create_export_pack as _create_export_pack_db
    return _create_export_pack_db(tenant_id, pack_data)


def get_export_pack(
    tenant_id: UUID,
    export_id: UUID
) -> Optional[ExportPack]:
    """Get export pack - from database"""
    from uepi_api.storage_exports import get_export_pack as _get_export_pack_db
    return _get_export_pack_db(tenant_id, export_id)


def list_export_packs(
    tenant_id: UUID,
    resource_id: Optional[UUID] = None,
    template_type: Optional[str] = None
) -> List[ExportPack]:
    """List export packs - from database"""
    from uepi_api.storage_exports import list_export_packs as _list_export_packs_db
    return _list_export_packs_db(tenant_id, resource_id, template_type)




