#!/usr/bin/env python3
"""
Step 2: Setup Demo Tenant and User
- Creates demo tenant if it doesn't exist
- Creates demo user if it doesn't exist
- Verifies tenant and user are ready
"""
import os
import sys
import logging
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

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
    """Setup demo tenant and user"""
    logger.info("=" * 80)
    logger.info("STEP 2: Setup Demo Tenant and User")
    logger.info("=" * 80)
    
    try:
        from uepi_api.storage_auth import DEFAULT_TENANT_ID, ensure_demo_tenant_and_user
        from uepi_api.database import SessionLocal
        from uepi_api.models.tenant import Tenant, User
        
        logger.info(f"📋 Ensuring demo tenant and user exist...")
        logger.info(f"   Tenant ID: {DEFAULT_TENANT_ID}")
        
        # Ensure tenant and user exist
        ensure_demo_tenant_and_user()
        
        # Verify tenant and user exist
        db = SessionLocal()
        try:
            tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
            if not tenant:
                logger.error(f"❌ Tenant {DEFAULT_TENANT_ID} not found after creation!")
                return 1
            
            user = db.query(User).filter(User.tenant_id == DEFAULT_TENANT_ID).first()
            if not user:
                logger.error(f"❌ No user found for tenant {DEFAULT_TENANT_ID}!")
                return 1
            
            logger.info(f"✅ Tenant: {tenant.name} (ID: {tenant.id})")
            logger.info(f"✅ User: {user.email} (ID: {user.id})")
            logger.info("✅ Demo tenant and user ready!")
            return 0
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"❌ Failed to setup tenant and user: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

