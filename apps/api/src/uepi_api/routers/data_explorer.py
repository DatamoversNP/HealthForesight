"""Data Explorer API - Browse files and folders, view data.

In database-only mode (USE_FILE_STORAGE=false), ``source_data`` / ``target_data_model`` list
PostgreSQL tables as virtual files (path prefix ``__db__/``) instead of on-disk folders.
"""
from decimal import Decimal
from typing import Annotated, Any, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from pathlib import Path
import pandas as pd
import json

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.database import USE_FILE_STORAGE, get_db, get_engine

router = APIRouter()

# Virtual paths for PostgreSQL-backed rows (no on-disk file)
DB_VIRTUAL_PREFIX = "__db__"

# Base data directory - resolve to project root data directory
# Calculate project root from current file location
current_file = Path(__file__).resolve()
# apps/api/src/uepi_api/routers/data_explorer.py -> project root
# Go up: routers (1) -> uepi_api (2) -> src (3) -> api (4) -> apps (5) -> project root (6)
project_root = current_file.parent.parent.parent.parent.parent.parent
DATA_BASE_PATH = (project_root / "data").resolve()


def _quote_table(engine, table_name: str) -> str:
    return engine.dialect.identifier_preparer.quote(table_name)


def _quote_col(engine, col_name: str) -> str:
    return engine.dialect.identifier_preparer.quote(col_name)


def _serialize_cell(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _parse_db_virtual_path(path: str) -> Optional[str]:
    if not path.startswith(f"{DB_VIRTUAL_PREFIX}/"):
        return None
    table = path[len(DB_VIRTUAL_PREFIX) + 1 :].strip()
    return table or None


def _db_virtual_listing(path: str) -> Optional[Dict[str, Any]]:
    """If path is served from PostgreSQL in DB-only mode, return listing payload; else None."""
    if USE_FILE_STORAGE:
        return None

    path = (path or "").strip()

    # Root: mirror legacy folder names so the SPA tabs keep working
    if path == "":
        return {
            "path": "",
            "items": [
                {"name": "source_data", "type": "folder", "path": "source_data", "size": None},
                {"name": "target_data_model", "type": "folder", "path": "target_data_model", "size": None},
            ],
            "parent_path": None,
        }

    if path in ("source_data", "target_data_model"):
        engine = get_engine()
        inspector = inspect(engine)
        tables = sorted(inspector.get_table_names())
        items = []
        for t in tables:
            items.append(
                {
                    "name": t,
                    "type": "file",
                    "path": f"{DB_VIRTUAL_PREFIX}/{t}",
                    "size": None,
                    "size_mb": None,
                    "extension": ".db",
                }
            )
        return {"path": path, "items": items, "parent_path": "" if path else None}

    if path.startswith("source_data/") or path.startswith("target_data_model/"):
        parent = path.rsplit("/", 1)[0] if "/" in path else path
        return {"path": path, "items": [], "parent_path": parent if parent != path else ""}

    return None


def _db_virtual_table_rows(
    db: Session,
    table_name: str,
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    engine = get_engine()
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail="Table not found")

    qtable = _quote_table(engine, table_name)
    count_result = db.execute(text(f"SELECT COUNT(*) FROM {qtable}"))
    total_count = int(count_result.scalar() or 0)

    query = f"SELECT * FROM {qtable}"
    pk_constraint = inspector.get_pk_constraint(table_name)
    if pk_constraint and pk_constraint.get("constrained_columns"):
        qc = _quote_col(engine, pk_constraint["constrained_columns"][0])
        query += f" ORDER BY {qc}"
    else:
        cols = inspector.get_columns(table_name)
        if cols:
            qc = _quote_col(engine, cols[0]["name"])
            query += f" ORDER BY {qc}"

    query += f" LIMIT {limit} OFFSET {offset}"

    result = db.execute(text(query))
    rows = result.fetchall()
    columns = list(result.keys()) if hasattr(result, "keys") else []
    if not columns and result.description:
        columns = [d[0] for d in result.description]

    records = []
    for row in rows:
        rec = {}
        for i, col_name in enumerate(columns):
            val = row[i] if isinstance(row, (tuple, list)) else getattr(row, col_name, None)
            rec[col_name] = _serialize_cell(val)
        records.append(rec)

    return {
        "path": f"{DB_VIRTUAL_PREFIX}/{table_name}",
        "columns": columns,
        "rows": records,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "file_size": 0,
        "file_type": ".db",
    }


@router.get("/data-explorer/list")
async def list_files_and_folders(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    path: str = Query("", description="Relative path from data directory"),
    include_files: bool = Query(True, description="Include files in listing"),
    include_folders: bool = Query(True, description="Include folders in listing"),
):
    """List files and folders in the data directory"""
    try:
        virtual = _db_virtual_listing(path)
        if virtual is not None:
            if not include_files:
                virtual = {
                    **virtual,
                    "items": [i for i in virtual["items"] if i["type"] == "folder"],
                }
            if not include_folders:
                virtual = {
                    **virtual,
                    "items": [i for i in virtual["items"] if i["type"] == "file"],
                }
            return virtual

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
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    path: str = Query(..., description="Relative path from data directory"),
    limit: int = Query(100, ge=1, le=5000, description="Number of rows to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """View data from a file"""
    try:
        table_name = _parse_db_virtual_path(path)
        if table_name:
            return _db_virtual_table_rows(db, table_name, limit, offset)

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
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    path: str = Query(..., description="Relative path from data directory"),
    rows: int = Query(10, ge=1, le=100, description="Number of preview rows"),
):
    """Get a quick preview of a file (first N rows)"""
    try:
        table_name = _parse_db_virtual_path(path)
        if table_name:
            data = _db_virtual_table_rows(db, table_name, rows, 0)
            return {
                "path": data["path"],
                "columns": data["columns"],
                "rows": data["rows"],
                "row_count": len(data["rows"]),
                "file_size": 0,
                "file_type": ".db",
            }

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

