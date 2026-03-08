"""Seed demo data for development and production"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import UUID, uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "api" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "common" / "src"))

from sqlalchemy.orm import Session

from uepi_api.database import Base, engine, SessionLocal
from uepi_api.models.tenant import Tenant, User, Role
from uepi_api.models.policy import Policy, PolicyVersion, PolicyCodeSet
from uepi_api.models.ingestion import Ingestion
from uepi_api.config import get_settings

settings = get_settings()


def seed_demo_data():
    """Seed demo tenant, user, policies, and ingestions"""
    # Create all tables first
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create demo tenant
        tenant_id = UUID("00000000-0000-0000-0000-000000000002")
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            tenant = Tenant(
                id=tenant_id,
                name="Demo Tenant",
                domain="demo",
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print("✅ Created demo tenant")
        else:
            print("ℹ️  Demo tenant already exists")
        
        # Create demo user
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                tenant_id=tenant.id,
                email="demo@example.com",
                oidc_sub="demo-user-123",
                full_name="Demo User",
                is_active="true",
                is_admin="true",
                is_tenant_admin="true",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print("✅ Created demo user")
        else:
            print("ℹ️  Demo user already exists")
        
        # Create roles if they don't exist
        role_names = ["POLICY_ADMIN", "UM_LEADER", "ACTUARIAL", "STRATEGY", "COMPLIANCE", "EXEC_VIEWER"]
        for role_name in role_names:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name)
                db.add(role)
        
        db.commit()
        print("✅ Created roles")
        
        # Assign roles to user
        policy_admin_role = db.query(Role).filter(Role.name == "POLICY_ADMIN").first()
        um_leader_role = db.query(Role).filter(Role.name == "UM_LEADER").first()
        if policy_admin_role and policy_admin_role not in user.roles:
            user.roles.append(policy_admin_role)
        if um_leader_role and um_leader_role not in user.roles:
            user.roles.append(um_leader_role)
        db.commit()
        print("✅ Assigned roles to user")
        
        # Create sample policies
        policies_data = [
            {
                "name": "Tighten PA for Outpatient MRI",
                "policy_type": "PA",
                "owner_role": "POLICY_ADMIN",
                "description": "Require prior authorization for outpatient MRI procedures",
                "effective_date": datetime.now() + timedelta(days=30),
                "codes": ["72141", "72142", "72146", "72148"],  # Lumbar MRI codes
                "code_group": "MRI_LUMBAR",
            },
            {
                "name": "Site-of-Care Restriction for Infusion",
                "policy_type": "SITE_OF_CARE",
                "owner_role": "UM_LEADER",
                "description": "Restrict infusion services to outpatient hospital setting",
                "effective_date": datetime.now() + timedelta(days=45),
                "codes": ["96413", "96415", "96417"],  # Chemotherapy infusion
                "code_group": "INFUSION",
            },
            {
                "name": "Coverage Relaxation for PT",
                "policy_type": "COVERAGE",
                "owner_role": "STRATEGY",
                "description": "Relax coverage requirements for physical therapy services",
                "effective_date": datetime.now() + timedelta(days=60),
                "codes": ["97110", "97112", "97140"],  # Physical therapy
                "code_group": "PT",
            },
            {
                "name": "Step Therapy for High-Cost Biologic",
                "policy_type": "STEP_THERAPY",
                "owner_role": "POLICY_ADMIN",
                "description": "Require step therapy before approving high-cost biologic treatments",
                "effective_date": datetime.now() + timedelta(days=75),
                "codes": ["96413", "96415"],
                "code_group": "BIOLOGIC",
            },
            {
                "name": "Urgent Care Copay Increase",
                "policy_type": "BENEFIT",
                "owner_role": "STRATEGY",
                "description": "Increase copay for urgent care visits",
                "effective_date": datetime.now() + timedelta(days=90),
                "codes": ["99281", "99282", "99283"],  # ER visits
                "code_group": "URGENT_CARE",
            },
        ]
        
        for policy_data in policies_data:
            # Check if policy already exists
            existing = db.query(Policy).filter(
                Policy.name == policy_data["name"],
                Policy.tenant_id == tenant.id
            ).first()
            
            if not existing:
                # Create policy
                policy = Policy(
                    tenant_id=tenant.id,
                    name=policy_data["name"],
                    policy_type=policy_data["policy_type"],
                    owner_role=policy_data["owner_role"],
                    description=policy_data["description"],
                )
                db.add(policy)
                db.flush()
                
                # Create policy version
                version = PolicyVersion(
                    tenant_id=tenant.id,
                    policy_id=policy.id,
                    version_number=1,
                    effective_start_date=policy_data["effective_date"],
                    change_type="NEW",
                    enforcement_strength="HARD",  # Default enforcement strength (SOFT or HARD)
                )
                db.add(version)
                db.flush()
                
                # Create policy code sets (linked to version, not policy directly)
                for code in policy_data["codes"]:
                    code_set = PolicyCodeSet(
                        tenant_id=tenant.id,
                        version_id=version.id,
                        code=code,
                        code_type="CPT",
                        code_group=policy_data["code_group"],
                    )
                    db.add(code_set)
                
                print(f"✅ Created policy: {policy_data['name']}")
            else:
                print(f"ℹ️  Policy already exists: {policy_data['name']}")
        
        db.commit()
        
        # Create sample ingestion record
        ingestion = db.query(Ingestion).filter(
            Ingestion.tenant_id == tenant.id,
            Ingestion.ingestion_type == "CLAIMS"
        ).first()
        
        if not ingestion:
            ingestion = Ingestion(
                tenant_id=tenant.id,
                ingestion_type="CLAIMS",
                status="COMPLETED",
                manifest_uri="s3://uepi-data/demo/manifest.json",
            )
            ingestion.completed_at = datetime.now() - timedelta(days=1)
            db.add(ingestion)
            db.commit()
            print("✅ Created sample ingestion record")
        else:
            print("ℹ️  Ingestion record already exists")
        
        print("\n✅ Demo data seeded successfully!")
        print(f"   Tenant: {tenant.name} ({tenant.id})")
        print(f"   User: {user.email} ({user.id})")
        print(f"   Policies: {len(policies_data)}")
        
    except Exception as e:
        print(f"❌ Error seeding demo data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
