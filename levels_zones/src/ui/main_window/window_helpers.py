"""
Window helper methods for the main window
"""

from config import Config


class WindowHelpersMixin:
    """Mixin class for window-related helper methods"""
    
    def _update_window_title(self):
        """Update window title with current session info"""
        title = f"{Config.APP_NAME} v{Config.APP_VERSION}"
        
        if self.current_session_id:
            title += f" - {self.current_session_id}"
        
        if self.is_modified:
            title += " *"
        
        self.setWindowTitle(title)