"""
Menu management functionality for the main window
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QAction

from ui.dark_theme import DarkStyleSheets


class MenuManagerMixin:
    """Mixin class for menu bar management"""
    
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