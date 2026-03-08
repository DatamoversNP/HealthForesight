#!/usr/bin/env python3
"""
Find and fix all syntax errors in router files
"""
import ast
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
router_dir = project_root / "apps" / "api" / "src" / "uepi_api" / "routers"

errors_found = []

def check_syntax(file_path):
    """Check if a Python file has syntax errors"""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        return None
    except SyntaxError as e:
        return e
    except Exception as e:
        return e

# Check all Python files in routers directory
for py_file in router_dir.glob("*.py"):
    if py_file.name.startswith("__"):
        continue
    
    error = check_syntax(py_file)
    if error:
        errors_found.append((py_file, error))
        print(f"❌ {py_file.name}: {error}")

if errors_found:
    print(f"\nFound {len(errors_found)} files with syntax errors")
    sys.exit(1)
else:
    print("✅ All router files have valid syntax!")
    sys.exit(0)

