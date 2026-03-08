"""Data Explorer API - Browse files and folders, view data"""
from typing import Annotated, List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from pathlib import Path
import pandas as pd
import json

from uepi_api.auth import CurrentUser, get_demo_current_user
import os

router = APIRouter()

# Base data directory - resolve to project root data directory
# Calculate project root from current file location
current_file = Path(__file__).resolve()
# apps/api/src/uepi_api/routers/data_explorer.py -> project root
# Go up: routers (1) -> uepi_api (2) -> src (3) -> api (4) -> apps (5) -> project root (6)
project_root = current_file.parent.parent.parent.parent.parent.parent
DATA_BASE_PATH = (project_root / "data").resolve()


@router.get("/data-explorer/list")
async def list_files_and_folders(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    path: str = Query("", description="Relative path from data directory"),
    include_files: bool = Query(True, description="Include files in listing"),
    include_folders: bool = Query(True, description="Include folders in listing"),
):
    """List files and folders in the data directory"""
    try:
        # Handle empty path - list root data directory
        if not path or path == "":
            full_path = DATA_BASE_PATH.resolve()
            safe_path = Path(".")
        else:
            # Sanitize path to prevent directory traversal
            safe_path = Path(path)
            if ".." in str(safe_path) or safe_path.is_absolute():
                raise HTTPException(status_code=400, detail="Invalid path")
            
            full_path = (DATA_BASE_PATH / safe_path).resolve()
            
            # Ensure path is within DATA_BASE_PATH using relative_to
            try:
                full_path.relative_to(DATA_BASE_PATH.resolve())
            except ValueError:
                raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {full_path}")
        
        items = []
        
        if include_folders:
            for item in full_path.iterdir():
                if item.is_dir():
                    # Calculate relative path for the item
                    if path:
                        item_path = str(safe_path / item.name)
                    else:
                        item_path = item.name
                    items.append({
                        "name": item.name,
                        "type": "folder",
                        "path": item_path,
                        "size": None,
                    })
        
        if include_files:
            # First, get direct files in current directory
            for item in full_path.iterdir():
                if item.is_file() and item.suffix.lower() in ['.csv', '.parquet', '.json', '.xlsx', '.xls']:
                    size = item.stat().st_size
                    # Calculate relative path for the item
                    if path:
                        item_path = str(safe_path / item.name)
                    else:
                        item_path = item.name
                    items.append({
                        "name": item.name,
                        "type": "file",
                        "path": item_path,
                        "size": size,
                        "size_mb": round(size / (1024 * 1024), 2),
                        "extension": item.suffix.lower(),
                    })
            
            # Also check subdirectories recursively for target_data_model (to show tenant/dataset files)
            # Only do this if we're at the target_data_model root level
            if "target_data_model" in str(full_path) and (not path or path == "target_data_model"):
                try:
                    # Limit depth to avoid performance issues - only go 2 levels deep (tenant/dataset)
                    for subdir in full_path.iterdir():
                        if subdir.is_dir():
                            # Look for files in tenant subdirectories (one level deep)
                            for tenant_subdir in subdir.iterdir():
                                if tenant_subdir.is_dir():
                                    # Look for files in dataset subdirectories
                                    for subfile in tenant_subdir.iterdir():
                                        if subfile.is_file() and subfile.suffix.lower() in ['.csv', '.parquet', '.json', '.xlsx', '.xls']:
                                            # Calculate relative path
                                            rel_path = subfile.relative_to(DATA_BASE_PATH)
                                            size = subfile.stat().st_size
                                            items.append({
                                                "name": f"{subdir.name}/{tenant_subdir.name}/{subfile.name}",
                                                "type": "file",
                                                "path": str(rel_path),
                                                "size": size,
                                                "size_mb": round(size / (1024 * 1024), 2),
                                                "extension": subfile.suffix.lower(),
                                            })
                                elif tenant_subdir.is_file() and tenant_subdir.suffix.lower() in ['.csv', '.parquet', '.json', '.xlsx', '.xls']:
                                    # File directly in tenant directory
                                    rel_path = tenant_subdir.relative_to(DATA_BASE_PATH)
                                    size = tenant_subdir.stat().st_size
                                    items.append({
                                        "name": f"{subdir.name}/{tenant_subdir.name}",
                                        "type": "file",
                                        "path": str(rel_path),
                                        "size": size,
                                        "size_mb": round(size / (1024 * 1024), 2),
                                        "extension": tenant_subdir.suffix.lower(),
                                    })
                except Exception as e:
                    # If recursive search fails, just continue with direct files
                    pass
        
        # Sort: folders first, then files, both alphabetically
        items.sort(key=lambda x: (x["type"] != "folder", x["name"].lower()))
        
        # Calculate parent path
        if path and safe_path != Path("."):
            try:
                # Get parent relative to data directory
                parent_rel = safe_path.parent
                if parent_rel == Path("."):
                    parent_path = ""
                else:
                    parent_path = str(parent_rel)
            except:
                parent_path = None
        else:
            parent_path = None
        
        return {
            "path": path,
            "items": items,
            "parent_path": parent_path,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing directory: {str(e)}")


@router.get("/data-explorer/view")
async def view_file_data(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    path: str = Query(..., description="Relative path from data directory"),
    limit: int = Query(100, ge=1, le=1000, description="Number of rows to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """View data from a file"""
    try:
        # Sanitize path
        safe_path = Path(path)
        if ".." in str(safe_path) or safe_path.is_absolute():
            raise HTTPException(status_code=400, detail="Invalid path")
        
        full_path = DATA_BASE_PATH / safe_path
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not str(full_path).startswith(str(DATA_BASE_PATH.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Read file based on extension
        ext = full_path.suffix.lower()
        
        try:
            if ext == '.csv':
                df = pd.read_csv(full_path, nrows=limit + offset)
            elif ext == '.parquet':
                df = pd.read_parquet(full_path)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(full_path, nrows=limit + offset)
            elif ext == '.json':
                with open(full_path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    df = pd.DataFrame([data])
                else:
                    raise HTTPException(status_code=400, detail="Unsupported JSON structure")
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
            
            # Apply pagination
            if offset > 0:
                df = df.iloc[offset:]
            df = df.head(limit)
            
            # Replace NaN/None values with None (JSON-compliant)
            import numpy as np
            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
            df = df.where(pd.notnull(df), None)
            
            # Convert to records
            records = df.to_dict('records')
            # Ensure all NaN/Inf values are None (final cleanup)
            for record in records:
                for key, value in record.items():
                    if isinstance(value, (float, np.floating)):
                        if np.isnan(value) or np.isinf(value):
                            record[key] = None
                    elif pd.isna(value):
                        record[key] = None
            
            columns = list(df.columns)
            
            # Get total count (approximate for large files)
            total_count = len(df) + offset
            if ext == '.csv':
                # For CSV, try to get a better count
                try:
                    with open(full_path, 'r') as f:
                        total_count = sum(1 for line in f) - 1  # Subtract header
                except:
                    pass
            
            return {
                "path": path,
                "columns": columns,
                "rows": records,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "file_size": full_path.stat().st_size,
                "file_type": ext,
            }
        
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="File is empty")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error viewing file: {str(e)}")


@router.get("/data-explorer/preview")
async def preview_file(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    path: str = Query(..., description="Relative path from data directory"),
    rows: int = Query(10, ge=1, le=100, description="Number of preview rows"),
):
    """Get a quick preview of a file (first N rows)"""
    try:
        safe_path = Path(path)
        if ".." in str(safe_path) or safe_path.is_absolute():
            raise HTTPException(status_code=400, detail="Invalid path")
        
        full_path = (DATA_BASE_PATH / safe_path).resolve()
        
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Ensure path is within DATA_BASE_PATH using relative_to
        try:
            full_path.relative_to(DATA_BASE_PATH.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        ext = full_path.suffix.lower()
        
        if ext == '.csv':
            df = pd.read_csv(full_path, nrows=rows)
        elif ext == '.parquet':
            df = pd.read_parquet(full_path).head(rows)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(full_path, nrows=rows)
        elif ext == '.json':
            with open(full_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data[:rows])
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise HTTPException(status_code=400, detail="Unsupported JSON structure")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
        
        return {
            "path": path,
            "columns": list(df.columns),
            "rows": df.to_dict('records'),
            "row_count": len(df),
            "file_size": full_path.stat().st_size,
            "file_type": ext,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing file: {str(e)}")

