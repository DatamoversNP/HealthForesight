#!/usr/bin/env python3
"""Test if the app can start without errors"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/uepi_db")
os.environ.setdefault("LOG_LEVEL", "INFO")

try:
    from uepi_api.main import create_app
    app = create_app()
    print("✅ App created successfully!")
    print(f"✅ Total routes: {len(app.routes)}")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error creating app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

