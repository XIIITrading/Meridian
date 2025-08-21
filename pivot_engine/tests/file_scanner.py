"""
File Scanner: Find all PriceLevel imports
This will help us identify exactly which files need to be updated
"""

import os
from pathlib import Path

project_root = Path(__file__).parent.parent

def scan_for_pricelevel_imports():
    """Scan all Python files for PriceLevel imports"""
    print("🔍 Scanning for PriceLevel imports...")
    
    # File extensions to scan
    extensions = ['.py']
    
    # Find all Python files
    python_files = []
    for ext in extensions:
        python_files.extend(project_root.rglob(f'*{ext}'))
    
    # Files with PriceLevel imports
    files_with_imports = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if 'PriceLevel' in line and ('import' in line or 'from' in line):
                        relative_path = file_path.relative_to(project_root)
                        files_with_imports.append({
                            'file': str(relative_path),
                            'line': line_num,
                            'content': line.strip()
                        })
                        print(f"📄 {relative_path}:{line_num}")
                        print(f"   {line.strip()}")
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
    
    return files_with_imports

def scan_for_pricelevel_usage():
    """Scan for PriceLevel usage (not just imports)"""
    print("\n🔍 Scanning for PriceLevel usage...")
    
    python_files = list(project_root.rglob('*.py'))
    files_with_usage = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if 'PriceLevel' in line and not line.strip().startswith('#'):
                        relative_path = file_path.relative_to(project_root)
                        files_with_usage.append({
                            'file': str(relative_path),
                            'line': line_num,
                            'content': line.strip()
                        })
        except Exception as e:
            continue
    
    # Group by file
    grouped = {}
    for usage in files_with_usage:
        file_name = usage['file']
        if file_name not in grouped:
            grouped[file_name] = []
        grouped[file_name].append(usage)
    
    # Display results
    for file_name, usages in grouped.items():
        print(f"\n📄 {file_name} ({len(usages)} occurrences)")
        for usage in usages[:5]:  # Show first 5
            print(f"   Line {usage['line']}: {usage['content']}")
        if len(usages) > 5:
            print(f"   ... and {len(usages) - 5} more")
    
    return grouped

if __name__ == "__main__":
    print("=" * 70)
    print("PRICELEVEL DEPENDENCY SCANNER")
    print("=" * 70)
    
    import_files = scan_for_pricelevel_imports()
    usage_files = scan_for_pricelevel_usage()
    
    print(f"\n📊 SUMMARY:")
    print(f"   Files with PriceLevel imports: {len(import_files)}")
    print(f"   Files with PriceLevel usage: {len(usage_files)}")
    
    print(f"\n🎯 FILES TO UPDATE:")
    all_files = set()
    for item in import_files:
        all_files.add(item['file'])
    for file_name in usage_files.keys():
        all_files.add(file_name)
    
    for i, file_name in enumerate(sorted(all_files), 1):
        print(f"   {i}. {file_name}")
    
    print("=" * 70)