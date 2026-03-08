"""
Epic 7: Executive Narrative Layer - API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID

from uepi_api.auth import get_demo_current_user, CurrentUser
from uepi_api.storage_narratives import (
    create_narrative,
    get_narrative,
    list_narratives,
    create_export_template,
    get_export_template,
    create_export_pack,
    get_export_pack,
    list_export_packs,
)
from uepi_common.models_enhanced import ResourceType

router = APIRouter()


def convert_resource_id_to_uuid(resource_id: str, resource_type: Optional[str], tenant_id: UUID) -> Optional[UUID]:
    """Convert string resource ID to UUID - optimized (no expensive lookup)"""
    if not resource_id:
        return None
    # Try UUID first
    try:
        return UUID(resource_id)
    except ValueError:
        # Not a UUID - generate deterministic UUID (fast, no lookup)
        import hashlib
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return UUID(bytes=hashlib.md5(namespace.bytes + resource_id.encode()).digest())


# Narratives
@router.post("/narratives")
async def create_narrative_endpoint(
    narrative_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new narrative"""
    try:
        if "generated_by" not in narrative_data:
            narrative_data["generated_by"] = str(current_user.user_id)
        narrative = create_narrative(
            tenant_id=current_user.tenant_id,
            narrative_data=narrative_data,
        )
        return narrative.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create narrative: {str(e)}")


@router.get("/narratives")
async def list_narratives_endpoint(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List narratives"""
    try:
        rt = ResourceType(resource_type) if resource_type else None
        rid = convert_resource_id_to_uuid(resource_id, resource_type, current_user.tenant_id) if resource_id else None
        narratives = list_narratives(
            tenant_id=current_user.tenant_id,
            resource_type=rt,
            resource_id=rid,
        )
        return [n.model_dump(mode='json', exclude_none=True) for n in narratives]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list narratives: {str(e)}")


@router.get("/narratives/{narrative_id}")
async def get_narrative_endpoint(
    narrative_id: str,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Get narrative"""
    try:
        narrative_uuid = UUID(narrative_id)
        narrative = get_narrative(
            tenant_id=current_user.tenant_id,
            narrative_id=narrative_uuid,
        )
        if not narrative:
            raise HTTPException(status_code=404, detail="Narrative not found")
        return narrative.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid narrative ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get narrative: {str(e)}")


# Export Templates
@router.post("/export-templates")
async def create_export_template_endpoint(
    template_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new export template"""
    try:
        template = create_export_template(
            tenant_id=current_user.tenant_id,
            template_data=template_data,
        )
        return template.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create export template: {str(e)}")


@router.get("/export-templates/{template_type}")
async def get_export_template_endpoint(
    template_type: str,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Get export template"""
    try:
        template = get_export_template(
            tenant_id=current_user.tenant_id,
            template_type=template_type,
        )
        if not template:
            raise HTTPException(status_code=404, detail="Export template not found")
        return template.model_dump(mode='json', exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get export template: {str(e)}")


# Export Packs
@router.post("/export-packs")
async def create_export_pack_endpoint(
    pack_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new export pack"""
    try:
        if "generated_by" not in pack_data:
            pack_data["generated_by"] = str(current_user.user_id)
        pack = create_export_pack(
            tenant_id=current_user.tenant_id,
            pack_data=pack_data,
        )
        return pack.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create export pack: {str(e)}")


@router.get("/export-packs")
async def list_export_packs_endpoint(
    resource_id: Optional[str] = None,
    template_type: Optional[str] = None,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List export packs"""
    try:
        rid = UUID(resource_id) if resource_id else None
        packs = list_export_packs(
            tenant_id=current_user.tenant_id,
            resource_id=rid,
            template_type=template_type,
        )
        return [p.model_dump(mode='json', exclude_none=True) for p in packs]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resource ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list export packs: {str(e)}")


@router.get("/export-packs/{export_id}")
async def get_export_pack_endpoint(
    export_id: str,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Get export pack"""
    try:
        export_uuid = UUID(export_id)
        pack = get_export_pack(
            tenant_id=current_user.tenant_id,
            export_id=export_uuid,
        )
        if not pack:
            raise HTTPException(status_code=404, detail="Export pack not found")
        return pack.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid export ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get export pack: {str(e)}")

