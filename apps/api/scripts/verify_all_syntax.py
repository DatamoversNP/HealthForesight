#!/usr/bin/env python3
"""
Verify all router files have valid Python syntax
"""
import ast
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
router_dir = project_root / "apps" / "api" / "src" / "uepi_api" / "routers"

errors = []

def check_file(file_path):
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        return None
    except SyntaxError as e:
        return f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return str(e)

# Check critical router files
critical_files = [
    "access.py",
    "analyses.py", 
    "policies.py",
    "pipelines.py",
]

for filename in critical_files:
    file_path = router_dir / filename
    if file_path.exists():
        error = check_file(file_path)
        if error:
            errors.append((filename, error))
            print(f"❌ {filename}: {error}")
        else:
            print(f"✅ {filename}: OK")

if errors:
    print(f"\n❌ Found {len(errors)} files with syntax errors")
    sys.exit(1)
else:
    print(f"\n✅ All critical router files have valid syntax!")
    sys.exit(0)

