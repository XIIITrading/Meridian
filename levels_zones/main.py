"""
Meridian Pre-Market Trading System
Main application entry point
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from config import Config

def main():
    """Main application entry point"""
    # Validate configuration
    if not Config.validate():
        print("Configuration validation failed. Exiting.")
        sys.exit(1)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle(Config.THEME)
    
    # High DPI settings
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # TODO: Create and show main window (Phase 3)
    print(f"Starting {Config.APP_NAME} v{Config.APP_VERSION}")
    print("UI components will be added in Phase 3")
    
    # For now, just exit
    sys.exit(0)

if __name__ == "__main__":
    main()