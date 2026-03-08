#!/usr/bin/env python3
"""
Daily job to generate and ingest post-policy data

This script is designed to run daily (e.g., via cron or systemd timer) to:
1. Generate post-policy synthetic data for the previous day
2. Load data via ingestion pipeline
3. Optionally trigger observation analysis

Usage:
    # Run manually
    python scripts/daily_post_policy_job.py
    
    # Schedule via cron (run daily at 2 AM)
    # Add to crontab: 0 2 * * * /path/to/venv/bin/python /path/to/scripts/daily_post_policy_job.py >> /var/log/uepi/daily_job.log 2>&1
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from uuid import UUID

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

# Import functions directly (same as in generate_post_policy_and_observation.py)
import importlib.util
import requests
import pandas as pd

# Load generate_post_policy_and_observation as a module
gen_obs_script_path = PROJECT_ROOT / "scripts" / "generate_post_policy_and_observation.py"
spec = importlib.util.spec_from_file_location("gen_obs", gen_obs_script_path)
gen_obs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_obs)

generate_post_policy_data = gen_obs.generate_post_policy_data
load_data_to_target_model_via_pipeline = gen_obs.load_data_to_target_model_via_pipeline
get_all_policies = gen_obs.get_all_policies
run_impact_analysis = gen_obs.run_impact_analysis
create_observation_from_analysis = gen_obs.create_observation_from_analysis

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer dev-token-123"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'daily_post_policy_job.log'),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
POLICY_EFFECTIVE_DATE = datetime(2026, 1, 1)  # Policies effective from this date


def run_daily_job(
    target_date: datetime | None = None,
    tenant_id: UUID = DEFAULT_TENANT_ID,
    run_observations: bool = False,
):
    """Run daily post-policy data generation and ingestion job"""
    
    # Default to yesterday if no date specified
    if target_date is None:
        target_date = datetime.now() - timedelta(days=1)
        # Set to start of day
        target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # End date is end of target_date
    end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    logger.info("="*60)
    logger.info("DAILY POST-POLICY DATA JOB")
    logger.info("="*60)
    logger.info(f"Target date: {target_date.date()}")
    logger.info(f"Policy effective date: {POLICY_EFFECTIVE_DATE.date()}")
    logger.info(f"Tenant ID: {tenant_id}")
    logger.info("="*60)
    
    # Only generate data if target_date is on or after policy effective date
    if target_date.date() < POLICY_EFFECTIVE_DATE.date():
        logger.warning(f"Target date {target_date.date()} is before policy effective date {POLICY_EFFECTIVE_DATE.date()}")
        logger.warning("Skipping data generation (no post-policy data needed)")
        return 0
    
    try:
        # Step 1: Generate post-policy data for the target date
        logger.info("Step 1: Generating post-policy data...")
        claims_df = generate_post_policy_data(POLICY_EFFECTIVE_DATE, end_date, str(tenant_id))
        logger.info(f"✅ Generated {len(claims_df)} claims for {target_date.date()}")
        
        # Step 2: Load data via ingestion pipeline
        logger.info("Step 2: Loading data via ingestion pipeline...")
        success, ingestion_id = load_data_to_target_model_via_pipeline(claims_df, str(tenant_id))
        
        if not success:
            logger.error("❌ Failed to load data via ingestion pipeline")
            return 1
        
        logger.info(f"✅ Data ingested successfully. Ingestion ID: {ingestion_id}")
        
        # Step 3: Optionally run observation analysis
        if run_observations:
            logger.info("Step 3: Running observation analysis...")
            
            policies = get_all_policies()
            logger.info(f"Found {len(policies)} policies")
            
            for policy in policies:
                policy_id = UUID(policy.get("id") or policy.get("policy_id"))
                policy_name = policy.get("name") or policy.get("policy_name", "Unknown")
                
                logger.info(f"Processing policy: {policy_name} ({policy_id})")
                
                # Run impact analysis
                analysis_id, analysis_result = run_impact_analysis(
                    policy_id, POLICY_EFFECTIVE_DATE, tenant_id
                )
                
                if analysis_id:
                    # Create observation
                    observation_id, observation_result = create_observation_from_analysis(
                        policy_id, analysis_id, tenant_id
                    )
                    
                    if observation_id:
                        logger.info(f"✅ Created observation {observation_id} for policy {policy_name}")
                    else:
                        logger.warning(f"⚠️  Failed to create observation for policy {policy_name}")
                else:
                    logger.warning(f"⚠️  Failed to run impact analysis for policy {policy_name}")
        
        logger.info("="*60)
        logger.info("✅ DAILY JOB COMPLETE")
        logger.info("="*60)
        return 0
        
    except Exception as e:
        logger.error(f"❌ Daily job failed: {e}", exc_info=True)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Daily job to generate and ingest post-policy data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run for yesterday (default)
  python scripts/daily_post_policy_job.py
  
  # Run for specific date
  python scripts/daily_post_policy_job.py --date 2026-01-15
  
  # Run with observation analysis
  python scripts/daily_post_policy_job.py --run-observations
  
  # Schedule via cron (daily at 2 AM)
  Add to crontab (crontab -e):
    0 2 * * * /path/to/venv/bin/python /path/to/scripts/daily_post_policy_job.py >> /var/log/uepi/daily_job.log 2>&1
        """
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target date (YYYY-MM-DD). Default: yesterday",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default=str(DEFAULT_TENANT_ID),
        help=f"Tenant ID (default: {DEFAULT_TENANT_ID})",
    )
    parser.add_argument(
        "--run-observations",
        action="store_true",
        help="Also run observation analysis after ingestion",
    )
    
    args = parser.parse_args()
    
    # Parse date
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Expected YYYY-MM-DD")
            return 1
    
    # Parse tenant ID
    try:
        tenant_id = UUID(args.tenant_id)
    except ValueError:
        logger.error(f"Invalid tenant ID: {args.tenant_id}")
        return 1
    
    # Ensure logs directory exists
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Run job
    return run_daily_job(
        target_date=target_date,
        tenant_id=tenant_id,
        run_observations=args.run_observations,
    )


if __name__ == "__main__":
    sys.exit(main())
