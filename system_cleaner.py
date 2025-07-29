#!/usr/bin/env python3
"""
System Cleaner for Trading Data Files
Modular cleaner for removing cache and data files from trading directories.
"""

import os
import glob
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_cleaner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Modular configuration - easy to add new directories
CLEANUP_CONFIG = {
    'polygon': {
        'path': './polygon/',
        'patterns': ['*.parquet', '*cache*', '*.tmp', '*.log']
    }
    # Add more directories here as needed:
    # 'alpha_vantage': {
    #     'path': './alpha_vantage/',
    #     'patterns': ['*.json', '*cache*']
    # },
    # 'yahoo_finance': {
    #     'path': './yahoo_finance/',
    #     'patterns': ['*.csv', '*cache*']
    # }
}

def get_current_date() -> str:
    """
    Get current date string in YYYY-MM-DD format.
    
    Returns:
        str: Current date in YYYY-MM-DD format
    """
    return datetime.now().strftime('%Y-%m-%d')

def is_current_day_file(filepath: str, current_date: str) -> bool:
    """
    Check if file belongs to current trading day.
    
    Determines if file is from today by checking:
    1. If today's date appears in filename
    2. If file was modified today
    
    Args:
        filepath: Path to the file
        current_date: Current date string (YYYY-MM-DD)
    
    Returns:
        bool: True if file is from current day
    """
    # Check if current date is in filename
    if current_date in filepath:
        return True
    
    # Check if file was modified today
    try:
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        file_date = file_mod_time.strftime('%Y-%m-%d')
        return file_date == current_date
    except (OSError, ValueError):
        # If we can't determine, assume it's not current day
        return False

def find_files_by_patterns(directory: str, patterns: List[str]) -> List[str]:
    """
    Find all files matching specified patterns in directory and subdirectories.
    
    Args:
        directory: Directory to search in
        patterns: List of glob patterns (e.g., ['*.parquet', '*cache*'])
    
    Returns:
        List[str]: List of file paths that match any pattern
    """
    files = []
    
    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return files
    
    for pattern in patterns:
        # Search recursively using ** for subdirectories
        search_pattern = os.path.join(directory, '**', pattern)
        matched_files = glob.glob(search_pattern, recursive=True)
        files.extend(matched_files)
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(files))

def categorize_files(files: List[str], current_date: str) -> Tuple[List[str], List[str]]:
    """
    Separate files into current day vs prior day categories.
    
    Args:
        files: List of file paths
        current_date: Current date string (YYYY-MM-DD)
    
    Returns:
        Tuple[List[str], List[str]]: (current_day_files, prior_day_files)
    """
    current_day_files = []
    prior_day_files = []
    
    for filepath in files:
        if is_current_day_file(filepath, current_date):
            current_day_files.append(filepath)
        else:
            prior_day_files.append(filepath)
    
    return current_day_files, prior_day_files

def delete_files(files: List[str], dry_run: bool = False) -> int:
    """
    Safely delete files with logging and error handling.
    
    Args:
        files: List of file paths to delete
        dry_run: If True, only show what would be deleted without actually deleting
    
    Returns:
        int: Number of files successfully deleted (or would be deleted in dry run)
    """
    deleted_count = 0
    
    for filepath in files:
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would delete: {filepath}")
                deleted_count += 1
            else:
                os.remove(filepath)
                logger.info(f"Deleted: {filepath}")
                deleted_count += 1
        except OSError as e:
            logger.error(f"Error deleting {filepath}: {e}")
    
    return deleted_count

def get_directory_stats(directory_name: str, config: Dict) -> Dict:
    """
    Get statistics about files in a directory.
    
    Args:
        directory_name: Name of directory in config
        config: Directory configuration
    
    Returns:
        Dict: Statistics including file counts and sizes
    """
    directory = config['path']
    patterns = config['patterns']
    current_date = get_current_date()
    
    files = find_files_by_patterns(directory, patterns)
    current_day_files, prior_day_files = categorize_files(files, current_date)
    
    # Calculate sizes
    def get_total_size(file_list):
        total = 0
        for f in file_list:
            try:
                total += os.path.getsize(f)
            except OSError:
                pass
        return total
    
    return {
        'directory': directory_name,
        'total_files': len(files),
        'current_day_files': len(current_day_files),
        'prior_day_files': len(prior_day_files),
        'total_size_mb': round(get_total_size(files) / (1024*1024), 2),
        'current_day_list': current_day_files,
        'prior_day_list': prior_day_files
    }

