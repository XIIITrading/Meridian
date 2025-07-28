#!/usr/bin/env python3
"""
git_commit.py
Git automation script for XIIITradingSystems Meridian
Run from: C:\XIIITradingSystems\Meridian\execute
Pushes to: https://github.com/XIIITrading/Meridian.git
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
import logging
import re

def setup_logging():
    """Setup logging for git operations"""
    script_dir = Path(__file__).parent
    log_file = script_dir / 'git_operations.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def get_repo_directory():
    """Get the repository root directory"""
    # This script is in execute/, repo root is ../
    script_dir = Path(__file__).parent
    repo_dir = script_dir.parent
    
    if not (repo_dir / '.git').exists():
        # Fallback to absolute path
        repo_dir = Path(r"C:\XIIITradingSystems\Meridian")
    
    return repo_dir

def run_git_command(command, cwd=None):
    """Run a git command and return the result"""
    if cwd is None:
        cwd = get_repo_directory()
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=True,
            check=False
        )
        
        logging.debug(f"Command: {command}")
        logging.debug(f"Return code: {result.returncode}")
        logging.debug(f"Stdout: {result.stdout}")
        if result.stderr:
            logging.debug(f"Stderr: {result.stderr}")
        
        return result
    except Exception as e:
        logging.error(f"Error running git command '{command}': {e}")
        return None

def check_git_status():
    """Check the current git status"""
    logging.info("[STATUS] Checking git status...")
    
    result = run_git_command("git status --porcelain")
    if result is None:
        return False, []
    
    if result.returncode != 0:
        logging.error("Failed to get git status")
        return False, []
    
    changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
    
    if changes:
        logging.info(f"Found {len(changes)} changes:")
        for change in changes[:10]:  # Show first 10 changes
            logging.info(f"  {change}")
        if len(changes) > 10:
            logging.info(f"  ... and {len(changes) - 10} more changes")
    else:
        logging.info("No changes detected")
    
    return True, changes

def check_remote_origin():
    """Check if remote origin is set correctly"""
    logging.info("[REMOTE] Checking remote origin...")
    
    result = run_git_command("git remote get-url origin")
    if result is None or result.returncode != 0:
        logging.warning("No remote origin found, setting it up...")
        setup_result = run_git_command("git remote add origin https://github.com/XIIITrading/Meridian.git")
        if setup_result and setup_result.returncode == 0:
            logging.info("[SUCCESS] Remote origin added successfully")
            return True
        else:
            logging.error("[ERROR] Failed to add remote origin")
            return False
    
    remote_url = result.stdout.strip()
    expected_url = "https://github.com/XIIITrading/Meridian.git"
    
    if remote_url != expected_url:
        logging.warning(f"Remote origin mismatch. Current: {remote_url}, Expected: {expected_url}")
        fix_result = run_git_command(f"git remote set-url origin {expected_url}")
        if fix_result and fix_result.returncode == 0:
            logging.info("[SUCCESS] Remote origin updated successfully")
        else:
            logging.error("[ERROR] Failed to update remote origin")
            return False
    else:
        logging.info("[SUCCESS] Remote origin is correctly set")
    
    return True

def get_current_branch():
    """Get the current git branch"""
    result = run_git_command("git branch --show-current")
    if result and result.returncode == 0:
        return result.stdout.strip()
    return "main"  # fallback

def generate_commit_message(message_type="update"):
    """Generate a commit message based on type and timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    message_templates = {
        "update": f"Update trading systems - {timestamp}",
        "feature": f"Add new feature - {timestamp}",
        "fix": f"Bug fixes and improvements - {timestamp}",
        "data": f"Update data and configurations - {timestamp}",
        "clean": f"Clean up and maintenance - {timestamp}",
        "strategy": f"Strategy updates - {timestamp}",
        "scanner": f"Scanner improvements - {timestamp}"
    }
    
    return message_templates.get(message_type, f"Update - {timestamp}")

