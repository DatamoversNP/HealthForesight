#!/usr/bin/env python3
"""
Step 1: Database Setup
- Resets database (drop and recreate)
- Creates all tables
- Verifies database connection
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
    """Setup database: reset and create tables"""
    logger.info("=" * 80)
    logger.info("STEP 1: Database Setup")
    logger.info("=" * 80)
    
    try:
        # Step 1: Force reset database (drop and recreate)
        logger.info("🔄 Resetting database (drop and recreate)...")
        force_reset_script = current_dir / "scripts" / "force_reset_and_create.py"
        if not force_reset_script.exists():
            logger.error(f"❌ Force reset script not found: {force_reset_script}")
            return 1
        
        import subprocess
        env = os.environ.copy()
        result = subprocess.run(
            [sys.executable, str(force_reset_script)],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            env=env
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Failed to reset database")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return 1
        
        logger.info("✅ Database reset and tables created")
        
        # Step 2: Verify database connection and tables
        logger.info("🔍 Verifying database connection...")
        from uepi_api.database import engine
        from sqlalchemy import inspect, text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ Connected to PostgreSQL: {version.split(',')[0]}")
        
        # Verify tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"📊 Found {len(tables)} tables in database")
        
        if len(tables) == 0:
            logger.error("❌ No tables found in database!")
            return 1
        
        logger.info("✅ Database setup complete!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Failed to setup database: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