def display_cleanup_summary():
    """Display summary of what would be cleaned for each configured directory."""
    print("\n" + "="*60)
    print("SYSTEM CLEANER - CLEANUP SUMMARY")
    print("="*60)
    
    for dir_name, config in CLEANUP_CONFIG.items():
        stats = get_directory_stats(dir_name, config)
        
        print(f"\nDirectory: {stats['directory']}")
        print(f"  Total files found: {stats['total_files']}")
        print(f"  Current day files: {stats['current_day_files']}")
        print(f"  Prior day files: {stats['prior_day_files']}")
        print(f"  Total size: {stats['total_size_mb']} MB")

def cleanup_directory(directory_name: str, config: Dict, mode: str, dry_run: bool = False) -> int:
    """
    Clean up a specific directory based on mode.
    
    Args:
        directory_name: Name of directory being cleaned
        config: Directory configuration
        mode: 'all' or 'prior_only'
        dry_run: If True, show what would be deleted without deleting
    
    Returns:
        int: Number of files deleted (or would be deleted)
    """
    directory = config['path']
    patterns = config['patterns']
    current_date = get_current_date()
    
    logger.info(f"Processing directory: {directory_name} ({directory})")
    
    files = find_files_by_patterns(directory, patterns)
    current_day_files, prior_day_files = categorize_files(files, current_date)
    
    if mode == 'all':
        files_to_delete = files
        logger.info(f"Mode: Remove ALL files ({len(files)} files)")
    elif mode == 'prior_only':
        files_to_delete = prior_day_files
        logger.info(f"Mode: Remove PRIOR DAY only ({len(prior_day_files)} files, keeping {len(current_day_files)} current day files)")
    else:
        logger.error(f"Unknown mode: {mode}")
        return 0
    
    if not files_to_delete:
        logger.info(f"No files to delete in {directory_name}")
        return 0
    
    return delete_files(files_to_delete, dry_run)

def main():
    """Main execution function with interactive menu."""
    try:
        print("System Cleaner for Trading Data Files")
        print("=====================================")
        
        # Display summary
        display_cleanup_summary()
        
        # Get user choice
        print("\nCleanup Options:")
        print("1) Remove ALL files (including current day)")
        print("2) Remove PRIOR DAY files only (keep current day)")
        print("3) Dry run - show what would be deleted")
        print("4) Exit")
        
        while True:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '4':
                print("Exiting without cleaning.")
                return
            
            if choice in ['1', '2', '3']:
                break
            
            print("Invalid choice. Please enter 1, 2, 3, or 4.")
        
        # Map choice to mode
        if choice == '1':
            mode = 'all'
            dry_run = False
        elif choice == '2':
            mode = 'prior_only'
            dry_run = False
        elif choice == '3':
            print("\nChoose dry run mode:")
            print("1) Show ALL files that would be deleted")
            print("2) Show PRIOR DAY files that would be deleted")
            sub_choice = input("Enter choice (1-2): ").strip()
            mode = 'all' if sub_choice == '1' else 'prior_only'
            dry_run = True
        
        # Confirmation for actual deletion
        if not dry_run:
            confirm = input(f"\nConfirm cleanup in {mode} mode? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("Cleanup cancelled.")
                return
        
        # Execute cleanup
        print(f"\n{'='*60}")
        print(f"STARTING CLEANUP - Mode: {mode.upper()}" + (" (DRY RUN)" if dry_run else ""))
        print(f"{'='*60}")
        
        total_deleted = 0
        for dir_name, config in CLEANUP_CONFIG.items():
            deleted = cleanup_directory(dir_name, config, mode, dry_run)
            total_deleted += deleted
        
        print(f"\n{'='*60}")
        action = "Would delete" if dry_run else "Deleted"
        print(f"CLEANUP COMPLETE: {action} {total_deleted} files total")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n\nCleanup interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()