def check_for_sensitive_files():
    """Check for potentially sensitive files that shouldn't be committed"""
    sensitive_patterns = [
        "*.key",
        "*.pem", 
        "*api_key*",
        "*secret*",
        "*password*",
        "*.env",
        "*credentials*",
        "*token*"
    ]
    
    repo_dir = get_repo_directory()
    sensitive_files = []
    
    for pattern in sensitive_patterns:
        for file_path in repo_dir.glob(f"**/{pattern}"):
            if file_path.is_file():
                sensitive_files.append(file_path.relative_to(repo_dir))
    
    if sensitive_files:
        logging.warning("[WARNING] Potentially sensitive files detected:")
        for file_path in sensitive_files:
            logging.warning(f"   {file_path}")
        return sensitive_files
    
    return []

def update_gitignore():
    """Update .gitignore with trading-specific patterns"""
    repo_dir = get_repo_directory()
    gitignore_path = repo_dir / '.gitignore'
    
    trading_patterns = [
        "# Trading System Ignores",
        "*.parquet",
        "*.pkl", 
        "*.cache",
        "polygon/*.parquet",
        "polygon/*.pkl",
        "polygon/*.cache",
        "polygon/**/*.parquet",
        "polygon/**/*.pkl",
        "polygon/**/*.cache",
        "polygon/temp/",
        "polygon/cache/",
        "*.log",
        "*.tmp",
        "*.temp",
        "__pycache__/",
        "*.pyc",
        ".env",
        "*api_key*",
        "*secret*",
        "*credentials*",
        ".DS_Store",
        "Thumbs.db",
        "*.swp",
        ".vscode/settings.json",
        "execute/polygon_cleanup.log",
        "execute/git_operations.log"
    ]
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Add patterns that don't exist
        new_patterns = []
        for pattern in trading_patterns:
            if pattern not in existing_content:
                new_patterns.append(pattern)
        
        if new_patterns:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write('\n' + '\n'.join(new_patterns) + '\n')
            logging.info(f"[SUCCESS] Added {len(new_patterns)} new patterns to .gitignore")
    else:
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(trading_patterns) + '\n')
        logging.info("[SUCCESS] Created new .gitignore file")

def commit_and_push(commit_message, dry_run=False, force_push=False):
    """Perform git add, commit, and push operations"""
    repo_dir = get_repo_directory()
    branch = get_current_branch()
    
    if dry_run:
        logging.info("[DRY RUN] No actual git operations will be performed")
    
    # Step 1: Add all changes
    logging.info("[ADD] Adding all changes...")
    if not dry_run:
        result = run_git_command("git add .")
        if result is None or result.returncode != 0:
            logging.error("[ERROR] Failed to add changes")
            return False
    logging.info("[SUCCESS] Changes added successfully")
    
    # Step 2: Commit
    logging.info(f"[COMMIT] Committing with message: '{commit_message}'")
    if not dry_run:
        commit_cmd = f'git commit -m "{commit_message}"'
        result = run_git_command(commit_cmd)
        if result is None or result.returncode != 0:
            if result and "nothing to commit" in result.stdout:
                logging.info("[INFO] Nothing to commit, working tree clean")
                return True
            else:
                logging.error("[ERROR] Failed to commit changes")
                return False
    logging.info("[SUCCESS] Changes committed successfully")
    
    # Step 3: Push
    push_cmd = f"git push origin {branch}"
    if force_push:
        push_cmd += " --force"
    
    logging.info(f"[PUSH] Pushing to GitHub ({branch} branch)...")
    if not dry_run:
        result = run_git_command(push_cmd)
        if result is None or result.returncode != 0:
            logging.error("[ERROR] Failed to push to GitHub")
            if result and result.stderr:
                logging.error(f"Error details: {result.stderr}")
            return False
    logging.info("[SUCCESS] Successfully pushed to GitHub!")
    
    return True

