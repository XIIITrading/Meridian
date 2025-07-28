#!/usr/bin/env python3
"""
run_polygon_cleaner.py
Polygon Data Cleanup Script for XIIITradingSystems
Run from: C:\XIIITradingSystems\Meridian\execute
Cleans: C:\XIIITradingSystems\Meridian\polygon
"""

import os
import shutil
import glob
from pathlib import Path
import argparse
from datetime import datetime, timedelta
import logging
import sys

def setup_logging():
    """Setup logging for cleanup operations"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    log_file = script_dir / 'polygon_cleanup.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_polygon_directory():
    """Get the polygon directory path relative to this script's location"""
    # This script is in execute/, polygon/ is at ../polygon/
    script_dir = Path(__file__).parent
    polygon_dir = script_dir.parent / 'polygon'
    
    if not polygon_dir.exists():
        # Fallback to absolute path if relative doesn't work
        polygon_dir = Path(r"C:\XIIITradingSystems\Meridian\polygon")
    
    return polygon_dir

def clean_polygon_directory(days_to_keep=7, dry_run=False):
    """
    Clean polygon directory of cache and parquet files
    
    Args:
        days_to_keep: Keep files newer than this many days (0 = delete all)
        dry_run: If True, show what would be deleted without deleting
    """
    
    polygon_path = get_polygon_directory()
    
    if not polygon_path.exists():
        logging.error(f"Polygon directory not found at {polygon_path}")
        return False
    
    logging.info(f"Cleaning polygon directory: {polygon_path}")
    
    # File patterns to clean
    patterns_to_clean = [
        "*.parquet",
        "*.pkl",  # pickle cache files
        "*.cache",
        "*.tmp",
        "*.temp",
        "**/*.parquet",  # recursive parquet files
        "**/*.pkl",
        "**/*.cache",
        "**/*.tmp",
        "**/*.temp",
        "__pycache__/**",
        "*.pyc",
        ".DS_Store",  # macOS files
        "Thumbs.db",  # Windows files
        "*.log",  # old log files (but not our current log)
        "*.bak",  # backup files
        "*.swp",  # vim swap files
        ".ipynb_checkpoints/**",  # Jupyter checkpoints
    ]
    
    # Directories to clean entirely
    dirs_to_clean = [
        "__pycache__",
        ".pytest_cache", 
        "temp",
        "tmp", 
        "cache",
        ".ipynb_checkpoints",
        ".mypy_cache",
        "node_modules",  # in case any JS tools were used
    ]
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    total_size_freed = 0
    files_deleted = 0
    
    logging.info(f"Starting cleanup - keeping files newer than {cutoff_date}")
    logging.info(f"Dry run mode: {dry_run}")
    
    # Clean files by pattern
    for pattern in patterns_to_clean:
        try:
            for file_path in polygon_path.glob(pattern):
                if file_path.is_file():
                    # Skip our own log file
                    if file_path.name == 'polygon_cleanup.log':
                        continue
                        
                    file_age = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if days_to_keep == 0 or file_age < cutoff_date:
                        file_size = file_path.stat().st_size
                        
                        if dry_run:
                            logging.info(f"Would delete: {file_path.relative_to(polygon_path)} ({file_size:,} bytes)")
                        else:
                            try:
                                file_path.unlink()
                                logging.info(f"Deleted: {file_path.relative_to(polygon_path)} ({file_size:,} bytes)")
                                total_size_freed += file_size
                                files_deleted += 1
                            except PermissionError:
                                logging.warning(f"Permission denied: {file_path}")
                            except Exception as e:
                                logging.error(f"Error deleting {file_path}: {e}")
        except Exception as e:
            logging.error(f"Error processing pattern {pattern}: {e}")
    
    # Clean directories
    for dir_name in dirs_to_clean:
        try:
            for dir_path in polygon_path.glob(f"**/{dir_name}"):
                if dir_path.is_dir():
                    try:
                        dir_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                        
                        if dry_run:
                            logging.info(f"Would delete directory: {dir_path.relative_to(polygon_path)} ({dir_size:,} bytes)")
                        else:
                            shutil.rmtree(dir_path)
                            logging.info(f"Deleted directory: {dir_path.relative_to(polygon_path)} ({dir_size:,} bytes)")
                            total_size_freed += dir_size
                            files_deleted += 1
                    except PermissionError:
                        logging.warning(f"Permission denied for directory: {dir_path}")
                    except Exception as e:
                        logging.error(f"Error deleting directory {dir_path}: {e}")
        except Exception as e:
            logging.error(f"Error processing directory pattern {dir_name}: {e}")
    
    # Summary
    if not dry_run and files_deleted > 0:
        logging.info(f"✅ Cleanup complete: {files_deleted} items deleted, {total_size_freed / (1024*1024):.2f} MB freed")
    elif not dry_run:
        logging.info("✅ Cleanup complete: No files needed deletion")
    else:
        logging.info("🔍 Dry run complete - no files were actually deleted")
    
    return True

