"""
Main application window for Meridian Pre-Market Trading System
Provides the primary UI container with dark theme
"""

import sys
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMessageBox, QApplication,
    QTabWidget, QLabel
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QAction, QCloseEvent

# Import configuration and theme
sys.path.append('../..')
from config import Config
from ui.dark_theme import DarkTheme, DarkStyleSheets, get_combined_stylesheet
from ui.widgets.overview_widget import OverviewWidget

# Set up logging
logger = logging.getLogger(__name__)


class AnalysisThread(QThread):
    """Worker thread for running analysis calculations"""
    
    # Signals
    progress = pyqtSignal(int, str)  # Progress percentage and message
    finished = pyqtSignal(dict)      # Analysis results
    error = pyqtSignal(str)          # Error message
    
    def __init__(self, session_data: Dict[str, Any]):
        super().__init__()
        self.session_data = session_data
        
    def run(self):
        """Run the analysis in background thread"""
        try:
            # TODO: Implement actual analysis calculations
            self.progress.emit(10, "Starting analysis...")
            
            # Placeholder for actual implementation
            results = {
                'status': 'completed',
                'timestamp': datetime.now(),
                # Results will be populated by actual calculations
            }
            
            self.progress.emit(100, "Analysis complete!")
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """
    Main application window for Meridian Trading System with dark theme
    """
    
    def __init__(self):
        super().__init__()
        
        # Instance variables
        self.current_session_id: Optional[str] = None
        self.is_modified: bool = False
        self.analysis_thread: Optional[AnalysisThread] = None
        
        # Initialize UI
        self._init_ui()
        self._setup_menu_bar()
        self._connect_signals()
        
        logger.info("Main window initialized with dark theme")
    
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
    
    def _setup_menu_bar(self):
        """Create minimal menu bar for dark theme"""
        menubar = self.menuBar()
        menubar.setStyleSheet(DarkStyleSheets.MENU_BAR)
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        file_menu.setStyleSheet(DarkStyleSheets.MENU)
        
        # New Session
        new_action = QAction("&New Session", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new_session)
        file_menu.addAction(new_action)
        
        # Load Session
        load_action = QAction("&Load Session", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._on_load_session)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        view_menu.setStyleSheet(DarkStyleSheets.MENU)
        
        # Results Window
        results_action = QAction("&Analysis Results", self)
        results_action.setShortcut("Ctrl+R")
        results_action.triggered.connect(self._on_show_results)
        view_menu.addAction(results_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        help_menu.setStyleSheet(DarkStyleSheets.MENU)
        
        # About
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        """Connect internal signals"""
        pass  # Signals connected in _init_ui
    
    @pyqtSlot()
    def _on_data_changed(self):
        """Handle data change in any widget"""
        self.is_modified = True
    
    @pyqtSlot(dict)
    def _on_save_to_database(self, data: Dict[str, Any]):
        """Handle saving to database"""
        logger.info(f"Saving session data for {data['ticker']}")
        # TODO: Implement actual database save using supabase_client
        self.is_modified = False
    
    @pyqtSlot()
    def _on_new_session(self):
        """Handle new session creation"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, 
                "Save Session",
                "Current session has unsaved changes. Save before creating new session?",
                QMessageBox.StandardButton.Yes | 
                QMessageBox.StandardButton.No | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Trigger save
                self.overview_widget._on_save()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        # Clear all fields
        self.overview_widget.clear_all()
        self.current_session_id = None
        self.is_modified = False
        
        logger.info("New session created")
    
    @pyqtSlot()
    def _on_load_session(self):
        """Handle loading a session from database"""
        # TODO: Implement session loading dialog
        QMessageBox.information(self, "Load Session", "Session loading will be implemented with database integration.")
    
    @pyqtSlot()
    def _on_show_results(self):
        """Show analysis results window"""
        # TODO: Create results display window
        QMessageBox.information(self, "Analysis Results", "Results window will be implemented to show HVN and Camarilla calculations.")
    
    @pyqtSlot(dict)
    def _on_run_analysis(self, session_data: Dict[str, Any]):
        """Handle running the analysis"""
        # Create and start analysis thread
        self.analysis_thread = AnalysisThread(session_data)
        self.analysis_thread.progress.connect(self._on_analysis_progress)
        self.analysis_thread.finished.connect(self._on_analysis_finished)
        self.analysis_thread.error.connect(self._on_analysis_error)
        self.analysis_thread.start()
        
        # Disable run button
        self.overview_widget.run_analysis_btn.setEnabled(False)
        
        logger.info(f"Starting analysis for {session_data['ticker']}")
    
    @pyqtSlot(int, str)
    def _on_analysis_progress(self, progress: int, message: str):
        """Handle analysis progress updates"""
        logger.debug(f"Analysis progress: {progress}% - {message}")
    
    @pyqtSlot(dict)
    def _on_analysis_finished(self, results: dict):
        """Handle analysis completion"""
        # Re-enable run button
        self.overview_widget.run_analysis_btn.setEnabled(True)
        
        # Update displays with results
        self.overview_widget.update_calculations(results)
        
        # TODO: Show results in separate window
        logger.info("Analysis completed")
    
    @pyqtSlot(str)
    def _on_analysis_error(self, error_msg: str):
        """Handle analysis errors"""
        # Re-enable run button
        self.overview_widget.run_analysis_btn.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"Analysis failed with error:\n\n{error_msg}"
        )
        
        logger.error(f"Analysis failed: {error_msg}")
    
    @pyqtSlot()
    def _on_about(self):
        """Handle showing about dialog"""
        about_text = f"""
        <h3 style="color: {DarkTheme.TEXT_PRIMARY};">{Config.APP_NAME}</h3>
        <p style="color: {DarkTheme.TEXT_SECONDARY};">Version {Config.APP_VERSION}</p>
        <p style="color: {DarkTheme.TEXT_SECONDARY};">A pre-market trading analysis system.</p>
        <p style="color: {DarkTheme.TEXT_SECONDARY};">© 2024 Meridian Trading Systems</p>
        """
        
        msg_box = QMessageBox()
        msg_box.setWindowTitle("About Meridian")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(about_text)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {DarkTheme.BG_DARK};
            }}
            QMessageBox QLabel {{
                color: {DarkTheme.TEXT_PRIMARY};
            }}
        """)
        msg_box.exec()
    
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