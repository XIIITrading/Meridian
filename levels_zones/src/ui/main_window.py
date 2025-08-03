"""
Simplified main window that coordinates components
"""

import sys
import logging
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QCloseEvent

from config import Config
from ui.dark_theme import get_combined_stylesheet
from ui.widgets.overview_widget import OverviewWidget
from ui.components.menu_manager import MenuManager
from ui.components.status_manager import StatusManager
from services.session_manager import SessionManager
from services.analysis_service import AnalysisService
from services.polygon_service import PolygonService

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Simplified main window that coordinates services and UI components
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize services
        self.session_manager = SessionManager()
        self.analysis_service = AnalysisService()
        self.polygon_service = PolygonService()
        
        # Initialize UI components
        self.menu_manager = MenuManager(self)
        self.status_manager = StatusManager(self)
        
        # Initialize UI
        self._init_ui()
        self._connect_signals()
        
        logger.info("Main window initialized")
    
    def _init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(get_combined_stylesheet())
        
        # Create central widget
        self.overview_widget = OverviewWidget()
        self.setCentralWidget(self.overview_widget)
        
        # Setup components
        self.menu_manager.setup_menus()
        self.status_manager.setup_status_bar()
    
    def _connect_signals(self):
        """Connect all signals between components"""
        # Overview widget signals
        self.overview_widget.analysis_requested.connect(
            self.analysis_service.run_analysis
        )
        self.overview_widget.save_data.connect(
            self.session_manager.save_session
        )
        self.overview_widget.data_changed.connect(
            self.session_manager.mark_modified
        )
        self.overview_widget.fetch_market_data.connect(
            self._on_fetch_market_data
        )
        
        # Session manager signals
        self.session_manager.session_created.connect(self._on_session_created)
        self.session_manager.session_loaded.connect(self._on_session_loaded)
        self.session_manager.session_saved.connect(self._on_session_saved)
        self.session_manager.session_modified.connect(self._update_title)
        self.session_manager.error_occurred.connect(self._on_error)
        
        # Analysis service signals
        self.analysis_service.analysis_started.connect(
            lambda ticker: self.status_manager.show_message(f"Starting analysis for {ticker}...")
        )
        self.analysis_service.analysis_progress.connect(
            self.status_manager.show_progress
        )
        self.analysis_service.analysis_completed.connect(self._on_analysis_completed)
        self.analysis_service.analysis_failed.connect(self._on_analysis_failed)
        
        # Polygon service signals
        self.polygon_service.data_fetch_started.connect(
            lambda ticker: self.status_manager.show_message(f"Fetching data for {ticker}...")
        )
        self.polygon_service.data_fetch_completed.connect(self._on_market_data_ready)
        self.polygon_service.data_fetch_failed.connect(self._on_error)
        self.polygon_service.progress_update.connect(
            self.status_manager.show_progress
        )
    
    @pyqtSlot(dict)
    def _on_fetch_market_data(self, params: dict):
        """Handle market data fetch request"""
        ticker = params.get('ticker')
        datetime_val = params.get('datetime')
        
        if ticker and datetime_val:
            self.polygon_service.fetch_market_data(ticker, datetime_val)
    
    @pyqtSlot(dict)
    def _on_market_data_ready(self, data: dict):
        """Handle market data ready"""
        if 'metrics' in data:
            self.overview_widget.metrics_frame.update_metrics(data['metrics'])
        self.status_manager.show_message("Market data updated", 3000)
    
    @pyqtSlot(str)
    def _on_session_created(self, session_id: str):
        """Handle new session creation"""
        self.overview_widget.clear_all()
        self._update_title()
    
    @pyqtSlot(dict)
    def _on_session_loaded(self, session_data: dict):
        """Handle session loaded"""
        self.overview_widget.load_session_data(session_data)
        self._update_title()
        self.status_manager.show_message("Session loaded successfully", 3000)
    
    @pyqtSlot(str)
    def _on_session_saved(self, session_id: str):
        """Handle session saved"""
        self._update_title()
        self.menu_manager.update_recent_sessions()
        self.status_manager.show_message(f"Session saved: {session_id}", 5000)
        QMessageBox.information(
            self,
            "Save Successful",
            f"Session saved successfully!\nID: {session_id}"
        )
    
    @pyqtSlot(dict)
    def _on_analysis_completed(self, results: dict):
        """Handle analysis completion"""
        self.overview_widget.run_analysis_btn.setEnabled(True)
        self.overview_widget.update_calculations(results)
        self.status_manager.show_message("Analysis completed", 5000)
    
    @pyqtSlot(str)
    def _on_analysis_failed(self, error: str):
        """Handle analysis failure"""
        self.overview_widget.run_analysis_btn.setEnabled(True)
        self.status_manager.show_message("Analysis failed", 5000)
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"Analysis failed:\n\n{error}"
        )
    
    @pyqtSlot(str)
    def _on_error(self, error: str):
        """Handle general errors"""
        QMessageBox.critical(self, "Error", error)
    
    def _update_title(self):
        """Update window title"""
        title = f"{Config.APP_NAME} v{Config.APP_VERSION}"
        
        session_info = self.session_manager.current_session_info
        if session_info:
            title += f" - {session_info}"
        
        if self.session_manager.has_unsaved_changes:
            title += " *"
        
        self.setWindowTitle(title)
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close"""
        if self.session_manager.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Stop any running analysis
        if self.analysis_service.is_running():
            self.analysis_service.stop()
        
        event.accept()
        logger.info("Application closed")