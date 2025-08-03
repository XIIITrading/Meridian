"""
Database-related signal handlers for the main window
"""

import logging
from typing import Dict, Any

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import pyqtSlot

logger = logging.getLogger(__name__)


class DatabaseHandlersMixin:
    """Mixin class for handling database-related signals"""
    
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
    
    def _load_session_by_id(self, session_id: str):
        """Load a specific session by ID"""
        session_data = self.db_service.load_session(session_id)
        if session_data:
            self.current_session_id = session_id
            # Note: load_completed signal will handle UI update