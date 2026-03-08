#!/usr/bin/env python3
"""Check analysis results to see if they have real data or mock data"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
db_url = "postgresql://postgres:postgres@localhost:5432/uepi_db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def check_analysis_results():
    """Check analysis results"""
    print("="*80)
    print("CHECKING ANALYSIS RESULTS")
    print("="*80)
    print()
    
    db = SessionLocal()
    try:
        # Get analyses with their results
        result = db.execute(text("""
            SELECT 
                a.id,
                a.policy_id,
                a.status,
                a.created_at,
                ir.result_data_json
            FROM analyses a
            LEFT JOIN impact_analysis_results ir ON ir.analysis_id = a.id
            ORDER BY a.created_at DESC
            LIMIT 10
        """))
        
        analyses = result.fetchall()
        print(f"Found {len(analyses)} recent analyses")
        print()
        
        for i, (analysis_id, policy_id, status, created_at, result_data) in enumerate(analyses, 1):
            print(f"Analysis {i}:")
            print(f"  ID: {analysis_id}")
            print(f"  Policy ID: {policy_id}")
            print(f"  Status: {status}")
            print(f"  Created: {created_at}")
            
            if result_data:
                # Check if it's mock data
                if isinstance(result_data, dict):
                    post_period = result_data.get('post_period', {})
                    pre_period = result_data.get('pre_period', {})
                    
                    print(f"  Post period utilization: {post_period.get('utilization_per_1k', 'N/A')}")
                    print(f"  Post period cost: {post_period.get('cost_per_member', 'N/A')}")
                    print(f"  Pre period utilization: {pre_period.get('utilization_per_1k', 'N/A')}")
                    print(f"  Pre period cost: {pre_period.get('cost_per_member', 'N/A')}")
                    
                    # Check if it looks like mock data (same values)
                    if post_period.get('utilization_per_1k') == 106.7 and post_period.get('cost_per_member') == 38.4:
                        print(f"  ⚠️  This appears to be MOCK DATA (same values as other analyses)")
                    else:
                        print(f"  ✅ This appears to be REAL DATA")
                else:
                    print(f"  Result data type: {type(result_data)}")
            else:
                print(f"  ⚠️  No result data")
            
            print()
        
        # Count how many have mock vs real data
        print("Summary:")
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN ir.result_data_json->>'post_period'->>'utilization_per_1k' = '106.7' THEN 1 END) as mock_count
            FROM analyses a
            LEFT JOIN impact_analysis_results ir ON ir.analysis_id = a.id
            WHERE ir.result_data_json IS NOT NULL
        """))
        
        stats = result.fetchone()
        total, mock_count = stats
        print(f"  Total analyses with results: {total}")
        print(f"  Analyses with mock data (utilization=106.7): {mock_count}")
        print(f"  Analyses with real data: {total - mock_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_analysis_results()
