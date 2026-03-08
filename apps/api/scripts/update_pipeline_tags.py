#!/usr/bin/env python3
"""
Update existing pipelines to add tags from seed_all_21_pipelines.py definitions
"""
import sys
from pathlib import Path
from uuid import UUID

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import SessionLocal
from uepi_api.models.pipeline import Pipeline
from uepi_api.storage_auth import DEFAULT_TENANT_ID

# Import pipeline definitions to get tags
scripts_dir = current_dir / "scripts"
seed_script = scripts_dir / "seed_all_21_pipelines.py"

# Read the seed script to extract pipeline definitions
import importlib.util
spec = importlib.util.spec_from_file_location("seed_all_21_pipelines", seed_script)
seed_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed_module)

PIPELINE_DEFINITIONS = seed_module.PIPELINE_DEFINITIONS

# Create mapping of pipeline_id to tags
pipeline_tags_map = {p["pipeline_id"]: p.get("tags", []) for p in PIPELINE_DEFINITIONS}

def main():
    """Update existing pipelines with tags"""
    db = SessionLocal()
    try:
        pipelines = db.query(Pipeline).filter(
            Pipeline.tenant_id == DEFAULT_TENANT_ID
        ).all()
        
        updated_count = 0
        for pipeline in pipelines:
            steps = pipeline.steps_json if pipeline.steps_json else {}
            current_tags = steps.get("tags", [])
            
            # Check if this pipeline has tags in our definitions
            if pipeline.pipeline_id in pipeline_tags_map:
                expected_tags = pipeline_tags_map[pipeline.pipeline_id]
                if current_tags != expected_tags:
                    # Update tags
                    steps["tags"] = expected_tags
                    pipeline.steps_json = steps
                    updated_count += 1
                    print(f"✅ Updated tags for pipeline: {pipeline.name}")
                    print(f"   Tags: {expected_tags}")
            elif not current_tags:
                # Pipeline not in definitions but has no tags - add default preconfigured tag
                # if it looks like a preconfigured pipeline (has target_model, etc.)
                if steps.get("target_model"):
                    steps["tags"] = ["preconfigured"]
                    pipeline.steps_json = steps
                    updated_count += 1
                    print(f"✅ Added default 'preconfigured' tag to: {pipeline.name}")
        
        if updated_count > 0:
            db.commit()
            print(f"\n✅ Updated {updated_count} pipelines with tags")
        else:
            print("✅ All pipelines already have correct tags")
        
        return 0
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating pipeline tags: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())

