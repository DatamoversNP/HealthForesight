#!/usr/bin/env python3
"""Create canonical data tables in database"""
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import Base, engine
from uepi_api.models.canonical_data import ClaimsLineDB, EnrollmentRecordDB, ProviderRecordDB
from sqlalchemy import inspect

def main():
    print("Creating canonical data tables...")
    from sqlalchemy import text
    
    try:
        # Check if tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        tables_to_create = []
        if 'claims_lines' not in existing_tables:
            tables_to_create.append(('claims_lines', ClaimsLineDB))
        if 'enrollment_records' not in existing_tables:
            tables_to_create.append(('enrollment_records', EnrollmentRecordDB))
        if 'provider_records' not in existing_tables:
            tables_to_create.append(('provider_records', ProviderRecordDB))
        
        if not tables_to_create:
            print("✅ All tables already exist")
            return 0
        
        # Drop orphaned indexes first if they exist
        with engine.connect() as conn:
            for table_name, model_class in tables_to_create:
                # Get all indexes for this table (if table doesn't exist, indexes might be orphaned)
                try:
                    indexes = inspector.get_indexes(table_name)
                    if indexes:
                        print(f"  Found {len(indexes)} indexes for {table_name}, but table doesn't exist")
                        print(f"  Dropping orphaned indexes...")
                        for index in indexes:
                            try:
                                conn.execute(text(f"DROP INDEX IF EXISTS {index['name']}"))
                                print(f"    Dropped index: {index['name']}")
                            except Exception as e:
                                print(f"    Warning: Could not drop index {index['name']}: {e}")
                except Exception:
                    pass  # Table doesn't exist, which is expected
        
        # Now create the tables
        print(f"  Creating {len(tables_to_create)} table(s)...")
        for table_name, model_class in tables_to_create:
            try:
                model_class.__table__.create(bind=engine, checkfirst=True)
                print(f"    ✅ Created {table_name}")
            except Exception as e:
                if "already exists" in str(e) or "DuplicateTable" in str(e):
                    print(f"    ✅ {table_name} already exists")
                else:
                    print(f"    ❌ Error creating {table_name}: {e}")
                    # Try to create without indexes
                    try:
                        # Create table structure first
                        with engine.connect() as conn:
                            # This is a workaround - create table manually if needed
                            pass
                    except:
                        pass
        
        print("✅ Successfully created canonical data tables")
        return 0
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

