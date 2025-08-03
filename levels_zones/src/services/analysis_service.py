"""
Analysis service that provides Qt signal integration for analysis operations
"""

import logging
from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from analysis.analysis_coordinator import AnalysisCoordinator, AnalysisRequest

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """Worker thread for analysis operations"""
    
    progress = pyqtSignal(int, str)
    completed = pyqtSignal(dict)
    failed = pyqtSignal(str)
    
    def __init__(self, request: AnalysisRequest):
        super().__init__()
        self.request = request
        self.coordinator = AnalysisCoordinator()
    
    def run(self):
        """Run analysis in thread"""
        try:
            result = self.coordinator.analyze(
                self.request,
                progress_callback=self._progress_callback
            )
            
            if result.status == 'completed':
                self.completed.emit({
                    'status': result.status,
                    'timestamp': result.timestamp,
                    **result.formatted_results
                })
            else:
                self.failed.emit(f"Analysis failed: {', '.join(result.errors)}")
                
        except Exception as e:
            logger.error(f"Analysis worker error: {str(e)}")
            self.failed.emit(str(e))
    
    def _progress_callback(self, percentage, message):
        """Progress callback for coordinator"""
        self.progress.emit(percentage, message)


class AnalysisService(QObject):
    """
    Service class for analysis operations with Qt signal support
    """
    
    # Signals
    analysis_started = pyqtSignal(str)  # ticker
    analysis_progress = pyqtSignal(int, str)  # percentage, message
    analysis_completed = pyqtSignal(dict)  # results
    analysis_failed = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.worker = None
    
    def run_analysis(self, session_data: Dict[str, Any], analysis_types=None):
        """
        Run analysis for session data
        
        Args:
            session_data: Session data from UI
            analysis_types: Optional list of analysis types to run
        """
        if self.worker and self.worker.isRunning():
            logger.warning("Analysis already in progress")
            return
        
        ticker = session_data.get('ticker', 'UNKNOWN')
        self.analysis_started.emit(ticker)
        
        # Create analysis request
        request = AnalysisRequest(
            ticker=ticker,
            analysis_datetime=session_data['datetime'],
            session_data=session_data,
            analysis_types=analysis_types
        )
        
        # Create and start worker
        self.worker = AnalysisWorker(request)
        self.worker.progress.connect(self.analysis_progress.emit)
        self.worker.completed.connect(self._on_completed)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()
    
    def _on_completed(self, results: dict):
        """Handle analysis completion"""
        self.analysis_completed.emit(results)
    
    def _on_failed(self, error: str):
        """Handle analysis failure"""
        self.analysis_failed.emit(error)
    
    def is_running(self) -> bool:
        """Check if analysis is currently running"""
        return self.worker is not None and self.worker.isRunning()
    
    def stop(self):
        """Stop current analysis if running"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()