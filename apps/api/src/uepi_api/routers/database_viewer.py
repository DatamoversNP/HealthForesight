"""Database Viewer API - For inspecting database tables and data"""
from typing import List, Dict, Any, Optional, Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.database import get_db, Base, get_engine

router = APIRouter()


@router.get("/database/tables")
async def list_tables(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List all database tables"""
    try:
        inspector = inspect(get_engine())
        tables = inspector.get_table_names()
        
        result = []
        for table_name in sorted(tables):
            # Get row count
            try:
                count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.scalar() or 0
            except Exception:
                row_count = None
            
            result.append({
                "name": table_name,
                "row_count": row_count,
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tables: {str(e)}")


@router.get("/database/tables/{table_name}/schema")
async def get_table_schema(
    table_name: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get schema information for a table"""
    try:
        inspector = inspect(get_engine())
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        # Get columns
        columns = inspector.get_columns(table_name)
        column_info = []
        for col in columns:
            column_info.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default", "")) if col.get("default") else None,
                "primary_key": col.get("primary_key", False),
            })
        
        # Get primary keys
        pk_constraint = inspector.get_pk_constraint(table_name)
        primary_keys = pk_constraint.get("constrained_columns", []) if pk_constraint else []
        
        # Get foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name)
        fk_info = []
        for fk in foreign_keys:
            fk_info.append({
                "column": fk["constrained_columns"][0] if fk["constrained_columns"] else None,
                "referenced_table": fk["referred_table"],
                "referenced_column": fk["referred_columns"][0] if fk["referred_columns"] else None,
            })
        
        # Get indexes
        indexes = inspector.get_indexes(table_name)
        index_info = []
        for idx in indexes:
            index_info.append({
                "name": idx["name"],
                "columns": idx["column_names"],
                "unique": idx.get("unique", False),
            })
        
        return {
            "table_name": table_name,
            "columns": column_info,
            "primary_keys": primary_keys,
            "foreign_keys": fk_info,
            "indexes": index_info,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table schema: {str(e)}")


@router.get("/database/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of rows to return"),
    offset: int = Query(0, ge=0, description="Number of rows to skip"),
    order_by: Optional[str] = Query(None, description="Column to order by (e.g., 'id DESC')"),
) -> Dict[str, Any]:
    """Get data from a table with pagination"""
    try:
        inspector = inspect(get_engine())
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        # Get total count
        count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        total_count = count_result.scalar() or 0
        
        # Build query
        query = f"SELECT * FROM {table_name}"
        
        # Add ordering
        if order_by:
            # Sanitize order_by to prevent SQL injection
            # Only allow alphanumeric, underscore, space, comma, and DESC/ASC
            import re
            if re.match(r'^[a-zA-Z0-9_,\s]+(?: DESC| ASC)?$', order_by, re.IGNORECASE):
                query += f" ORDER BY {order_by}"
            else:
                raise HTTPException(status_code=400, detail="Invalid order_by parameter")
        else:
            # Default ordering by first primary key or first column
            pk_constraint = inspector.get_pk_constraint(table_name)
            if pk_constraint and pk_constraint.get("constrained_columns"):
                query += f" ORDER BY {pk_constraint['constrained_columns'][0]}"
            else:
                columns = inspector.get_columns(table_name)
                if columns:
                    query += f" ORDER BY {columns[0]['name']}"
        
        # Add pagination
        query += f" LIMIT {limit} OFFSET {offset}"
        
        # Execute query
        result = db.execute(text(query))
        rows = result.fetchall()
        
        # Get column names
        columns = [col[0] for col in result.keys()] if hasattr(result, 'keys') else []
        if not columns:
            columns = [desc[0] for desc in result.description] if result.description else []
        
        # Convert rows to dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, col_name in enumerate(columns):
                value = row[i] if isinstance(row, (tuple, list)) else getattr(row, col_name, None)
                # Convert UUID and datetime to strings for JSON serialization
                if isinstance(value, UUID):
                    value = str(value)
                elif hasattr(value, 'isoformat'):  # datetime, date
                    value = value.isoformat()
                row_dict[col_name] = value
            data.append(row_dict)
        
        return {
            "table_name": table_name,
            "data": data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table data: {str(e)}")


@router.get("/database/tables/{table_name}/count")
async def get_table_count(
    table_name: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get row count for a table"""
    try:
        inspector = inspect(get_engine())
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = count_result.scalar() or 0
        
        return {
            "table_name": table_name,
            "count": count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table count: {str(e)}")
