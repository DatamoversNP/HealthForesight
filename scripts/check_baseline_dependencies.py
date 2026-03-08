#!/usr/bin/env python3
"""
Check if all dependencies for baseline analysis are available
"""
import sys
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

print("="*60)
print("Baseline Analysis Dependency Check")
print("="*60)
print()

dependencies = {
    "pandas": None,
    "numpy": None,
    "scipy": None,
    "sklearn": None,
    "statsmodels": None,
}

missing = []
available = []

# Check each dependency
for dep_name in dependencies.keys():
    try:
        if dep_name == "sklearn":
            import sklearn
            version = getattr(sklearn, "__version__", "unknown")
        elif dep_name == "scipy":
            import scipy
            version = getattr(scipy, "__version__", "unknown")
        elif dep_name == "statsmodels":
            import statsmodels
            version = getattr(statsmodels, "__version__", "unknown")
        elif dep_name == "numpy":
            import numpy
            version = getattr(numpy, "__version__", "unknown")
        elif dep_name == "pandas":
            import pandas
            version = getattr(pandas, "__version__", "unknown")
        
        print(f"✅ {dep_name}: available (version: {version})")
        available.append(dep_name)
    except ImportError as e:
        print(f"❌ {dep_name}: MISSING - {e}")
        missing.append(dep_name)

print()
print("="*60)
print("Summary")
print("="*60)
print(f"Available: {len(available)}/{len(dependencies)}")
print(f"Missing: {len(missing)}/{len(dependencies)}")

if missing:
    print(f"\n❌ Missing dependencies: {', '.join(missing)}")
    print(f"\nTo install missing dependencies:")
    if "scipy" in missing:
        print("  pip install scipy")
    if "sklearn" in missing:
        print("  pip install scikit-learn")
    if "statsmodels" in missing:
        print("  pip install statsmodels")
    if "pandas" in missing:
        print("  pip install pandas")
    if "numpy" in missing:
        print("  pip install numpy")
    sys.exit(1)
else:
    print("\n✅ All dependencies are available!")
    
    # Try importing BaselineAnalysisEngine
    print("\nTesting BaselineAnalysisEngine import...")
    try:
        from uepi_common.analytics.baseline import BaselineAnalysisEngine
        print("✅ BaselineAnalysisEngine imported successfully!")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Failed to import BaselineAnalysisEngine: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
