#!/usr/bin/env python3
"""
Simple script to add 'preconfigured' tag to all existing pipelines
"""
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import SessionLocal
from uepi_api.models.pipeline import Pipeline
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from sqlalchemy.orm.attributes import flag_modified

def main():
    """Add 'preconfigured' tag to all pipelines"""
    db = SessionLocal()
    try:
        pipelines = db.query(Pipeline).filter(
            Pipeline.tenant_id == DEFAULT_TENANT_ID
        ).all()
        
        print(f"Found {len(pipelines)} pipelines")
        updated_count = 0
        
        for pipeline in pipelines:
            # Get a copy of steps_json to modify
            steps = dict(pipeline.steps_json) if pipeline.steps_json else {}
            current_tags = list(steps.get("tags", []))
            
            # If tags don't include 'preconfigured', add it
            if "preconfigured" not in current_tags:
                if not current_tags:
                    current_tags = ["preconfigured"]
                else:
                    current_tags.append("preconfigured")
                
                steps["tags"] = current_tags
                pipeline.steps_json = steps
                # CRITICAL: Tell SQLAlchemy that the JSONB field was modified
                flag_modified(pipeline, "steps_json")
                updated_count += 1
                print(f"✅ Added 'preconfigured' tag to: {pipeline.name}")
                print(f"   Tags: {current_tags}")
        
        if updated_count > 0:
            db.commit()
            print(f"\n✅ Updated {updated_count} pipelines with 'preconfigured' tag")
            print("   Please refresh your web app to see the changes")
        else:
            print("✅ All pipelines already have 'preconfigured' tag")
        
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

