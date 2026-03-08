"""Export endpoints - File storage implementation"""
from typing import Annotated, Optional
from uuid import UUID
from pathlib import Path
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

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


class ExportCreate(BaseModel):
    """Export creation model"""
    analysis_id: str  # Analysis ID
    export_type: str = "PDF"  # PDF, PPTX, AUDIT_PACK
    parent_export_id: Optional[str] = None
    change_description: Optional[str] = None


@router.post("/exports", status_code=201)
async def create_export(
    export_data: ExportCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create export - File storage implementation"""
    try:
        # Validate analysis exists
        analysis = get_analysis(UUID(export_data.analysis_id), current_user.tenant_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.get("status") != "COMPLETED":
            raise HTTPException(status_code=400, detail=f"Analysis not completed. Status: {analysis.get('status')}")
        
        # Create export record
        export = create_export_storage(
            tenant_id=current_user.tenant_id,
            export_data={
                "analysis_id": export_data.analysis_id,
                "export_type": export_data.export_type,
                "parent_export_id": export_data.parent_export_id,
                "change_description": export_data.change_description,
                "created_by": str(current_user.user_id) if hasattr(current_user, 'user_id') else None,
            },
        )
        
        # Update status to PROCESSING
        update_export_storage(
            export_id=UUID(export["id"]),
            tenant_id=current_user.tenant_id,
            updates={"status": "PROCESSING"},
        )
        
        # Generate export file asynchronously (simplified - generate immediately)
        try:
            # Get analysis results
            result_index = get_result_index(
                UUID(export_data.analysis_id),
                current_user.tenant_id,
                result_type="impact_result",
            )
            
            if not result_index:
                # Try other result types
                result_index = get_result_index(
                    UUID(export_data.analysis_id),
                    current_user.tenant_id,
                    result_type=None,  # Get any result
                )
            
            analysis_results = {}
            if result_index:
                data_uri = result_index.get("data_uri", "")
                if data_uri.startswith("file://"):
                    file_path = Path(data_uri.replace("file://", ""))
                    if file_path.exists():
                        with open(file_path, 'r') as f:
                            analysis_results = json.load(f)
            
            # Generate export file
            from uepi_api.routers.exports_file import generate_export_file
            
            file_bytes, file_ext = await generate_export_file(
                export_type=export_data.export_type,
                tenant_id=current_user.tenant_id,
                analysis_id=UUID(export_data.analysis_id),
                analysis_results=analysis_results,
            )
            
            # Save file to exports directory
            import os
            STORAGE_PATH = os.getenv("STORAGE_PATH", "./data")
            exports_dir = Path(STORAGE_PATH) / "exports" / str(current_user.tenant_id) / "files"
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            export_file_path = exports_dir / f"{export['id']}.{file_ext}"
            with open(export_file_path, 'wb') as f:
                f.write(file_bytes)
            
            # Update export with file info
            update_export_storage(
                export_id=UUID(export["id"]),
                tenant_id=current_user.tenant_id,
                updates={
                    "status": "COMPLETED",
                    "file_uri": f"file://{export_file_path}",
                    "file_size_bytes": len(file_bytes),
                    "completed_at": None,  # Will be set by update_export
                },
            )
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error generating export: {e}")
            print(f"Traceback: {error_trace}")
            
            update_export_storage(
                export_id=UUID(export["id"]),
                tenant_id=current_user.tenant_id,
                updates={
                    "status": "FAILED",
                    "error_message": str(e),
                },
            )
            
            raise HTTPException(status_code=500, detail=f"Failed to generate export: {str(e)}")
        
        # Reload export to get completed_at
        export = get_export_storage(UUID(export["id"]), current_user.tenant_id)
        
        return export
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create export: {str(e)}")


@router.get("/exports")
async def list_exports(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List exports - File storage implementation"""
    try:
        exports = list_exports_storage(current_user.tenant_id)
        # Apply pagination
        exports = exports[skip:skip+limit]
        return exports
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list exports: {str(e)}")


@router.get("/exports/{export_id}")
async def get_export(
    export_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get export - File storage implementation"""
    try:
        export = get_export_storage(export_id, current_user.tenant_id)
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")
        return export
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get export: {str(e)}")


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Download export file"""
    try:
        export = get_export_storage(export_id, current_user.tenant_id)
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")
        
        if export.get("status") != "COMPLETED":
            raise HTTPException(status_code=400, detail=f"Export not completed. Status: {export.get('status')}")
        
        file_uri = export.get("file_uri")
        if not file_uri or not file_uri.startswith("file://"):
            raise HTTPException(status_code=404, detail="Export file not found")
        
        file_path = Path(file_uri.replace("file://", ""))
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Export file not found on disk")
        
        # Increment download count
        update_export_storage(
            export_id=export_id,
            tenant_id=current_user.tenant_id,
            updates={"download_count": export.get("download_count", 0) + 1},
        )
        
        # Determine content type
        export_type = export.get("export_type", "PDF")
        media_type = "application/pdf" if export_type in ["PDF", "AUDIT_PACK"] else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        
        # Item 10: Generate signed download URL (for file storage, use direct file path)
        # In production with S3, would generate presigned URL with expiration
        download_url = f"/api/v1/exports/{export_id}/download"
        
        # For file storage, return FileResponse directly
        # For S3, would return redirect to presigned URL
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=f"export_{export_id}.{file_path.suffix[1:]}",
            headers={
                "X-Download-URL": download_url,  # Include URL in headers for reference
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to download export: {str(e)}")


@router.get("/exports/{export_id}/versions")
async def get_export_versions_route(
    export_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get all versions of an export"""
    try:
        versions = get_export_versions(export_id, current_user.tenant_id)
        return versions
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get export versions: {str(e)}")


@router.post("/exports/{export_id}/versions")
async def create_export_version(
    export_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    change_description: str = Query(..., description="Description of changes in this version"),
):
    """Create a new version of an export"""
    try:
        parent_export = get_export_storage(export_id, current_user.tenant_id)
        if not parent_export:
            raise HTTPException(status_code=404, detail="Parent export not found")
        
        # Get analysis ID
        analysis_id = parent_export.get("analysis_id")
        if not analysis_id:
            raise HTTPException(status_code=400, detail="Parent export has no analysis_id")
        
        # Get max version number
        versions = get_export_versions(export_id, current_user.tenant_id)
        max_version = max((v.get("version_number", 1) for v in versions), default=1)
        
        # Create new export with incremented version
        new_export = create_export_storage(
            tenant_id=current_user.tenant_id,
            export_data={
                "analysis_id": analysis_id,
                "export_type": parent_export.get("export_type", "PDF"),
                "parent_export_id": str(export_id),
                "change_description": change_description,
                "version_number": max_version + 1,
                "created_by": str(current_user.user_id) if hasattr(current_user, 'user_id') else None,
            },
        )
        
        # Update status to PROCESSING
        update_export_storage(
            export_id=UUID(new_export["id"]),
            tenant_id=current_user.tenant_id,
            updates={"status": "PROCESSING"},
        )
        
        # Generate the export (same logic as create_export)
        try:
            # Get analysis results
            result_index = get_result_index(
                UUID(analysis_id),
                current_user.tenant_id,
                result_type="impact_result",
            )
            
            if not result_index:
                result_index = get_result_index(
                    UUID(analysis_id),
                    current_user.tenant_id,
                    result_type=None,
                )
            
            analysis_results = {}
            if result_index:
                data_uri = result_index.get("data_uri", "")
                if data_uri.startswith("file://"):
                    file_path = Path(data_uri.replace("file://", ""))
                    if file_path.exists():
                        with open(file_path, 'r') as f:
                            analysis_results = json.load(f)
            
            # Generate export file
            from uepi_api.routers.exports_file import generate_export_file
            
            file_bytes, file_ext = await generate_export_file(
                export_type=parent_export.get("export_type", "PDF"),
                tenant_id=current_user.tenant_id,
                analysis_id=UUID(analysis_id),
                analysis_results=analysis_results,
            )
            
            # Save file
            import os
            STORAGE_PATH = os.getenv("STORAGE_PATH", "./data")
            exports_dir = Path(STORAGE_PATH) / "exports" / str(current_user.tenant_id) / "files"
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            export_file_path = exports_dir / f"{new_export['id']}.{file_ext}"
            with open(export_file_path, 'wb') as f:
                f.write(file_bytes)
            
            # Update export with file info
            update_export_storage(
                export_id=UUID(new_export["id"]),
                tenant_id=current_user.tenant_id,
                updates={
                    "status": "COMPLETED",
                    "file_uri": f"file://{export_file_path}",
                    "file_size_bytes": len(file_bytes),
                },
            )
            
            # Reload to get completed_at
            new_export = get_export_storage(UUID(new_export["id"]), current_user.tenant_id)
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error generating export version: {e}")
            print(f"Traceback: {error_trace}")
            
            update_export_storage(
                export_id=UUID(new_export["id"]),
                tenant_id=current_user.tenant_id,
                updates={
                    "status": "FAILED",
                    "error_message": str(e),
                },
            )
            
            raise HTTPException(status_code=500, detail=f"Failed to generate export version: {str(e)}")
        
        return new_export
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create export version: {str(e)}")
