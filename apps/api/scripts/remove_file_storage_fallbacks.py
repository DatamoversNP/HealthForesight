#!/usr/bin/env python3
"""
Remove all file storage fallback code from routers
This script removes USE_FILE_STORAGE checks and file storage fallback blocks
"""
import re
import sys
from pathlib import Path

def remove_file_storage_fallbacks(file_path: Path):
    """Remove file storage fallback blocks from a Python file"""
    content = file_path.read_text()
    original = content
    
    # Remove USE_FILE_STORAGE imports
    content = re.sub(
        r'from uepi_api\.database import USE_FILE_STORAGE\n',
        '# Database-only mode - USE_FILE_STORAGE removed\n',
        content
    )
    
    # Remove "if USE_FILE_STORAGE:" blocks (multiline)
    # Pattern: if USE_FILE_STORAGE: ... (until next except/else at same indent)
    lines = content.split('\n')
    new_lines = []
    skip_until_indent = None
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a USE_FILE_STORAGE check
        if 'if USE_FILE_STORAGE:' in line or 'if False:  # Always use database' in line:
            # Skip this entire block
            indent = len(line) - len(line.lstrip())
            skip_until_indent = indent
            # Skip the if line
            i += 1
            # Skip all lines with same or greater indent until we hit else/except at same level
            while i < len(lines):
                current_line = lines[i]
                if not current_line.strip():  # Empty line
                    i += 1
                    continue
                current_indent = len(current_line) - len(current_line.lstrip())
                if current_indent <= skip_until_indent:
                    # Check if it's else/except at same level
                    if current_line.strip().startswith(('else:', 'except', 'elif')):
                        # Skip else/except too if it's part of file storage block
                        if 'file' in current_line.lower() or 'storage' in current_line.lower():
                            i += 1
                            continue
                    break
                i += 1
            continue
        
        # Check if we're in a file storage fallback block
        if skip_until_indent is not None:
            current_indent = len(line) - len(line.lstrip()) if line.strip() else 0
            if current_indent <= skip_until_indent and line.strip():
                skip_until_indent = None
        
        if skip_until_indent is None:
            new_lines.append(line)
        
        i += 1
    
    content = '\n'.join(new_lines)
    
    # Remove comments about file storage
    content = re.sub(r'# .*file.*storage.*\n', '', content, flags=re.IGNORECASE)
    content = re.sub(r'# .*USE_FILE_STORAGE.*\n', '', content, flags=re.IGNORECASE)
    
    if content != original:
        file_path.write_text(content)
        print(f"✅ Updated {file_path}")
        return True
    return False

if __name__ == "__main__":
    router_dir = Path(__file__).parent.parent / "src" / "uepi_api" / "routers"
    
    files_to_update = [
        router_dir / "policies.py",
        router_dir / "analyses.py",
        router_dir / "access.py",
    ]
    
    updated = 0
    for file_path in files_to_update:
        if file_path.exists():
            if remove_file_storage_fallbacks(file_path):
                updated += 1
    
    print(f"\n✅ Updated {updated} file(s)")
    sys.exit(0)

