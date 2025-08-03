"""
Main application window for Meridian Pre-Market Trading System
Provides the primary UI container with dark theme and database integration
"""

import sys
from typing import Optional
import logging
import os

# Add parent directory to path for calculations imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtGui import QCloseEvent

# Import configuration and theme
sys.path.append('../..')
from config import Config
from ui.dark_theme import get_combined_stylesheet
from ui.widgets.overview_widget import OverviewWidget
from services.database_service import DatabaseService
from services.polygon_service import PolygonService

# Import the extracted components
from ui.dialogs.session_picker_dialog import SessionPickerDialog
from ui.threads.analysis_thread import AnalysisThread

# Import the mixin classes
from .main_window.menu_manager import MenuManagerMixin
from .main_window.signal_handlers import SignalHandlersMixin
from .main_window.database_handlers import DatabaseHandlersMixin
from .main_window.window_helpers import WindowHelpersMixin

# Set up logging
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow, MenuManagerMixin, SignalHandlersMixin, 
                 DatabaseHandlersMixin, WindowHelpersMixin):
    """
    Main application window for Meridian Trading System with dark theme and database integration
    """
    
    def __init__(self):
        super().__init__()
        
        # Instance variables
        self.current_session_id: Optional[str] = None
        self.is_modified: bool = False
        self.analysis_thread: Optional[AnalysisThread] = None
        
        # Initialize services
        self.db_service = DatabaseService()
        self.polygon_service = PolygonService()
        
        # Initialize UI
        self._init_ui()
        self._setup_menu_bar()
        self._connect_signals()
        self._connect_database_signals()
        self._connect_polygon_signals()
        
        logger.info("Main window initialized with dark theme and all services")
    
    def _init_ui(self):
        """Initialize the main UI with dark theme"""
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme styles
        self.setStyleSheet(get_combined_stylesheet())
        
        # Create central widget - now just the overview widget
        self.overview_widget = OverviewWidget()
        self.setCentralWidget(self.overview_widget)
        
        # Connect overview widget signals
        self.overview_widget.analysis_requested.connect(self._on_run_analysis)
        self.overview_widget.save_to_database.connect(self._on_save_to_database)
        self.overview_widget.data_changed.connect(self._on_data_changed)
        self.overview_widget.fetch_market_data.connect(self._on_fetch_market_data)
    
    def _connect_signals(self):
        """Connect internal signals"""
        # Signals are connected in _init_ui and _setup_menu_bar
        pass
    
    def _connect_database_signals(self):
        """Connect database service signals"""
        # Save signals
        self.db_service.save_started.connect(self._on_save_started)
        self.db_service.save_completed.connect(self._on_save_completed)
        self.db_service.save_failed.connect(self._on_save_failed)
        
        # Load signals
        self.db_service.load_started.connect(self._on_load_started)
        self.db_service.load_completed.connect(self._on_load_completed)
        self.db_service.load_failed.connect(self._on_load_failed)
    
    def _connect_polygon_signals(self):
        """Connect Polygon service signals"""
        # Data fetch signals
        self.polygon_service.data_fetch_started.connect(
            lambda ticker: self.statusBar().showMessage(f"Fetching market data for {ticker}...")
        )
        self.polygon_service.data_fetch_completed.connect(self._on_market_data_ready)
        self.polygon_service.data_fetch_failed.connect(
            lambda err: QMessageBox.critical(self, "Data Fetch Failed", err)
        )
        
        # Progress updates
        self.polygon_service.progress_update.connect(
            lambda pct, msg: self.statusBar().showMessage(f"{msg} ({pct}%)")
        )
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Stop any running threads
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.terminate()
            self.analysis_thread.wait()
        
        event.accept()
        logger.info("Application closed")