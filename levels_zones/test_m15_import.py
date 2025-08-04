"""
Test script to debug M15 zone calculator import issues
Run this from the levels_zones directory: python test_m15_import.py
"""

import sys
import os
from pathlib import Path

print("=" * 80)
print("M15 Zone Calculator Import Debug Test")
print("=" * 80)

# 1. Show current working directory
print(f"\n1. Current Working Directory:")
print(f"   {os.getcwd()}")

# 2. Show Python path
print(f"\n2. Python Path:")
for i, path in enumerate(sys.path):
    print(f"   [{i}] {path}")

# 3. Check if directories exist
print(f"\n3. Directory Structure Check:")
project_root = Path(__file__).parent
print(f"   Project root: {project_root}")

calc_dir = project_root / "calculations"
candlestick_dir = calc_dir / "candlestick"

print(f"   calculations/ exists: {calc_dir.exists()}")
print(f"   calculations/candlestick/ exists: {candlestick_dir.exists()}")

# 4. Check if files exist
print(f"\n4. File Existence Check:")
calc_init = calc_dir / "__init__.py"
candlestick_init = candlestick_dir / "__init__.py"
m15_file = candlestick_dir / "m15_zone_calc.py"

print(f"   calculations/__init__.py exists: {calc_init.exists()}")
print(f"   calculations/candlestick/__init__.py exists: {candlestick_init.exists()}")
print(f"   calculations/candlestick/m15_zone_calc.py exists: {m15_file.exists()}")

# 5. Try to create missing directories and files
print(f"\n5. Creating Missing Structure:")
if not calc_dir.exists():
    calc_dir.mkdir(parents=True)
    print(f"   Created: {calc_dir}")

if not candlestick_dir.exists():
    candlestick_dir.mkdir(parents=True)
    print(f"   Created: {candlestick_dir}")

if not calc_init.exists():
    calc_init.write_text('"""Calculation modules for Meridian Trading System"""')
    print(f"   Created: {calc_init}")

if not candlestick_init.exists():
    candlestick_init.write_text('"""Candlestick calculation modules"""')
    print(f"   Created: {candlestick_init}")

# 6. Create the m15_zone_calc.py if it doesn't exist
if not m15_file.exists():
    print(f"\n   WARNING: m15_zone_calc.py doesn't exist!")
    print(f"   Creating a minimal version for testing...")
    
    m15_content = '''"""
M15 Zone Candlestick Calculator - Test Version
"""

class M15ZoneCalculator:
    def __init__(self):
        print("M15ZoneCalculator initialized (test version)")
    
    def test_connection(self):
        return True, "Test connection successful"
    
    def fetch_all_zone_candles(self, ticker, zones):
        print(f"Would fetch candles for {ticker}")
        return [(i, None) for i in range(len(zones))]
'''
    m15_file.write_text(m15_content)
    print(f"   Created: {m15_file}")

# 7. Try different import methods
print(f"\n6. Import Tests:")

# Method 1: Direct import (after adding to path)
print(f"\n   Method 1 - Direct import with sys.path:")
try:
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from calculations.candlestick.m15_zone_calc import M15ZoneCalculator
    print(f"   ✓ SUCCESS: Direct import worked!")
    calculator = M15ZoneCalculator()
except Exception as e:
    print(f"   ✗ FAILED: {type(e).__name__}: {e}")

# Method 2: Using importlib
print(f"\n   Method 2 - Using importlib:")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "m15_zone_calc", 
        str(m15_file)
    )
    if spec and spec.loader:
        m15_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m15_module)
        M15ZoneCalculator2 = m15_module.M15ZoneCalculator
        print(f"   ✓ SUCCESS: importlib method worked!")
        calculator2 = M15ZoneCalculator2()
except Exception as e:
    print(f"   ✗ FAILED: {type(e).__name__}: {e}")

# Method 3: Relative to src/ui/widgets/overview_widget
print(f"\n   Method 3 - Simulating import from app_overview.py location:")
try:
    # Simulate being in the overview_widget directory
    overview_widget_dir = project_root / "src" / "ui" / "widgets" / "overview_widget"
    
    # Calculate relative path
    rel_path = os.path.relpath(project_root, overview_widget_dir)
    print(f"   Relative path from widget to root: {rel_path}")
    
    # This is what the import would need to do
    widget_sys_path = str(Path(overview_widget_dir) / rel_path)
    if widget_sys_path not in sys.path:
        sys.path.insert(0, widget_sys_path)
    
    # Try import again
    from calculations.candlestick.m15_zone_calc import M15ZoneCalculator as M15Calc3
    print(f"   ✓ SUCCESS: Relative import worked!")
except Exception as e:
    print(f"   ✗ FAILED: {type(e).__name__}: {e}")

# 8. Show final recommendations
print(f"\n7. Recommendations:")
print(f"   Based on the tests above, here's what should work:")

if 'M15ZoneCalculator' in locals():
    print(f"   ✓ The import is working when project root is in sys.path")
    print(f"   ✓ Make sure {project_root} is added to sys.path in main.py")
else:
    print(f"   ✗ Import is still failing - check the errors above")

print(f"\n8. Quick Fix for app_overview.py:")
print(f"   Add this before the import in _on_query_zone_data:")
print(f"""
    import sys
    from pathlib import Path
    # Navigate to project root
    widget_dir = Path(__file__).parent
    project_root = widget_dir.parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
""")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)