def show_repo_info():
    """Show repository information"""
    logging.info("[INFO] Repository Information:")
    
    # Current branch
    branch = get_current_branch()
    logging.info(f"   Current branch: {branch}")
    
    # Last commit
    result = run_git_command("git log -1 --oneline")
    if result and result.returncode == 0:
        logging.info(f"   Last commit: {result.stdout.strip()}")
    
    # Remote info
    result = run_git_command("git remote get-url origin")
    if result and result.returncode == 0:
        logging.info(f"   Remote origin: {result.stdout.strip()}")
    
    # Repo directory
    logging.info(f"   Repository path: {get_repo_directory()}")

def main():
    parser = argparse.ArgumentParser(
        description='Git commit and push automation for Meridian trading system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python git_commit.py                              # Interactive commit
  python git_commit.py -m "Update scanner logic"   # Quick commit with message
  python git_commit.py --type strategy             # Use strategy template
  python git_commit.py --dry-run                   # See what would happen
  python git_commit.py --clean-first               # Clean polygon data first
  python git_commit.py --info                      # Show repo information
        """
    )
    
    parser.add_argument('-m', '--message', type=str,
                       help='Custom commit message')
    parser.add_argument('--type', choices=['update', 'feature', 'fix', 'data', 'clean', 'strategy', 'scanner'],
                       default='update', help='Type of commit (affects message template)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without doing it')
    parser.add_argument('--force', action='store_true',
                       help='Force push (use with caution)')
    parser.add_argument('--clean-first', action='store_true',
                       help='Run polygon cleaner before committing')
    parser.add_argument('--info', action='store_true',
                       help='Show repository info and exit')
    parser.add_argument('--skip-sensitive-check', action='store_true',
                       help='Skip check for sensitive files')
    
    args = parser.parse_args()
    
    setup_logging()
    
    logging.info("[START] Starting Git Commit & Push Automation")
    logging.info(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show info and exit if requested
    if args.info:
        show_repo_info()
        return
    
    # Clean polygon data first if requested
    if args.clean_first:
        logging.info("[CLEAN] Running polygon cleaner first...")
        try:
            from run_polygon_cleaner import clean_polygon_directory
            clean_polygon_directory(days_to_keep=7, dry_run=False)
        except ImportError:
            logging.warning("Could not import polygon cleaner, skipping...")
    
    # Check if we're in a git repository
    repo_dir = get_repo_directory()
    if not (repo_dir / '.git').exists():
        logging.error(f"[ERROR] No git repository found at {repo_dir}")
        sys.exit(1)
    
    # Update .gitignore
    update_gitignore()
    
    # Check git status
    status_ok, changes = check_git_status()
    if not status_ok:
        sys.exit(1)
    
    if not changes and not args.dry_run:
        logging.info("[INFO] No changes to commit")
        return
    
    # Check for sensitive files
    if not args.skip_sensitive_check:
        sensitive_files = check_for_sensitive_files()
        if sensitive_files and not args.dry_run:
            response = input("Sensitive files detected. Continue anyway? (y/N): ")
            if response.lower() != 'y':
                logging.info("Commit cancelled by user")
                return
    
    # Check remote origin
    if not check_remote_origin():
        sys.exit(1)
    
    # Get commit message
    if args.message:
        commit_message = args.message
    else:
        if not args.dry_run:
            # Interactive mode
            suggested_message = generate_commit_message(args.type)
            print(f"\nSuggested commit message: {suggested_message}")
            user_message = input("Enter commit message (or press Enter to use suggested): ").strip()
            commit_message = user_message if user_message else suggested_message
        else:
            commit_message = generate_commit_message(args.type)
    
    logging.info(f"[MESSAGE] Commit message: '{commit_message}'")
    
    # Perform the commit and push
    success = commit_and_push(commit_message, args.dry_run, args.force)
    
    if success:
        logging.info("[COMPLETE] Git operations completed successfully!")
        if not args.dry_run:
            logging.info(f"[LINK] View at: https://github.com/XIIITrading/Meridian")
    else:
        logging.error("[FAILED] Git operations failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()