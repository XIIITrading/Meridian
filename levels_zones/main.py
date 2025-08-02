"""
Meridian Pre-Market Trading System
Main application entry point with dark theme
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add src to path for imports
sys.path.append('src')

from config import Config
from ui.main_window import MainWindow
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