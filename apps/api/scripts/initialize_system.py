#!/usr/bin/env python3
"""
Main System Initialization Orchestrator
- Runs all setup steps in logical order
- Each step is a separate script for easier debugging
- Continues on non-critical errors
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
scripts_dir = current_dir / "scripts"
project_root = current_dir.parent.parent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Set environment variables
os.environ.setdefault('USE_FILE_STORAGE', 'false')
os.environ.setdefault('LOG_LEVEL', 'INFO')


def run_script(script_name: str, description: str, required: bool = True) -> bool:
    """Run a setup script and return success status"""
    script_path = scripts_dir / script_name
    
    if not script_path.exists():
        logger.error(f"❌ Script not found: {script_path}")
        return False if required else True
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"Running: {description}")
    logger.info("=" * 80)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            env=os.environ.copy(),
            capture_output=False,  # Show output in real-time
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {description} completed successfully")
            return True
        else:
            logger.error(f"❌ {description} failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running {script_name}: {e}", exc_info=True)
        return False


def main():
    """Main initialization function"""
    logger.info("=" * 80)
    logger.info("🚀 SYSTEM INITIALIZATION STARTING")
    logger.info("=" * 80)
    logger.info("")
    logger.info("This script orchestrates the following setup steps:")
    logger.info("  1. Database Setup (reset and create tables)")
    logger.info("  2. Setup Demo Tenant and User")
    logger.info("  3. Seed Predefined Policies")
    logger.info("  4. Seed Pipelines")
    logger.info("  5. Setup Source Data Directories")
    logger.info("  6. Verify System")
    logger.info("")
    
    # Run setup steps in order
    steps = [
        ("01_setup_database.py", "Database Setup", True),
        ("02_setup_tenant_user.py", "Setup Demo Tenant and User", True),
        ("03_seed_policies.py", "Seed Predefined Policies", False),  # Non-critical
        ("04_seed_pipelines.py", "Seed Pipelines", False),  # Non-critical
        ("05_setup_source_directories.py", "Setup Source Data Directories", False),  # Non-critical
        ("06_verify_system.py", "Verify System", False),  # Non-critical
    ]
    
    results = {}
    for script_name, description, required in steps:
        success = run_script(script_name, description, required)
        results[description] = success
        
        # Stop on critical failures
        if required and not success:
            logger.error("")
            logger.error("=" * 80)
            logger.error("❌ CRITICAL STEP FAILED - Stopping initialization")
            logger.error("=" * 80)
            return 1
    
    # Final summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎉 SYSTEM INITIALIZATION COMPLETE")
    logger.info("=" * 80)
    logger.info("Results:")
    for step, result in results.items():
        status_icon = "✅" if result else "❌"
        logger.info(f"   {status_icon} {step}")
    logger.info("")
    
    # Check if all critical steps passed
    critical_passed = all(
        result for (script, desc, required), result in zip(steps, results.values())
        if required
    )
    
    if critical_passed:
        logger.info("✅ Critical setup steps completed successfully!")
        logger.info("")
        logger.info("Next Steps:")
        logger.info("   1. Start API server: ./start_system.sh")
        logger.info("   2. Or start manually: cd apps/api && uvicorn uepi_api.main:app --reload")
        logger.info("   3. Access API docs: http://localhost:8000/docs")
        logger.info("")
        return 0
    else:
        logger.error("❌ Some critical setup steps failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
