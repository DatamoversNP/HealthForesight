#!/usr/bin/env python3
"""
Step 4: Seed Pipelines
- Loads pipelines from JSON files in data/pipelines/
- Creates pipelines in database (skips if already exist)
- Reports creation status
"""
import os
import sys
import json
import logging
from pathlib import Path
from uuid import UUID

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
    """Seed pipelines from JSON files"""
    logger.info("=" * 80)
    logger.info("STEP 4: Seed Pipelines")
    logger.info("=" * 80)
    
    try:
        from uepi_api.storage_pipelines import create_pipeline, list_pipelines
        from uepi_api.storage_auth import DEFAULT_TENANT_ID
        
        pipelines_dir = project_root / "data" / "pipelines"
        if not pipelines_dir.exists():
            logger.warning(f"⚠️  Pipelines directory not found: {pipelines_dir}")
            logger.info("💡 Creating empty pipelines directory...")
            pipelines_dir.mkdir(parents=True, exist_ok=True)
            logger.info("✅ Pipelines directory created (empty - no pipelines to seed)")
            return 0
        
        # Find all pipeline JSON files
        pipeline_files = list(pipelines_dir.glob("pipeline-*.json"))
        logger.info(f"📋 Found {len(pipeline_files)} pipeline files")
        
        if len(pipeline_files) == 0:
            logger.info("💡 No pipeline files found. Skipping pipeline seeding.")
            return 0
        
        # Check existing pipelines
        existing_pipelines = list_pipelines(DEFAULT_TENANT_ID)
        # Use pipeline_id (string) from the returned dict, not 'id'
        existing_pipeline_ids = {UUID(p.get('pipeline_id')) for p in existing_pipelines if p.get('pipeline_id')}
        logger.info(f"📊 Found {len(existing_pipelines)} existing pipelines in database")
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for pipeline_file in pipeline_files:
            try:
                with open(pipeline_file, 'r') as f:
                    pipeline_data = json.load(f)
                
                pipeline_id = UUID(pipeline_data.get('pipeline_id') or pipeline_data.get('id'))
                pipeline_name = pipeline_data.get('pipeline_name', 'Unknown')
                
                if pipeline_id in existing_pipeline_ids:
                    logger.debug(f"⏭️  Skipping existing pipeline: {pipeline_name} ({pipeline_id})")
                    skipped_count += 1
                    continue
                
                logger.info(f"📝 Creating pipeline: {pipeline_name} ({pipeline_id})")
                
                # Convert to format expected by create_pipeline
                pipeline_dict = {
                    'pipeline_id': str(pipeline_id),  # Include pipeline_id in dict
                    'name': pipeline_name,
                    'description': pipeline_data.get('pipeline_description', ''),
                    'source_type': pipeline_data.get('source_type', 'CSV'),
                    'target_dataset_type': pipeline_data.get('target_dataset_type'),
                    'target_model': pipeline_data.get('target_model'),
                    'field_mappings': pipeline_data.get('field_mappings', []),
                    'mode': pipeline_data.get('mode', 'APPEND'),
                    'deduplication': pipeline_data.get('deduplication', {}),
                    'control_fields': pipeline_data.get('control_fields', {}),
                    'validation_rules': pipeline_data.get('validation_rules'),
                    'required_fields': pipeline_data.get('required_fields', []),
                    'batch_size': pipeline_data.get('batch_size', 10000),
                    'error_threshold': pipeline_data.get('error_threshold', 0.05),
                    'continue_on_error': pipeline_data.get('continue_on_error', True),
                    'status': 'ACTIVE' if pipeline_data.get('active', True) else 'INACTIVE',
                }
                
                created = create_pipeline(DEFAULT_TENANT_ID, pipeline_dict)
                if created:
                    logger.info(f"✅ Created pipeline: {pipeline_name}")
                    created_count += 1
                else:
                    logger.error(f"❌ Failed to create pipeline: {pipeline_name}")
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error creating pipeline from {pipeline_file.name}: {e}", exc_info=True)
                error_count += 1
        
        logger.info("=" * 80)
        logger.info(f"✅ Pipeline seeding from files complete: {created_count} created, {skipped_count} skipped, {error_count} errors")
        logger.info("=" * 80)
        
        # Also seed comprehensive pipelines
        logger.info("")
        logger.info("=" * 80)
        logger.info("Seeding Comprehensive Pipelines")
        logger.info("=" * 80)
        try:
            # Import and run comprehensive pipeline seeding
            import importlib.util
            scripts_dir = current_dir / "scripts"
            comprehensive_script = scripts_dir / "seed_all_21_pipelines.py"
            if comprehensive_script.exists():
                spec = importlib.util.spec_from_file_location("seed_all_21_pipelines", comprehensive_script)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Call the function that seeds all pipelines
                if hasattr(module, 'seed_all_pipelines'):
                    module.seed_all_pipelines()
                else:
                    logger.warning("⚠️  seed_all_pipelines function not found in script")
            else:
                logger.warning("⚠️  Comprehensive pipelines script not found, skipping")
        except Exception as e:
            logger.warning(f"⚠️  Could not seed comprehensive pipelines: {e}")
            import traceback
            traceback.print_exc()
            # Non-critical, continue
        
        logger.info("=" * 80)
        logger.info(f"✅ Pipeline seeding complete: {created_count} created, {skipped_count} skipped, {error_count} errors")
        logger.info("=" * 80)
        
        return 0 if error_count == 0 else 1
        
    except Exception as e:
        logger.error(f"❌ Failed to seed pipelines: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

