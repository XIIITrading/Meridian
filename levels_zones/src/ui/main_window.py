"""
Main application window for Meridian Pre-Market Trading System
Provides the primary UI container with dark theme and database integration
"""

import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMessageBox, QApplication,
    QTabWidget, QLabel, QDialog, QDialogButtonBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout,
    QInputDialog, QDateEdit, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot, QDate
from PyQt6.QtGui import QAction, QCloseEvent

# Import configuration and theme
sys.path.append('../..')
from config import Config
from ui.dark_theme import DarkTheme, DarkStyleSheets, get_combined_stylesheet
from ui.widgets.overview_widget import OverviewWidget
from services.database_service import DatabaseService

# Set up logging
logger = logging.getLogger(__name__)


class SessionPickerDialog(QDialog):
    """Dialog for selecting a session to load"""
    
    def __init__(self, sessions: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.selected_session_id = None
        self.sessions = sessions
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the session picker UI"""
        self.setWindowTitle("Select Session to Load")
        self.setMinimumSize(800, 400)
        
        # Apply dark theme
        self.setStyleSheet(get_combined_stylesheet())
        
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Ticker filter
        filter_layout.addWidget(QLabel("Ticker:"))
        self.ticker_filter = QLineEdit()
        self.ticker_filter.setPlaceholderText("Filter by ticker...")
        self.ticker_filter.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.ticker_filter)
        
        # Date filter
        filter_layout.addWidget(QLabel("Date:"))
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setSpecialValueText("All dates")
        self.date_filter.dateChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.date_filter)
        
        # Clear filters button
        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(clear_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Sessions table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Ticker", "Session ID", "Date", "Live", "Weekly", "Daily", "Levels"
        ])
        
        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        
        # Populate table
        self._populate_table(self.sessions)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _populate_table(self, sessions: List[Dict[str, Any]]):
        """Populate the table with session data"""
        self.table.setRowCount(len(sessions))
        
        for row, session in enumerate(sessions):
            # Ticker
            self.table.setItem(row, 0, QTableWidgetItem(session['ticker']))
            
            # Session ID
            self.table.setItem(row, 1, QTableWidgetItem(session['ticker_id']))
            
            # Date
            date_str = session['date'].strftime('%Y-%m-%d')
            self.table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Live status
            live_status = "✓" if session['is_live'] else ""
            self.table.setItem(row, 3, QTableWidgetItem(live_status))
            
            # Weekly data
            weekly_status = "✓" if session['has_weekly'] else ""
            self.table.setItem(row, 4, QTableWidgetItem(weekly_status))
            
            # Daily data
            daily_status = "✓" if session['has_daily'] else ""
            self.table.setItem(row, 5, QTableWidgetItem(daily_status))
            
            # Level count
            self.table.setItem(row, 6, QTableWidgetItem(str(session['level_count'])))
            
        # Resize columns to content
        self.table.resizeColumnsToContents()
        
    def _apply_filters(self):
        """Apply filters to the table"""
        ticker_filter = self.ticker_filter.text().upper()
        
        # Check if date filter has a real date or is showing special text
        has_date_filter = self.date_filter.date() != self.date_filter.minimumDate()
        date_filter = self.date_filter.date().toPyDate() if has_date_filter else None
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            # Check ticker filter
            if ticker_filter:
                ticker_item = self.table.item(row, 0)
                if ticker_item and ticker_filter not in ticker_item.text():
                    show_row = False
            
            # Check date filter
            if date_filter:
                date_item = self.table.item(row, 2)
                if date_item:
                    row_date = datetime.strptime(date_item.text(), '%Y-%m-%d').date()
                    if row_date != date_filter:
                        show_row = False
            
            self.table.setRowHidden(row, not show_row)
            
    def _clear_filters(self):
        """Clear all filters"""
        self.ticker_filter.clear()
        self.date_filter.setDate(self.date_filter.minimumDate())
        self._apply_filters()
        
    def _on_double_click(self):
        """Handle double-click on a row"""
        self._on_accept()
        
    def _on_accept(self):
        """Handle accept button"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            session_id_item = self.table.item(current_row, 1)
            if session_id_item:
                self.selected_session_id = session_id_item.text()
                self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a session to load.")


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
    Main application window for Meridian Trading System with dark theme and database integration
    """
    
    def __init__(self):
        super().__init__()
        
        # Instance variables
        self.current_session_id: Optional[str] = None
        self.is_modified: bool = False
        self.analysis_thread: Optional[AnalysisThread] = None
        
        # Initialize database service
        self.db_service = DatabaseService()
        
        # Initialize UI
        self._init_ui()
        self._setup_menu_bar()
        self._connect_signals()
        self._connect_database_signals()
        
        logger.info("Main window initialized with dark theme and database service")
    
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
        self.overview_widget.save_data.connect(self._on_save_to_database)
        self.overview_widget.data_changed.connect(self._on_data_changed)
    
    def _setup_menu_bar(self):
        """Create menu bar with database operations"""
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
        load_action = QAction("&Load Session...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._on_load_session)
        file_menu.addAction(load_action)
        
        # Save Session
        save_action = QAction("&Save Session", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_session)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Recent Sessions
        self.recent_menu = file_menu.addMenu("&Recent Sessions")
        self._update_recent_sessions()
        
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
        
        # Database Menu
        db_menu = menubar.addMenu("&Database")
        db_menu.setStyleSheet(DarkStyleSheets.MENU)
        
        # Browse Sessions
        browse_action = QAction("&Browse Sessions", self)
        browse_action.setShortcut("Ctrl+B")
        browse_action.triggered.connect(self._on_browse_sessions)
        db_menu.addAction(browse_action)
        
        # Test Connection
        test_action = QAction("&Test Connection", self)
        test_action.triggered.connect(self._on_test_connection)
        db_menu.addAction(test_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        help_menu.setStyleSheet(DarkStyleSheets.MENU)
        
        # About
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
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
    
    @pyqtSlot()
    def _on_data_changed(self):
        """Handle data change in any widget"""
        self.is_modified = True
        self._update_window_title()
    
    @pyqtSlot(dict)
    def _on_save_to_database(self, data: Dict[str, Any]):
        """Handle saving to database"""
        logger.info(f"Saving session data for {data['ticker']}")
        success, result = self.db_service.save_session(data)
        
        if success:
            self.current_session_id = result
            self.is_modified = False
            self._update_window_title()
            self._update_recent_sessions()
    
    @pyqtSlot()
    def _on_save_session(self):
        """Handle save session menu action"""
        self.overview_widget.validate_and_save()
    
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
                self.overview_widget.validate_and_save()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        # Clear all fields
        self.overview_widget.clear_all()
        self.current_session_id = None
        self.is_modified = False
        self._update_window_title()
        
        logger.info("New session created")
    
    @pyqtSlot()
    def _on_load_session(self):
        """Handle loading a session from database"""
        # Get list of available sessions
        sessions = self.db_service.list_sessions()
        
        if not sessions:
            QMessageBox.information(
                self,
                "No Sessions",
                "No saved sessions found in the database."
            )
            return
        
        # Show session picker dialog
        dialog = SessionPickerDialog(sessions, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.selected_session_id:
                self._load_session_by_id(dialog.selected_session_id)
    
    def _load_session_by_id(self, session_id: str):
        """Load a specific session by ID"""
        session_data = self.db_service.load_session(session_id)
        if session_data:
            self.current_session_id = session_id
            # Note: load_completed signal will handle UI update
    
    @pyqtSlot()
    def _on_browse_sessions(self):
        """Browse all sessions in database"""
        sessions = self.db_service.list_sessions()
        
        if not sessions:
            QMessageBox.information(
                self,
                "No Sessions",
                "No saved sessions found in the database."
            )
            return
        
        # Show session picker dialog in browse mode
        dialog = SessionPickerDialog(sessions, self)
        dialog.setWindowTitle("Browse Sessions")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.selected_session_id:
                self._load_session_by_id(dialog.selected_session_id)
    
    @pyqtSlot()
    def _on_test_connection(self):
        """Test database connection"""
        if self.db_service.client:
            try:
                # Try to list sessions as a connection test
                sessions = self.db_service.list_sessions()
                QMessageBox.information(
                    self,
                    "Connection Test",
                    f"Database connection successful!\n\nFound {len(sessions)} saved sessions."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Connection Test Failed",
                    f"Database connection failed:\n\n{str(e)}"
                )
        else:
            QMessageBox.critical(
                self,
                "Connection Test Failed",
                "Database client not initialized.\nCheck your configuration."
            )
    
    def _update_recent_sessions(self):
        """Update recent sessions menu"""
        self.recent_menu.clear()
        
        # Get recent sessions (last 10)
        sessions = self.db_service.list_sessions()[:10]
        
        if sessions:
            for session in sessions:
                action_text = f"{session['ticker']} - {session['date'].strftime('%Y-%m-%d')}"
                action = QAction(action_text, self)
                action.setData(session['ticker_id'])
                action.triggered.connect(
                    lambda checked, sid=session['ticker_id']: self._load_session_by_id(sid)
                )
                self.recent_menu.addAction(action)
        else:
            no_recent = QAction("No recent sessions", self)
            no_recent.setEnabled(False)
            self.recent_menu.addAction(no_recent)
    
    def _update_window_title(self):
        """Update window title with current session info"""
        title = f"{Config.APP_NAME} v{Config.APP_VERSION}"
        
        if self.current_session_id:
            title += f" - {self.current_session_id}"
        
        if self.is_modified:
            title += " *"
        
        self.setWindowTitle(title)
    
    # Database signal handlers
    @pyqtSlot()
    def _on_save_started(self):
        """Handle save started signal"""
        self.statusBar().showMessage("Saving session to database...")
    
    @pyqtSlot(str)
    def _on_save_completed(self, session_id: str):
        """Handle successful save"""
        self.statusBar().showMessage(f"Session saved successfully: {session_id}", 5000)
        QMessageBox.information(
            self,
            "Save Successful",
            f"Session saved successfully!\nID: {session_id}"
        )
    
    @pyqtSlot(str)
    def _on_save_failed(self, error_msg: str):
        """Handle failed save"""
        self.statusBar().showMessage("Save failed", 5000)
        QMessageBox.critical(
            self,
            "Save Failed",
            f"Failed to save session:\n{error_msg}"
        )
    
    @pyqtSlot()
    def _on_load_started(self):
        """Handle load started signal"""
        self.statusBar().showMessage("Loading session from database...")
    
    @pyqtSlot(dict)
    def _on_load_completed(self, session_data: dict):
        """Handle successful load"""
        # Load data into UI
        self.overview_widget.load_session_data(session_data)
        self.is_modified = False
        self._update_window_title()
        self.statusBar().showMessage("Session loaded successfully", 5000)
    
    @pyqtSlot(str)
    def _on_load_failed(self, error_msg: str):
        """Handle failed load"""
        self.statusBar().showMessage("Load failed", 5000)
        QMessageBox.critical(
            self,
            "Load Failed",
            f"Failed to load session:\n{error_msg}"
        )
    
    @pyqtSlot()
    def _on_show_results(self):
        """Show analysis results window"""
        # TODO: Create results display window
        QMessageBox.information(
            self,
            "Analysis Results",
            "Results window will be implemented to show HVN and Camarilla calculations."
        )
    
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
        self.statusBar().showMessage(f"Analysis: {message} ({progress}%)")
        logger.debug(f"Analysis progress: {progress}% - {message}")
    
    @pyqtSlot(dict)
    def _on_analysis_finished(self, results: dict):
        """Handle analysis completion"""
        # Re-enable run button
        self.overview_widget.run_analysis_btn.setEnabled(True)
        
        # Update displays with results
        self.overview_widget.update_calculations(results)
        
        # TODO: Show results in separate window
        self.statusBar().showMessage("Analysis completed", 5000)
        logger.info("Analysis completed")
    
    @pyqtSlot(str)
    def _on_analysis_error(self, error_msg: str):
        """Handle analysis errors"""
        # Re-enable run button
        self.overview_widget.run_analysis_btn.setEnabled(True)
        
        self.statusBar().showMessage("Analysis failed", 5000)
        
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
        <p style="color: {DarkTheme.TEXT_SECONDARY};">© 2025 Meridian Trading Systems</p>
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