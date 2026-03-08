#!/usr/bin/env python3
"""
Set password for postgres user using psycopg2
This connects without password first (if trust auth is enabled) or prompts for password
"""
import sys
import getpass
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

def set_password():
    """Set password for postgres user"""
    try:
        import psycopg2
        
        print("🔐 Setting password for postgres user...")
        print("")
        print("Try connecting with different methods:")
        print("")
        
        # Try 1: Connect as postgres with no password (if trust auth enabled)
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user='postgres',
                password=''
            )
            print("✅ Connected without password (trust authentication enabled)")
            
            # Set password
            new_password = getpass.getpass("Enter new password for postgres user (or press Enter for empty): ")
            if new_password:
                cur = conn.cursor()
                cur.execute(f"ALTER USER postgres WITH PASSWORD '{new_password}';")
                conn.commit()
                cur.close()
                print(f"✅ Password set for postgres user")
            else:
                cur = conn.cursor()
                cur.execute("ALTER USER postgres WITH PASSWORD '';")
                conn.commit()
                cur.close()
                print("✅ Empty password set (trust authentication)")
            
            conn.close()
            return True
            
        except psycopg2.OperationalError:
            print("⚠️  Cannot connect without password")
            print("")
            print("You need to either:")
            print("1. Configure trust authentication (run configure_postgres_auth.sh)")
            print("2. Or provide existing password:")
            
            password = getpass.getpass("Enter current postgres password: ")
            try:
                conn = psycopg2.connect(
                    host='localhost',
                    port=5432,
                    database='postgres',
                    user='postgres',
                    password=password
                )
                print("✅ Connected with password")
                
                new_password = getpass.getpass("Enter new password (or press Enter to keep current): ")
                if new_password:
                    cur = conn.cursor()
                    cur.execute(f"ALTER USER postgres WITH PASSWORD '{new_password}';")
                    conn.commit()
                    cur.close()
                    print(f"✅ Password updated")
                
                conn.close()
                return True
                
            except psycopg2.OperationalError as e:
                print(f"❌ Authentication failed: {e}")
                return False
        
    except ImportError:
        print("❌ psycopg2 not installed")
        print("   Install with: pip3 install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = set_password()
    sys.exit(0 if success else 1)

