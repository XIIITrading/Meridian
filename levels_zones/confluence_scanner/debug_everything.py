# debug_everything.py - Complete system check

import os
import sys
import importlib.util
from pathlib import Path

print("="*60)
print("COMPLETE CONFLUENCE SCANNER DEBUG")
print("="*60)

# Get current directory
current_dir = Path.cwd()
print(f"\n📁 Current Directory: {current_dir}")

# Check directory structure
print("\n📂 Directory Structure Check:")
required_dirs = [
    'scanner',
    'data', 
    'discovery',
    'calculations',
    'calculations/volume',
    'calculations/pivots',
    'calculations/zones'
]

for dir_name in required_dirs:
    dir_path = current_dir / dir_name
    exists = dir_path.exists()
    print(f"  {'✓' if exists else '✗'} {dir_name}: {'exists' if exists else 'MISSING'}")
    if not exists:
        os.makedirs(dir_path, exist_ok=True)
        print(f"    → Created {dir_name}")

# Check for __init__.py files
print("\n📄 Python Package Structure:")
init_files = [
    'calculations/__init__.py',
    'calculations/volume/__init__.py',
    'calculations/pivots/__init__.py',
    'calculations/zones/__init__.py'
]

for init_file in init_files:
    file_path = current_dir / init_file
    exists = file_path.exists()
    print(f"  {'✓' if exists else '✗'} {init_file}: {'exists' if exists else 'MISSING'}")
    if not exists:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        print(f"    → Created {init_file}")

# Check required module files
print("\n📋 Required Module Files:")
module_files = [
    ('data/polygon_client.py', True),
    ('data/market_metrics.py', True),
    ('scanner/zone_scanner.py', True),
    ('discovery/zone_discovery.py', True),
    ('calculations/volume/hvn_engine.py', False),
    ('calculations/volume/volume_profile.py', False),
    ('calculations/pivots/camarilla_engine.py', False),
    ('cli.py', True)
]

missing_critical = []
for file_path, is_critical in module_files:
    full_path = current_dir / file_path
    exists = full_path.exists()
    status = 'exists' if exists else ('CRITICAL - MISSING' if is_critical else 'MISSING')
    print(f"  {'✓' if exists else '✗'} {file_path}: {status}")
    if not exists and is_critical:
        missing_critical.append(file_path)

# Test imports
print("\n🔧 Testing Imports:")
sys.path.insert(0, str(current_dir))

imports_to_test = [
    ('data.polygon_client', 'PolygonClient'),
    ('data.market_metrics', 'MetricsCalculator'),
    ('discovery.zone_discovery', 'ZoneDiscoveryEngine'),
    ('scanner.zone_scanner', 'ZoneScanner'),
    ('calculations.volume.hvn_engine', 'HVNEngine'),
    ('calculations.volume.volume_profile', 'VolumeProfile'),
    ('calculations.pivots.camarilla_engine', 'CamarillaEngine')
]

failed_imports = []
for module_name, class_name in imports_to_test:
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, class_name):
            print(f"  ✓ {module_name}.{class_name}")
        else:
            print(f"  ⚠️ {module_name} imported but {class_name} not found")
            failed_imports.append(module_name)
    except ImportError as e:
        print(f"  ✗ {module_name}: {str(e)}")
        failed_imports.append(module_name)

# Quick functional test
print("\n🧪 Functional Test:")
if not failed_imports:
    try:
        from scanner.zone_scanner import ZoneScanner
        scanner = ZoneScanner()
        print("  ✓ ZoneScanner initialized successfully")
        
        # Test connection
        success, msg = scanner.initialize()
        print(f"  {'✓' if success else '✗'} Polygon connection: {msg}")
        
    except Exception as e:
        print(f"  ✗ Scanner initialization failed: {e}")

# Summary and recommendations
print("\n" + "="*60)
print("DIAGNOSIS & RECOMMENDATIONS")
print("="*60)

if missing_critical:
    print("\n❌ Critical files missing:")
    for file in missing_critical:
        print(f"  - {file}")
    print("\n  Action: These files must exist for the scanner to work")

if failed_imports:
    print("\n❌ Failed imports:")
    for module in failed_imports:
        print(f"  - {module}")
    
    if 'calculations.volume.hvn_engine' in failed_imports:
        print("\n  Fix: The calculation modules aren't being found.")
        print("  Options:")
        print("  1. Move calculation files from levels_zones/calculations/")
        print("  2. Or create simplified versions in confluence_scanner/calculations/")
        print("  3. Or remove these imports from zone_scanner.py for now")

if not missing_critical and not failed_imports:
    print("\n✅ All checks passed! Scanner should be ready to run.")
else:
    print("\n📝 Quick Fix Script:")
    print("Run this to create a minimal working version:\n")
    print("python create_minimal_scanner.py")