def clean_by_date_folders(days_to_keep=30, dry_run=False):
    """
    Clean date-based folders (common in trading data)
    Assumes folders named like YYYY-MM-DD or YYYYMMDD
    """
    polygon_path = get_polygon_directory()
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    logging.info(f"Cleaning date folders older than {cutoff_date.strftime('%Y-%m-%d')}")
    
    # Common date folder patterns
    date_patterns = ['????-??-??', '????????', '????_??_??']
    folders_cleaned = 0
    
    for pattern in date_patterns:
        try:
            for folder in polygon_path.glob(pattern):
                if folder.is_dir():
                    try:
                        # Try to parse folder name as date
                        folder_name = folder.name
                        folder_date = None
                        
                        if '-' in folder_name:
                            folder_date = datetime.strptime(folder_name, '%Y-%m-%d')
                        elif '_' in folder_name:
                            folder_date = datetime.strptime(folder_name, '%Y_%m_%d')
                        elif len(folder_name) == 8 and folder_name.isdigit():
                            folder_date = datetime.strptime(folder_name, '%Y%m%d')
                        
                        if folder_date and folder_date < cutoff_date:
                            folder_size = sum(f.stat().st_size for f in folder.rglob('*') if f.is_file())
                            
                            if dry_run:
                                logging.info(f"Would delete old date folder: {folder.name} ({folder_size / (1024*1024):.2f} MB)")
                            else:
                                shutil.rmtree(folder)
                                logging.info(f"Deleted old date folder: {folder.name} ({folder_size / (1024*1024):.2f} MB)")
                                folders_cleaned += 1
                            
                    except ValueError:
                        # Skip folders that don't match date format
                        continue
                    except Exception as e:
                        logging.error(f"Error processing date folder {folder}: {e}")
        except Exception as e:
            logging.error(f"Error processing date pattern {pattern}: {e}")
    
    if folders_cleaned > 0:
        logging.info(f"Cleaned {folders_cleaned} old date folders")

def show_directory_size():
    """Show current size of polygon directory"""
    polygon_path = get_polygon_directory()
    
    if not polygon_path.exists():
        logging.error("Polygon directory not found")
        return
    
    total_size = 0
    file_count = 0
    
    for file_path in polygon_path.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
            file_count += 1
    
    logging.info(f"📊 Current polygon directory stats:")
    logging.info(f"   Total files: {file_count:,}")
    logging.info(f"   Total size: {total_size / (1024*1024):.2f} MB")
    logging.info(f"   Directory: {polygon_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Clean Polygon data directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_polygon_cleaner.py --dry-run              # See what would be deleted
  python run_polygon_cleaner.py --days 3               # Delete files older than 3 days
  python run_polygon_cleaner.py --days 0               # Delete all cache files
  python run_polygon_cleaner.py --clean-date-folders   # Also clean old date folders
  python run_polygon_cleaner.py --size                 # Show directory size
        """
    )
    
    parser.add_argument('--days', type=int, default=7, 
                       help='Keep files newer than this many days (default: 7, use 0 for all)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without deleting')
    parser.add_argument('--clean-date-folders', action='store_true',
                       help='Also clean old date-based folders (30 days retention)')
    parser.add_argument('--size', action='store_true',
                       help='Show current directory size and exit')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce logging output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    logging.info("🧹 Starting Polygon Data Cleaner")
    logging.info(f"   Script location: {Path(__file__).parent}")
    logging.info(f"   Target directory: {get_polygon_directory()}")
    
    # Show size if requested
    if args.size:
        show_directory_size()
        return
    
    # Main cleanup
    success = clean_polygon_directory(args.days, args.dry_run)
    
    if not success:
        sys.exit(1)
    
    # Optional date folder cleanup
    if args.clean_date_folders:
        logging.info("🗓️  Cleaning old date folders...")
        clean_by_date_folders(30, args.dry_run)
    
    # Show final size
    if not args.dry_run:
        show_directory_size()
    
    logging.info("✨ Polygon cleaner finished")

if __name__ == "__main__":
    main()