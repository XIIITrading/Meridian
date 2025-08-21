"""
Debug Script 3: File Structure Validation
Validates that all expected files exist and are properly structured
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent

def check_file_structure():
    """Check that all expected files exist"""
    print("🔍 Checking File Structure...")
    
    expected_files = {
        # Core calculation files
        "calculations/pivots/camarilla_engine.py": "Camarilla calculation engine",
        "calculations/confluence/pivot_confluence_engine.py": "Pivot confluence engine", 
        "calculations/volume/hvn_engine.py": "HVN calculation engine",
        "calculations/zones/weekly_zone_calc.py": "Weekly zone calculator",
        "calculations/zones/daily_zone_calc.py": "Daily zone calculator",
        "calculations/zones/atr_zone_calc.py": "ATR zone calculator",
        
        # UI files
        "src/ui/widgets/overview_widget/pivot_confluence_widget.py": "Pivot confluence widget",
        "src/ui/widgets/overview_widget/app_overview.py": "Main overview widget",
        "src/ui/threads/analysis_thread.py": "Analysis thread",
        
        # Data files
        "src/data/models.py": "Data models",
        "src/data/supabase_client.py": "Supabase client", 
        "src/data/validators.py": "Data validators",
        
        # Service files
        "src/services/database_service.py": "Database service",
    }
    
    missing_files = []
    existing_files = []
    
    for file_path, description in expected_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            existing_files.append((file_path, description))
            print(f"✅ {file_path} - {description}")
        else:
            missing_files.append((file_path, description))
            print(f"❌ {file_path} - {description} [MISSING]")
    
    print(f"\n📊 File Structure Summary:")
    print(f"   Existing files: {len(existing_files)}")
    print(f"   Missing files: {len(missing_files)}")
    
    return len(missing_files) == 0

def check_deprecated_files():
    """Check for deprecated M15 files that should be removed"""
    print("\n🔍 Checking for Deprecated Files...")
    
    deprecated_patterns = [
        "**/m15_zone*.py",
        "**/M15Zone*.py", 
        "**/m15_*.py"
    ]
    
    deprecated_found = []
    
    for pattern in deprecated_patterns:
        matches = list(project_root.rglob(pattern))
        for match in matches:
            relative_path = match.relative_to(project_root)
            deprecated_found.append(str(relative_path))
            print(f"⚠️  Deprecated file found: {relative_path}")
    
    if not deprecated_found:
        print("✅ No deprecated M15 files found")
        return True
    else:
        print(f"\n❌ Found {len(deprecated_found)} deprecated files")
        return False

def check_init_files():
    """Check that __init__.py files exist where needed"""
    print("\n🔍 Checking __init__.py Files...")
    
    required_init_dirs = [
        "calculations",
        "calculations/pivots",
        "calculations/confluence", 
        "calculations/volume",
        "calculations/zones",
        "src",
        "src/data",
        "src/ui",
        "src/ui/widgets",
        "src/ui/widgets/overview_widget",
        "src/ui/threads",
        "src/services",
        "tests"
    ]
    
    missing_inits = []
    
    for dir_path in required_init_dirs:
        init_path = project_root / dir_path / "__init__.py"
        if init_path.exists():
            print(f"✅ {dir_path}/__init__.py")
        else:
            missing_inits.append(dir_path)
            print(f"❌ {dir_path}/__init__.py [MISSING]")
    
    if missing_inits:
        print(f"\n⚠️  Missing {len(missing_inits)} __init__.py files")
        print("   This may cause import issues")
        return False
    else:
        print("✅ All required __init__.py files present")
        return True

def check_project_structure():
    """Check overall project structure"""
    print("\n🔍 Checking Project Structure...")
    
    required_dirs = [
        "calculations",
        "src",
        "tests", 
        "docs"
    ]
    
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.is_dir():
            print(f"✅ {dir_name}/ directory exists")
        else:
            missing_dirs.append(dir_name)
            print(f"❌ {dir_name}/ directory missing")
    
    return len(missing_dirs) == 0

if __name__ == "__main__":
    print("=" * 70)
    print("PIVOT ENGINE DEBUG: File Structure Validation")
    print("=" * 70)
    print(f"Project root: {project_root}")
    
    structure_ok = check_project_structure()
    files_ok = check_file_structure()
    deprecated_ok = check_deprecated_files()
    init_ok = check_init_files()
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"Project Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"Required Files: {'✅ PASS' if files_ok else '❌ FAIL'}")
    print(f"Deprecated Cleanup: {'✅ PASS' if deprecated_ok else '❌ FAIL'}")
    print(f"Init Files: {'✅ PASS' if init_ok else '❌ FAIL'}")
    
    if all([structure_ok, files_ok, deprecated_ok, init_ok]):
        print("\n🎉 FILE STRUCTURE VALIDATION PASSED!")
        print("   Project structure is properly organized")
    else:
        print("\n🚨 FILE STRUCTURE ISSUES FOUND")
        print("   Review missing files and deprecated components above")
    
    print("=" * 70)