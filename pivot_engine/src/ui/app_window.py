"""
Main application window for Meridian Pre-Market Trading System
Provides the primary UI container with dark theme and database integration
"""

import sys
from typing import Optional, Dict, Any
import logging
import os
import traceback
from datetime import datetime

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
        
        logger.info("="*60)
        logger.info("INITIALIZING MAIN WINDOW")
        logger.info("="*60)
        
        # Instance variables
        self.current_session_id: Optional[str] = None
        self.is_modified: bool = False
        self.analysis_thread: Optional[AnalysisThread] = None
        
        # Initialize services
        logger.info("Initializing services...")
        self.db_service = DatabaseService()
        self.polygon_service = PolygonService()
        logger.info("Services initialized")
        
        # Initialize UI
        self._init_ui()
        self._setup_menu_bar()
        self._connect_signals()
        self._connect_database_signals()
        self._connect_polygon_signals()
        
        logger.info("Main window initialized with dark theme and all services")
        logger.info("="*60)
    
    def _init_ui(self):
        """Initialize the main UI with dark theme"""
        logger.debug("Initializing UI...")
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme styles
        self.setStyleSheet(get_combined_stylesheet())
        
        # Create central widget - now just the overview widget
        self.overview_widget = OverviewWidget()
        self.setCentralWidget(self.overview_widget)
        
        # Connect overview widget signals
        logger.debug("Connecting overview widget signals...")
        self.overview_widget.analysis_requested.connect(self._on_run_analysis)
        self.overview_widget.save_to_database.connect(self._on_save_to_database)
        self.overview_widget.data_changed.connect(self._on_data_changed)
        self.overview_widget.fetch_market_data.connect(self._on_fetch_market_data)
        logger.debug("Overview widget signals connected")
    
    def _connect_signals(self):
        """Connect internal signals"""
        # Signals are connected in _init_ui and _setup_menu_bar
        logger.debug("Internal signals connected")
    
    def _connect_database_signals(self):
        """Connect database service signals"""
        logger.debug("Connecting database service signals...")
        
        # Save signals
        self.db_service.save_started.connect(self._on_save_started)
        self.db_service.save_completed.connect(self._on_save_completed)
        self.db_service.save_failed.connect(self._on_save_failed)
        
        # Load signals
        self.db_service.load_started.connect(self._on_load_started)
        self.db_service.load_completed.connect(self._on_load_completed)
        self.db_service.load_failed.connect(self._on_load_failed)
        
        logger.debug("Database signals connected")
    
    def _connect_polygon_signals(self):
        """Connect Polygon service signals"""
        logger.debug("Connecting Polygon service signals...")
        
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
        
        logger.debug("Polygon signals connected")
    
    def _on_save_to_database(self, session_data: Dict[str, Any]):
        """
        Handle save to database signal from overview widget
        
        Args:
            session_data: Dictionary containing all session data from UI
        """
        logger.info("="*60)
        logger.info("MAIN WINDOW: SAVE TO DATABASE HANDLER")
        logger.info("="*60)
        
        try:
            # Log incoming data structure
            logger.debug("Received session data from overview widget:")
            self._log_data_structure(session_data)
            
            # Check if database service is available
            if not hasattr(self, 'db_service') or not self.db_service:
                logger.error("Database service not initialized!")
                QMessageBox.critical(
                    self,
                    "Configuration Error",
                    "Database service not initialized.\nPlease check your configuration."
                )
                return
            
            # Call database service to save
            logger.info("Calling database service save_session...")
            success, result = self.db_service.save_session(session_data)
            
            if success:
                logger.info(f"Save successful! Session ID: {result}")
                self.current_session_id = result
                self.is_modified = False
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Success",
                    f"Session saved successfully!\nSession ID: {result}"
                )
                
                # Update status bar
                self.statusBar().showMessage(f"Session saved: {result}", 5000)
            else:
                logger.error(f"Save failed: {result}")
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    f"Failed to save session:\n{result}\n\nCheck console for details."
                )
                
        except Exception as e:
            logger.error(f"Exception in save handler: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while saving:\n{str(e)}\n\nCheck console for details."
            )
        finally:
            logger.info("="*60)
            logger.info("SAVE HANDLER COMPLETE")
            logger.info("="*60)
    
    def _log_data_structure(self, data: Dict[str, Any], indent: int = 0):
        """Log the structure of data for debugging"""
        prefix = "  " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                logger.debug(f"{prefix}{key}: <dict> with {len(value)} keys")
                if indent < 2:  # Limit recursion depth
                    self._log_data_structure(value, indent + 1)
            elif isinstance(value, list):
                logger.debug(f"{prefix}{key}: <list> with {len(value)} items")
                if value and isinstance(value[0], dict) and indent < 2:
                    logger.debug(f"{prefix}  [0]:")
                    self._log_data_structure(value[0], indent + 2)
            elif isinstance(value, datetime):
                logger.debug(f"{prefix}{key}: {value.isoformat()} (datetime)")
            else:
                if isinstance(value, str) and len(value) > 50:
                    logger.debug(f"{prefix}{key}: '{value[:50]}...' (str, {len(value)} chars)")
                else:
                    logger.debug(f"{prefix}{key}: {value} ({type(value).__name__})")
    
    def _on_fetch_market_data(self, params: Dict[str, Any]):
        """Handle fetch market data request"""
        logger.info(f"Fetching market data for {params.get('ticker')}")
        
        # Check if polygon service exists
        if not hasattr(self, 'polygon_service') or not self.polygon_service:
            logger.error("Polygon service not initialized")
            QMessageBox.warning(
                self,
                "Service Not Available",
                "Market data service is not initialized."
            )
            return
        
        # Extract parameters and call the service
        try:
            ticker = params.get('ticker')
            datetime_val = params.get('datetime')
            
            if not ticker or not datetime_val:
                logger.error("Missing ticker or datetime in params")
                return
            
            # Call with the correct signature (the service expects separate parameters)
            self.polygon_service.fetch_market_data(ticker, datetime_val)
            
        except Exception as e:
            logger.error(f"Error calling polygon service: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Fetch Error",
                f"Error fetching market data: {str(e)}"
            )
    
    def _on_market_data_ready(self, data: Dict[str, Any]):
        """Handle market data ready signal"""
        logger.info("Market data received")
        # Update UI with market data
        if 'metrics' in data:
            self.overview_widget.metrics_frame.update_metrics(data['metrics'])
    
    # Database signal handlers
    def _on_save_started(self):
        """Handle save started signal"""
        logger.info("Save operation started...")
        self.statusBar().showMessage("Saving session to database...")
        # Disable save button temporarily
        if hasattr(self.overview_widget, 'save_to_db_btn'):
            self.overview_widget.save_to_db_btn.setEnabled(False)
    
    def _on_save_completed(self, session_id: str):
        """Handle save completed signal"""
        logger.info(f"Save completed: {session_id}")
        self.statusBar().showMessage(f"Session saved successfully: {session_id}", 5000)
        # Re-enable save button
        if hasattr(self.overview_widget, 'save_to_db_btn'):
            self.overview_widget.save_to_db_btn.setEnabled(True)
    
    def _on_save_failed(self, error_msg: str):
        """Handle save failed signal"""
        logger.error(f"Save failed: {error_msg}")
        self.statusBar().showMessage("Save failed", 3000)
        # Re-enable save button
        if hasattr(self.overview_widget, 'save_to_db_btn'):
            self.overview_widget.save_to_db_btn.setEnabled(True)
    
    def _on_load_started(self):
        """Handle load started signal"""
        logger.info("Load operation started...")
        self.statusBar().showMessage("Loading session from database...")
    
    def _on_load_completed(self, session_data: dict):
        """Handle load completed signal"""
        logger.info("Load completed")
        self.statusBar().showMessage("Session loaded successfully", 3000)
        # Load data into UI
        self.overview_widget.load_session_data(session_data)
        self.is_modified = False
    
    def _on_load_failed(self, error_msg: str):
        """Handle load failed signal"""
        logger.error(f"Load failed: {error_msg}")
        self.statusBar().showMessage("Load failed", 3000)
    
    def _on_data_changed(self):
        """Handle data changed signal from overview widget"""
        logger.debug("Data changed in UI")
        self.is_modified = True
        # Update window title to show unsaved changes
        title = self.windowTitle()
        if not title.endswith(" *"):
            self.setWindowTitle(title + " *")
    
    def _on_run_analysis(self, session_data: Dict[str, Any]):
        """Handle run analysis request"""
        logger.info("="*60)
        logger.info("ANALYSIS REQUESTED")
        logger.info("="*60)
        
        try:
            ticker = session_data.get('ticker')
            if not ticker:
                logger.error("No ticker in session data")
                QMessageBox.warning(self, "Missing Data", "Please enter a ticker symbol.")
                return
            
            logger.info(f"Starting analysis for {ticker}")
            
            # Stop any existing analysis thread
            if self.analysis_thread and self.analysis_thread.isRunning():
                logger.info("Stopping existing analysis thread...")
                self.analysis_thread.terminate()
                self.analysis_thread.wait()
            
            # Create and start new analysis thread
            logger.info("Creating new analysis thread...")
            self.analysis_thread = AnalysisThread(session_data)
            
            # Connect signals - NOTE: Your AnalysisThread uses different signal names
            self.analysis_thread.progress.connect(
                lambda pct, msg: self.statusBar().showMessage(f"Analysis: {msg} ({pct}%)")
            )
            self.analysis_thread.finished.connect(self._on_analysis_complete)
            self.analysis_thread.error.connect(self._on_analysis_error)
            
            # Start the analysis
            self.analysis_thread.start()
            self.statusBar().showMessage(f"Running analysis for {ticker}...")
            
            # Disable the run button while analyzing
            if hasattr(self.overview_widget, 'run_analysis_btn'):
                self.overview_widget.run_analysis_btn.setEnabled(False)
                
        except Exception as e:
            logger.error(f"Error starting analysis: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Failed to start analysis:\n{str(e)}"
            )

    def _on_analysis_complete(self, results: Dict[str, Any]):
        """Handle analysis completion"""
        logger.info("Analysis complete")
        
        # Re-enable run button
        if hasattr(self.overview_widget, 'run_analysis_btn'):
            self.overview_widget.run_analysis_btn.setEnabled(True)
        
        # Update the UI with results
        if results and results.get('status') == 'completed':
            self.overview_widget.update_calculations(results)
            self.statusBar().showMessage("Analysis complete", 5000)
            
            # Log summary
            logger.info(f"Analysis results: HVN 7-day: {results.get('metrics', {}).get('hvn_7day_count', 0)} peaks")
            logger.info(f"Analysis results: HVN 14-day: {results.get('metrics', {}).get('hvn_14day_count', 0)} peaks")
            logger.info(f"Analysis results: HVN 30-day: {results.get('metrics', {}).get('hvn_30day_count', 0)} peaks")
        else:
            logger.warning("Analysis completed but results were incomplete")
            QMessageBox.warning(
                self,
                "Analysis Incomplete",
                "Analysis completed but some results may be missing.\nCheck the console for details."
            )

    def _on_analysis_error(self, error_msg: str):
        """Handle analysis error"""
        logger.error(f"Analysis error: {error_msg}")
        
        # Re-enable run button
        if hasattr(self.overview_widget, 'run_analysis_btn'):
            self.overview_widget.run_analysis_btn.setEnabled(True)
        
        self.statusBar().showMessage("Analysis failed", 3000)
        QMessageBox.critical(
            self,
            "Analysis Failed",
            f"Analysis failed:\n{error_msg}\n\nCheck the console for details."
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