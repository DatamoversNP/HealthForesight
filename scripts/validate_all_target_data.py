#!/usr/bin/env python3
"""
Validate All Target Data
Validates all consolidated target data model files
"""
import sys
import os
from pathlib import Path
from uuid import UUID
import json
import subprocess

# Use API's poetry environment to run validation
API_DIR = Path(__file__).parent.parent / "apps" / "api"

# Default tenant ID (for demo)
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# Target data root (check both locations)
PROJECT_ROOT = Path(__file__).parent.parent
TARGET_DATA_ROOT = PROJECT_ROOT / "data" / "target_data_model"
# Also check apps/data (legacy location)
TARGET_DATA_ROOT_LEGACY = PROJECT_ROOT / "apps" / "data" / "target_data_model"


def validate_all():
    """Validate all target data files using API's poetry environment"""
    print("🔍 Validating All Target Data")
    print("=" * 60)
    
    if not TARGET_DATA_ROOT.exists():
        print(f"❌ Target data directory not found: {TARGET_DATA_ROOT}")
        return
    
    # Create a Python script to run validation in API's environment
    validation_script = f"""
import sys
from pathlib import Path
from uuid import UUID
import json

# Add paths
sys.path.insert(0, '{Path(__file__).parent.parent / "packages/common/src"}')
sys.path.insert(0, '{Path(__file__).parent.parent / "apps/api/src"}')

from uepi_common.ingestion.target_data_validator import TargetDataValidator

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
TARGET_DATA_ROOT = Path("{TARGET_DATA_ROOT}")
TARGET_DATA_ROOT_LEGACY = Path("{TARGET_DATA_ROOT_LEGACY}")

validator = TargetDataValidator(DEFAULT_TENANT_ID)
# Try legacy location first (where files actually are), then project root
reports = {{}}
if TARGET_DATA_ROOT_LEGACY.exists():
    reports = validator.validate_all_target_data(TARGET_DATA_ROOT_LEGACY)
elif TARGET_DATA_ROOT.exists():
    reports = validator.validate_all_target_data(TARGET_DATA_ROOT)

# Convert reports to dict for JSON serialization
report_data = {{
    "generated_at": reports[list(reports.keys())[0]].generated_at.isoformat() if reports else None,
    "datasets": {{
        dataset_type: {{
            "quality_score": report.quality_score,
            "completeness_score": report.completeness_score,
            "validity_score": report.validity_score,
            "uniqueness_score": report.uniqueness_score,
            "total_rows": report.total_rows,
            "valid_rows": report.valid_rows,
            "invalid_rows": report.invalid_rows,
            "issues_count": len(report.issues),
            "issues": [
                {{
                    "check_type": issue.check_type.value,
                    "severity": issue.severity.value,
                    "field_name": issue.field_name,
                    "issue_description": issue.issue_description,
                    "affected_rows": issue.affected_rows,
                }}
                for issue in report.issues
            ],
        }}
        for dataset_type, report in reports.items()
    }},
}}

# Print results
print(f"Total datasets validated: {{len(reports)}}")
passed = sum(1 for r in reports.values() if r.quality_score >= 0.8)
warning = sum(1 for r in reports.values() if 0.6 <= r.quality_score < 0.8)
failed = sum(1 for r in reports.values() if r.quality_score < 0.6)
print(f"Passed (≥80%): {{passed}}")
print(f"Warning (60-79%): {{warning}}")
print(f"Failed (<60%): {{failed}}")

# Save report
report_file = TARGET_DATA_ROOT / "validation_report.json"
with open(report_file, 'w') as f:
    json.dump(report_data, f, indent=2)
print(f"Report saved to: {{report_file}}")

# Print detailed results
for dataset_type, report in sorted(reports.items()):
    status = "PASSED" if report.quality_score >= 0.8 else "WARNING" if report.quality_score >= 0.6 else "FAILED"
    print(f"\\n{{dataset_type}} ({{status}}):")
    print(f"  Quality Score: {{report.quality_score:.2%}}")
    print(f"  Issues: {{len(report.issues)}}")
    for issue in report.issues[:3]:
        print(f"    - {{issue.check_type.value}}: {{issue.issue_description[:60]}}")
"""
    
    # Run validation using API's poetry environment
    try:
        result = subprocess.run(
            ["poetry", "run", "python", "-c", validation_script],
            cwd=API_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ Validation failed: {e}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Poetry not found. Please run validation from API directory or install poetry.")
        sys.exit(1)


if __name__ == "__main__":
    validate_all()

