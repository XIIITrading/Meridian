"""
Meridian Pre-Market Trading System
Main application entry point with dark theme
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add project directories to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))  # Add project root for calculations
sys.path.insert(0, str(project_root / 'src'))  # Add src for modules

# Now we can import from our modules
from config import Config
from ui import MainWindow
from ui.dark_theme import apply_dark_theme

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    # Validate configuration
    if not Config.validate():
        print("Configuration validation failed. Exiting.")
        sys.exit(1)
    
    logger.info(f"Starting {Config.APP_NAME} v{Config.APP_VERSION}")
    
    # Log the Python path for debugging
    logger.debug(f"Python path: {sys.path}")
    logger.debug(f"Project root: {project_root}")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName(Config.APP_NAME)
    app.setOrganizationName("Meridian Trading Systems")
    
    # Note: PyQt6 handles high DPI automatically, no need to set attributes
    
    # Apply dark theme
    apply_dark_theme(app)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()