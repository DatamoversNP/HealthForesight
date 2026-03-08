#!/usr/bin/env python3
"""
Step 5: Setup Source Data Directories
- Creates source data directory structure
- Creates historical and daily load directories
- Creates README with usage instructions
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

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
    """Setup source data directories"""
    logger.info("=" * 80)
    logger.info("STEP 5: Setup Source Data Directories")
    logger.info("=" * 80)
    
    try:
        from uepi_api.storage_auth import DEFAULT_TENANT_ID
        
        # Source data directory structure:
        # data/source_data/
        #   {tenant_id}/
        #     historical/          # One-time historical data loads
        #     daily/               # Daily incremental loads
        #       YYYY-MM-DD/        # Date-based subdirectories
        
        source_data_root = project_root / "data" / "source_data"
        tenant_source_dir = source_data_root / str(DEFAULT_TENANT_ID)
        historical_dir = tenant_source_dir / "historical"
        daily_dir = tenant_source_dir / "daily"
        
        # Create directories
        historical_dir.mkdir(parents=True, exist_ok=True)
        daily_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Created source data directories:")
        logger.info(f"   📁 Historical: {historical_dir}")
        logger.info(f"   📁 Daily: {daily_dir}")
        
        # Create README in source data directory
        readme_file = tenant_source_dir / "README.md"
        readme_content = f"""# Source Data Directory

This directory is where source data files should be placed for ingestion.

## Directory Structure

- `historical/` - One-time historical data loads
  - Place all historical data files here
  - Files will be processed by pipelines and loaded into target data model
  
- `daily/` - Daily incremental data loads
  - Create date-based subdirectories: `YYYY-MM-DD/`
  - Example: `daily/2026-01-15/`
  - Place daily files in the appropriate date directory

## Usage

1. **Historical Load:**
   - Place files in `historical/` directory
   - Run pipeline ingestion via API or UI
   - Files will be processed and loaded into target data model

2. **Daily Load:**
   - Create date directory: `daily/YYYY-MM-DD/`
   - Place daily files in the date directory
   - Run pipeline ingestion via API or UI
   - Files will be processed and appended to target data model

## Supported Formats

- CSV
- Parquet
- JSON

## Pipeline Processing

Pipelines are configured in the database and will:
1. Read source files from this directory
2. Apply field mappings and transformations
3. Load data into target data model (blob storage)
4. Store metadata in database

## Target Data Model Location

Processed data is stored in:
- `data/target_data_model/{DEFAULT_TENANT_ID}/`
- Organized by dataset type (CLAIMS_LINES, MEMBER_MASTER, etc.)

Created: {datetime.now().isoformat()}
"""
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        logger.info(f"✅ Created README: {readme_file}")
        logger.info("✅ Source data directories setup complete!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Failed to setup source data directories: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

