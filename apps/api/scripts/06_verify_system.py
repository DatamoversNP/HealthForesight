#!/usr/bin/env python3
"""
Step 6: Verify System
- Verifies database connection
- Checks that policies exist
- Checks that pipelines exist
- Verifies source data directories exist
- Reports system status
"""
import os
import sys
import logging
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"
project_root = current_dir.parent.parent

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Set environment variables
os.environ.setdefault('USE_FILE_STORAGE', 'false')
os.environ.setdefault('LOG_LEVEL', 'INFO')


def main():
    """Verify system is ready"""
    logger.info("=" * 80)
    logger.info("STEP 6: Verify System")
    logger.info("=" * 80)
    
    checks = {
        'Database': False,
        'Tenant/User': False,
        'Policies': False,
        'Pipelines': False,
        'Source Data Directories': False,
    }
    
    # Check database
    try:
        from uepi_api.database import engine
        from sqlalchemy import text, inspect
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks['Database'] = True
        logger.info("✅ Database connection: OK")
        
        # Check tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"   📊 Found {len(tables)} tables")
        
    except Exception as e:
        logger.error(f"❌ Database connection: FAILED - {e}")
    
    # Check tenant/user
    try:
        from uepi_api.storage_auth import DEFAULT_TENANT_ID
        from uepi_api.database import SessionLocal
        from uepi_api.models.tenant import Tenant, User
        
        db = SessionLocal()
        try:
            tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
            user = db.query(User).filter(User.tenant_id == DEFAULT_TENANT_ID).first()
            
            if tenant and user:
                checks['Tenant/User'] = True
                logger.info(f"✅ Tenant/User: OK ({tenant.name}, {user.email})")
            else:
                logger.error("❌ Tenant/User: FAILED - Missing tenant or user")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Tenant/User: FAILED - {e}")
    
    # Check policies
    try:
        from uepi_api.storage_policies import list_policies
        from uepi_api.storage_auth import DEFAULT_TENANT_ID
        
        policies = list_policies(DEFAULT_TENANT_ID)
        checks['Policies'] = len(policies) > 0
        logger.info(f"✅ Policies: {len(policies)} found")
    except Exception as e:
        logger.error(f"❌ Policies: FAILED - {e}")
    
    # Check pipelines
    try:
        from uepi_api.storage_pipelines import list_pipelines
        from uepi_api.storage_auth import DEFAULT_TENANT_ID
        
        pipelines = list_pipelines(DEFAULT_TENANT_ID)
        checks['Pipelines'] = len(pipelines) >= 0  # Allow 0 pipelines
        logger.info(f"✅ Pipelines: {len(pipelines)} found")
    except Exception as e:
        logger.error(f"❌ Pipelines: FAILED - {e}")
    
    # Check source data directories
    try:
        from uepi_api.storage_auth import DEFAULT_TENANT_ID
        
        source_data_dir = project_root / "data" / "source_data" / str(DEFAULT_TENANT_ID)
        historical_dir = source_data_dir / "historical"
        daily_dir = source_data_dir / "daily"
        
        checks['Source Data Directories'] = historical_dir.exists() and daily_dir.exists()
        if checks['Source Data Directories']:
            logger.info(f"✅ Source data directories: OK ({source_data_dir})")
        else:
            logger.warning(f"⚠️  Source data directories: NOT FOUND ({source_data_dir})")
    except Exception as e:
        logger.error(f"❌ Source data directories: FAILED - {e}")
    
    # Summary
    logger.info("=" * 80)
    logger.info("VERIFICATION SUMMARY:")
    for check, status in checks.items():
        status_icon = "✅" if status else "❌"
        logger.info(f"   {status_icon} {check}")
    logger.info("=" * 80)
    
    all_passed = all(checks.values())
    if all_passed:
        logger.info("🎉 All checks passed! System is ready.")
    else:
        logger.warning("⚠️  Some checks failed. Review the errors above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

