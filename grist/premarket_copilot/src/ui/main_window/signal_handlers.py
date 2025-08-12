"""
Signal handler methods for the main window
"""

import logging
from typing import Dict, Any

from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtCore import pyqtSlot, Qt

from ui.dark_theme import DarkTheme
from ui.dialogs.session_picker_dialog import SessionPickerDialog
from ui.threads.analysis_thread import AnalysisThread
from config import Config

logger = logging.getLogger(__name__)


class SignalHandlersMixin:
    """Mixin class for handling signals in the main window"""
    
    @pyqtSlot(dict)
    def _on_market_data_ready(self, data: dict):
        """Handle market data fetch completion"""
        if 'metrics' in data:
            self.overview_widget.metrics_frame.update_metrics(data['metrics'])
        self.statusBar().showMessage("Market data updated", 3000)
    
    @pyqtSlot(dict)
    def _on_fetch_market_data(self, params: dict):
        """Handle request to fetch market data"""
        ticker = params.get('ticker')
        datetime_val = params.get('datetime')
        
        if ticker and datetime_val:
            self.polygon_service.fetch_market_data(ticker, datetime_val)
    
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
        
        # TODO: Save analysis results to database
        if self.current_session_id and 'raw_hvn_results' in results:
            # Create analysis run
            run_id = self.db_service.client.create_analysis_run(
                self.current_session_id,
                run_type='manual'
            )
            
            if run_id:
                # Save HVN results
                # self.db_service.client.save_hvn_results(...)
                
                # Complete the run
                self.db_service.client.complete_analysis_run(run_id)
        
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
        <p style="color: {DarkTheme.TEXT_SECONDARY};">A pre-market trading analysis system with HVN and Camarilla calculations.</p>
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