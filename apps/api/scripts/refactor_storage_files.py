#!/usr/bin/env python3
"""
Script to help refactor storage_*.py files to remove file storage
This is a helper script - manual review and adjustment is still needed
"""
import re
from pathlib import Path

def refactor_storage_file(file_path: Path):
    """Refactor a storage file to remove file storage code"""
    content = file_path.read_text()
    
    # Remove file storage imports
    content = re.sub(r'from uepi_api\.storage_file import.*\n', '', content)
    content = re.sub(r'from uepi_api\.storage import.*\n', '', content)
    content = re.sub(r'import json\n', '', content)
    content = re.sub(r'from pathlib import Path\n', '', content)
    content = re.sub(r'from uepi_api\.database import USE_FILE_STORAGE\n', '', content)
    
    # Remove init_storage() calls
    content = re.sub(r'init_storage\(\)\n', '', content)
    
    # Remove file path definitions
    content = re.sub(r'[A-Z_]+_PATH = BASE_PATH.*\n', '', content)
    content = re.sub(r'[A-Z_]+_INDEX_FILE =.*\n', '', content)
    
    # Remove _ensure_*_storage functions
    content = re.sub(r'def _ensure_\w+_storage\(\):.*?\n\n', '', content, flags=re.DOTALL)
    
    # Remove _load_*_index functions
    content = re.sub(r'def _load_\w+_index\(\):.*?\n\n', '', content, flags=re.DOTALL)
    
    # Remove _save_*_index functions
    content = re.sub(r'def _save_\w+_index\(.*?\):.*?\n\n', '', content, flags=re.DOTALL)
    
    # Remove _get_*_file_path functions
    content = re.sub(r'def _get_\w+_file_path\(.*?\):.*?\n\n', '', content, flags=re.DOTALL)
    
    # Remove _*_in_file functions
    content = re.sub(r'def _\w+_in_file\(.*?\):.*?return.*?\n\n', '', content, flags=re.DOTALL)
    
    # Update main functions to remove USE_FILE_STORAGE checks
    content = re.sub(
        r'if not USE_FILE_STORAGE:\s+return _(\w+)_in_db\(.*?\)\s+else:\s+return _\1_in_file\(.*?\)',
        r'return _\1_in_db(\2)',
        content,
        flags=re.DOTALL
    )
    
    # Rename _*_in_db to remove _in_db suffix
    content = re.sub(r'_(\w+)_in_db\(', r'_\1(', content)
    
    # Update docstrings
    content = re.sub(r'supports both file-based and database storage', 'database only', content)
    content = re.sub(r'stored in database or file-based storage', 'stored in database', content)
    content = re.sub(r'from database or file-based storage', 'from database', content)
    
    return content

if __name__ == "__main__":
    storage_dir = Path(__file__).parent.parent / "src" / "uepi_api"
    
    for storage_file in storage_dir.glob("storage_*.py"):
        if storage_file.name == "storage_file.py" or storage_file.name == "storage_adapter.py":
            continue
        
        print(f"Refactoring {storage_file.name}...")
        # Backup original
        backup = storage_file.with_suffix('.py.bak')
        if not backup.exists():
            backup.write_text(storage_file.read_text())
        
        # Refactor
        new_content = refactor_storage_file(storage_file)
        storage_file.write_text(new_content)
        print(f"  ✅ Refactored {storage_file.name}")

