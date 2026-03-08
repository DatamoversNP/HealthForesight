"""Create QA test users for each role"""
import json
import sys
import os
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Get project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent

# Add paths
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

# Set PYTHONPATH
os.environ['PYTHONPATH'] = f"{PROJECT_ROOT / 'apps' / 'api' / 'src'}:{PROJECT_ROOT / 'packages' / 'common' / 'src'}"

from uepi_api.storage_file import BASE_PATH
from uepi_api.storage_auth import DEFAULT_TENANT_ID

# QA Test Users Configuration
QA_TEST_USERS = [
    {
        "email": "qa.payer.cmo@test.com",
        "name": "QA Payer CMO",
        "roles": ["EXEC_VIEWER", "STRATEGY"],  # CMO has executive view + strategy
        "user_id": UUID("10000000-0000-0000-0000-000000000001"),
    },
    {
        "email": "qa.provider.cfo@test.com",
        "name": "QA Provider CFO",
        "roles": ["EXEC_VIEWER"],  # CFO has executive view
        "user_id": UUID("10000000-0000-0000-0000-000000000002"),
    },
    {
        "email": "qa.payer.um.lead@test.com",
        "name": "QA Payer UM Lead",
        "roles": ["UM_LEADER"],  # UM Lead
        "user_id": UUID("10000000-0000-0000-0000-000000000003"),
    },
    {
        "email": "qa.payer.actuary@test.com",
        "name": "QA Payer Actuary",
        "roles": ["ACTUARIAL"],  # Actuary
        "user_id": UUID("10000000-0000-0000-0000-000000000004"),
    },
    {
        "email": "qa.payer.network.strategy@test.com",
        "name": "QA Payer Network Strategy",
        "roles": ["STRATEGY"],  # Network Strategy
        "user_id": UUID("10000000-0000-0000-0000-000000000005"),
    },
    {
        "email": "qa.payer.analytics@test.com",
        "name": "QA Payer Analytics",
        "roles": ["ACTUARIAL", "STRATEGY"],  # Analytics (combines actuarial + strategy)
        "user_id": UUID("10000000-0000-0000-0000-000000000006"),
    },
    {
        "email": "qa.readonly.exec@test.com",
        "name": "QA Read-Only Executive",
        "roles": ["EXEC_VIEWER"],  # Read-only executive
        "user_id": UUID("10000000-0000-0000-0000-000000000007"),
    },
]

# Use user_storage from storage module
from uepi_api.storage import user_storage


def create_qa_user(user_config: dict):
    """Create a QA test user"""
    user_id = user_config["user_id"]
    
    user_data = {
        "tenant_id": str(DEFAULT_TENANT_ID),
        "email": user_config["email"],
        "name": user_config["name"],
        "roles": user_config["roles"],
        "status": "active",
    }
    
    # Use user_storage to create user
    user_storage.create(user_id, user_data)
    
    print(f"✅ Created QA user: {user_config['name']} ({user_config['email']})")
    print(f"   Roles: {', '.join(user_config['roles'])}")
    print(f"   User ID: {user_id}")
    print()
    
    return user_data


def main():
    """Create all QA test users"""
    print("=" * 70)
    print("Creating QA Test Users")
    print("=" * 70)
    print()
    
    created_users = []
    for user_config in QA_TEST_USERS:
        try:
            user_data = create_qa_user(user_config)
            created_users.append(user_data)
        except Exception as e:
            print(f"❌ Failed to create user {user_config['email']}: {e}")
            print()
    
    print("=" * 70)
    print(f"✅ Created {len(created_users)} QA test users")
    print("=" * 70)
    print()
    print("QA Test Users Summary:")
    print()
    for user in created_users:
        print(f"  • {user['name']}")
        print(f"    Email: {user['email']}")
        print(f"    Roles: {', '.join(user['roles'])}")
        print(f"    ID: {user['id']}")
        print()


if __name__ == "__main__":
    main()

