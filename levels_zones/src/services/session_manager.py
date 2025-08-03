"""
Session manager for handling session lifecycle operations
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

from services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class SessionManager(QObject):
    """
    Manages session lifecycle including create, load, save, and tracking
    """
    
    # Signals
    session_created = pyqtSignal(str)  # session_id
    session_loaded = pyqtSignal(dict)  # session_data
    session_saved = pyqtSignal(str)  # session_id
    session_modified = pyqtSignal()
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.db_service = DatabaseService()
        self.current_session_id: Optional[str] = None
        self.is_modified: bool = False
        
        # Connect database signals
        self._connect_db_signals()
    
    def _connect_db_signals(self):
        """Connect to database service signals"""
        self.db_service.save_completed.connect(self._on_save_completed)
        self.db_service.save_failed.connect(self.error_occurred.emit)
        self.db_service.load_completed.connect(self._on_load_completed)
        self.db_service.load_failed.connect(self.error_occurred.emit)
    
    def create_new_session(self):
        """Create a new empty session"""
        self.current_session_id = None
        self.is_modified = False
        self.session_created.emit("")
        logger.info("New session created")
    
    def load_session(self, session_id: str):
        """Load a session by ID"""
        logger.info(f"Loading session: {session_id}")
        session_data = self.db_service.load_session(session_id)
        if session_data:
            self.current_session_id = session_id
            self.is_modified = False
    
    def save_session(self, session_data: Dict[str, Any]):
        """Save session data"""
        logger.info(f"Saving session for {session_data.get('ticker', 'UNKNOWN')}")
        success, result = self.db_service.save_session(session_data)
        return success, result
    
    def mark_modified(self):
        """Mark current session as modified"""
        if not self.is_modified:
            self.is_modified = True
            self.session_modified.emit()
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions"""
        return self.db_service.list_sessions()[:limit]
    
    def get_all_sessions(self, **filters) -> List[Dict[str, Any]]:
        """Get all sessions with optional filters"""
        return self.db_service.list_sessions(**filters)
    
    def _on_save_completed(self, session_id: str):
        """Handle successful save"""
        self.current_session_id = session_id
        self.is_modified = False
        self.session_saved.emit(session_id)
    
    def _on_load_completed(self, session_data: dict):
        """Handle successful load"""
        self.is_modified = False
        self.session_loaded.emit(session_data)
    
    @property
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        return self.is_modified
    
    @property
    def current_session_info(self) -> str:
        """Get current session info for display"""
        return self.current_session_id or "New Session"