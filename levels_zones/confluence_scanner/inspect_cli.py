# inspect_cli.py
import inspect
from cli import ZoneScannerCLI

# Create CLI instance
cli = ZoneScannerCLI()

# Find the scan execution
import ast
import os

# Read cli.py and find what parameters it passes to scan()
with open('cli.py', 'r') as f:
    content = f.read()
    
# Find all scan() calls
import re
pattern = r'scanner\.scan\((.*?)\)'
matches = re.findall(pattern, content, re.DOTALL)

print("CLI calls scanner.scan() with these parameters:")
for match in matches[:2]:  # Show first 2 occurrences
    print(f"\n{match}")

# Also check what run_scan expects
from cli import ZoneScannerCLI
import inspect

print("\n" + "="*50)
print("CLI's run_scan method signature:")
sig = inspect.signature(ZoneScannerCLI.run_scan)
print(sig)