"""Export generation - File storage implementation"""
from typing import Annotated, Optional
from uuid import UUID
from pathlib import Path
import json
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_exports import (
    create_export as create_export_storage,
    get_export as get_export_storage,
    list_exports as list_exports_storage,
    update_export as update_export_storage,
    get_export_versions,
)
from uepi_api.storage_analyses import get_analysis, get_result_index

router = APIRouter()


async def generate_export_file(
    export_type: str,
    tenant_id: UUID,
    analysis_id: UUID,
    analysis_results: dict,
) -> tuple[bytes, str]:
    """
    Generate export file using worker generators
    
    Returns:
        Tuple of (file_bytes, file_extension)
    """
    import sys
    from pathlib import Path
    
    # Add worker to path
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root / "apps" / "worker" / "src"))
    
    try:
        from uepi_worker.exports import PDFGenerator, PPTXGenerator
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export generation not available: {str(e)}"
        )
    
    # Mock storage client for generators (not used for file storage)
    class MockStorageClient:
        pass
    
    file_bytes = None
    file_ext = None
    
    if export_type == "PDF" or export_type == "AUDIT_PACK":
        generator = PDFGenerator(MockStorageClient(), "mock-bucket")
        file_bytes = generator.generate_audit_pack_pdf(
            tenant_id=tenant_id,
            analysis_id=analysis_id,
            analysis_results=analysis_results,
        )
        file_ext = "pdf"
    elif export_type == "PPTX":
        generator = PPTXGenerator(MockStorageClient(), "mock-bucket")
        file_bytes = generator.generate_presentation_pptx(
            tenant_id=tenant_id,
            analysis_id=analysis_id,
            analysis_results=analysis_results,
        )
        file_ext = "pptx"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export type: {export_type}")
    
    return file_bytes, file_ext
