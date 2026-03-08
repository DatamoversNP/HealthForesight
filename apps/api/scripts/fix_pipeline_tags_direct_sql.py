#!/usr/bin/env python3
"""
Direct SQL update to add 'preconfigured' tag to all pipelines - guaranteed to work
"""
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import engine
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from sqlalchemy import text

def main():
    """Add 'preconfigured' tag using direct SQL update"""
    try:
        with engine.connect() as conn:
            # Use PostgreSQL JSONB functions to update tags
            # This adds 'preconfigured' to the tags array if it doesn't exist
            update_sql = text("""
                UPDATE pipelines
                SET steps_json = 
                    CASE 
                        WHEN steps_json->'tags' IS NULL THEN
                            jsonb_set(steps_json, '{tags}', '["preconfigured"]'::jsonb)
                        WHEN NOT (steps_json->'tags' @> '"preconfigured"') THEN
                            jsonb_set(
                                steps_json, 
                                '{tags}', 
                                (steps_json->'tags') || '["preconfigured"]'::jsonb
                            )
                        ELSE steps_json
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE tenant_id = :tenant_id
                  AND (steps_json->'tags' IS NULL OR NOT (steps_json->'tags' @> '"preconfigured"'))
            """)
            
            result = conn.execute(update_sql, {"tenant_id": str(DEFAULT_TENANT_ID)})
            conn.commit()
            
            updated_count = result.rowcount
            print(f"✅ Updated {updated_count} pipelines with 'preconfigured' tag using direct SQL")
            print("   Please refresh your web app to see the changes")
            
            # Verify the update
            verify_sql = text("""
                SELECT COUNT(*) as total,
                       COUNT(*) FILTER (WHERE steps_json->'tags' @> '"preconfigured"') as with_tag
                FROM pipelines
                WHERE tenant_id = :tenant_id
            """)
            
            verify_result = conn.execute(verify_sql, {"tenant_id": str(DEFAULT_TENANT_ID)})
            row = verify_result.fetchone()
            print(f"\n📊 Verification:")
            print(f"   Total pipelines: {row[0]}")
            print(f"   Pipelines with 'preconfigured' tag: {row[1]}")
            
        return 0
    except Exception as e:
        print(f"❌ Error updating pipeline tags: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

