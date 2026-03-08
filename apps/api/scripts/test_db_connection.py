#!/usr/bin/env python3
"""
Test PostgreSQL database connection
"""
import os
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

def test_connection(db_url):
    """Test database connection"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse connection string
        parsed = urlparse(db_url)
        
        print(f"🔌 Testing connection to: {parsed.hostname}:{parsed.port}/{parsed.path[1:]}")
        print(f"   User: {parsed.username}")
        
        # Connect
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:] if parsed.path else 'postgres',
            user=parsed.username,
            password=parsed.password
        )
        
        # Test query
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        print(f"✅ Connection successful!")
        print(f"   PostgreSQL: {version.split(',')[0]}")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not set")
        print("")
        print("Set DATABASE_URL with your actual PostgreSQL credentials:")
        print("  export DATABASE_URL='postgresql://username:password@localhost:5432/database_name'")
        print("")
        print("Common examples:")
        print("  # Default PostgreSQL installation:")
        print("  export DATABASE_URL='postgresql://postgres:yourpassword@localhost:5432/uepi_db'")
        print("")
        print("  # macOS Homebrew PostgreSQL:")
        print("  export DATABASE_URL='postgresql://$(whoami)@localhost:5432/uepi_db'")
        print("")
        print("  # If no password:")
        print("  export DATABASE_URL='postgresql://postgres@localhost:5432/uepi_db'")
        sys.exit(1)
    
    success = test_connection(db_url)
    sys.exit(0 if success else 1)

