#!/usr/bin/env python3
"""
Update existing baseline analyses with default names based on creation date
"""
import sys
from pathlib import Path
from datetime import datetime

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import SessionLocal
from uepi_api.models.analysis import Analysis
from uepi_api.storage_auth import DEFAULT_TENANT_ID

def generate_default_name(analysis: Analysis, index: int) -> str:
    """Generate a default name for an analysis based on its creation date"""
    if analysis.created_at:
        date_str = analysis.created_at.strftime("%b %d, %Y")
        return f"Baseline Analysis - {date_str}"
    else:
        return f"Baseline Analysis {index + 1}"

def main():
    """Update existing baseline analyses with names"""
    db = SessionLocal()
    try:
        # Get all baseline analyses without names
        analyses = db.query(Analysis).filter(
            Analysis.analysis_type == "BASELINE",
            Analysis.tenant_id == DEFAULT_TENANT_ID,
            (Analysis.name == None) | (Analysis.name == "")
        ).order_by(Analysis.created_at.asc()).all()
        
        print(f"Found {len(analyses)} baseline analyses without names")
        
        if len(analyses) == 0:
            print("✅ All analyses already have names")
            return 0
        
        updated_count = 0
        for i, analysis in enumerate(analyses):
            # Generate a unique name
            base_name = generate_default_name(analysis, i)
            name = base_name
            
            # Check if name already exists (including already updated ones in this session), append number if needed
            counter = 1
            while True:
                # Check in database
                existing = db.query(Analysis).filter(
                    Analysis.tenant_id == DEFAULT_TENANT_ID,
                    Analysis.analysis_type == "BASELINE",
                    Analysis.name == name
                ).first()
                
                # Also check in current session (analyses we've already updated)
                if existing and existing.id != analysis.id:
                    name = f"{base_name} ({counter})"
                    counter += 1
                else:
                    break
            
            # Update the analysis and commit immediately to avoid conflicts
            analysis.name = name
            updated_count += 1
            analysis_id_str = str(analysis.id)
            print(f"  ✅ Updated: {analysis_id_str[:8]}... -> '{name}'")
            
            # Commit after each update to ensure uniqueness
            db.commit()
            db.refresh(analysis)
        print(f"\n✅ Successfully updated {updated_count} baseline analyses with names")
        
        # Verify
        all_analyses = db.query(Analysis).filter(
            Analysis.analysis_type == "BASELINE",
            Analysis.tenant_id == DEFAULT_TENANT_ID
        ).all()
        
        print(f"\n📊 All baseline analyses:")
        for a in all_analyses:
            analysis_id_str = str(a.id)
            print(f"  - {a.name or '(no name)'} ({analysis_id_str[:8]}...) - {a.status}")
        
        return 0
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating analysis names: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())

