"""File-based storage implementation (no database)"""
import json
import os
from pathlib import Path
from typing import Any, Optional, TypeVar, Generic, List, Dict
from uuid import UUID
from datetime import datetime
import threading

T = TypeVar('T')


class FileStorage(Generic[T]):
    """Generic file-based storage for JSON data"""
    
    def __init__(self, base_path: str, file_prefix: str = ""):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.file_prefix = file_prefix
        self._lock = threading.Lock()
        self.index_file = self.base_path / "index.json"
        self._ensure_index()
    
    def _ensure_index(self):
        """Ensure index file exists"""
        if not self.index_file.exists():
            with self._lock:
                with open(self.index_file, 'w') as f:
                    json.dump([], f)
    
    def _get_file_path(self, item_id: UUID) -> Path:
        """Get file path for an item"""
        return self.base_path / f"{self.file_prefix}{item_id}.json"
    
    def _read_index(self) -> List[str]:
        """Read index of all item IDs"""
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_index(self, item_ids: List[str]):
        """Write index of all item IDs"""
        with self._lock:
            with open(self.index_file, 'w') as f:
                json.dump(sorted(item_ids), f, indent=2)
    
    def _read_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _write_file(self, file_path: Path, data: Dict[str, Any]):
        """Write JSON file"""
        with self._lock:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    def _delete_file(self, file_path: Path):
        """Delete JSON file"""
        try:
            file_path.unlink()
        except FileNotFoundError:
            pass
    
    def create(self, item_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item"""
        file_path = self._get_file_path(item_id)
        if file_path.exists():
            raise ValueError(f"Item {item_id} already exists")
        
        # Add metadata
        data['id'] = str(item_id)
        data['created_at'] = datetime.utcnow().isoformat()
        data['updated_at'] = datetime.utcnow().isoformat()
        
        self._write_file(file_path, data)
        
        # Update index
        index = self._read_index()
        if str(item_id) not in index:
            index.append(str(item_id))
            self._write_index(index)
        
        return data
    
    def get(self, item_id: UUID) -> Optional[Dict[str, Any]]:
        """Get an item by ID"""
        file_path = self._get_file_path(item_id)
        return self._read_file(file_path)
    
    def update(self, item_id: UUID, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an item"""
        file_path = self._get_file_path(item_id)
        existing = self._read_file(file_path)
        if not existing:
            return None
        
        # Preserve ID and created_at
        data['id'] = str(item_id)
        data['created_at'] = existing.get('created_at')
        data['updated_at'] = datetime.utcnow().isoformat()
        
        self._write_file(file_path, data)
        return data
    
    def delete(self, item_id: UUID) -> bool:
        """Delete an item"""
        file_path = self._get_file_path(item_id)
        if not file_path.exists():
            return False
        
        self._delete_file(file_path)
        
        # Update index
        index = self._read_index()
        if str(item_id) in index:
            index.remove(str(item_id))
            self._write_index(index)
        
        return True
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all items - scans directory if index is empty"""
        index = self._read_index()
        items = []
        
        # If index is empty or very small, scan directory for existing files
        if len(index) == 0:
            # Scan directory for existing files
            for file_path in self.base_path.glob(f"{self.file_prefix}*.json"):
                if file_path.name == "index.json":
                    continue
                try:
                    # Try to extract ID from filename
                    filename = file_path.stem  # Remove .json
                    if self.file_prefix:
                        id_str = filename.replace(self.file_prefix, "")
                    else:
                        id_str = filename
                    try:
                        item_id = UUID(id_str)
                        item = self.get(item_id)
                        if item:
                            items.append(item)
                            # Add to index if not present
                            if id_str not in index:
                                index.append(id_str)
                    except ValueError:
                        # Not a valid UUID, skip
                        pass
                except Exception:
                    pass
            
            # Update index if we found files
            if items and len(index) > 0:
                self._write_index(index)
        else:
            # Use index as normal
            for item_id_str in index:
                try:
                    item_id = UUID(item_id_str)
                    item = self.get(item_id)
                    if item:
                        items.append(item)
                except (ValueError, AttributeError):
                    # Invalid UUID in index, skip
                    pass
        
        return items
    
    def find_by(self, **filters) -> List[Dict[str, Any]]:
        """Find items matching filters"""
        all_items = self.list_all()
        results = []
        for item in all_items:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                results.append(item)
        return results
    
    def find_one_by(self, **filters) -> Optional[Dict[str, Any]]:
        """Find one item matching filters"""
        results = self.find_by(**filters)
        return results[0] if results else None

