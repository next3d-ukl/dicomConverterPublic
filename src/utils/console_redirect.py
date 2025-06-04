from PyQt5.QtCore import pyqtSignal, QObject
from typing import TextIO
import re

class ConsoleRedirect(QObject):
    """
    Redirects console output to a Qt text widget with progress tracking
    """
    text_written = pyqtSignal(str)
    progress_updated = pyqtSignal(int, int)  # current, total

    def __init__(self, text_edit, original_stream: TextIO, progress_bar=None):
        """
        Initialize console redirect
        
        Args:
            text_edit: QTextEdit widget to redirect output to
            original_stream: Original stream (sys.stdout or sys.stderr)
            progress_bar: Optional progress bar to update with progress information
        """
        super().__init__()
        self.text_edit = text_edit
        self.original_stream = original_stream
        self.progress_bar = progress_bar
        self.text_written.connect(self.write_to_text_edit)
        self.progress_updated.connect(self.update_progress_bar)
        
        # Regular expression to match file progress updates like "5 / 10"
        self.file_progress_pattern = re.compile(r'^\s*(\d+)\s*\/\s*(\d+)\s*$')
        
        # Regular expression to match overall progress like "PROGRESS: 50 / 100"
        self.overall_progress_pattern = re.compile(r'PROGRESS:\s*(\d+)\s*\/\s*(\d+)')
        
        # Track the total number of DICOM images and conversion progress
        self.total_files = 0
        self.current_file = 0
        
        # Is conversion in progress
        self.conversion_in_progress = False

    def write(self, text: str) -> None:
        """
        Write text to both the original stream and emit signal for text edit
        Also check for progress information
        """
        self.text_written.emit(str(text))
        self.original_stream.write(text)
        
        # Check if this text contains progress information
        if self.progress_bar:
            # Check for conversion start
            if "Starting conversion..." in text:
                self.conversion_in_progress = True
                # Use signal to update progress bar on main thread
                self.progress_updated.emit(0, 100)
                
            # Check for conversion finished
            elif "Conversion finished!" in text:
                self.conversion_in_progress = False
                # Use signal to update progress bar on main thread
                self.progress_updated.emit(100, 100)
            
            # First check for direct overall progress updates
            overall_match = self.overall_progress_pattern.search(text.strip())
            if overall_match:
                try:
                    current = int(overall_match.group(1))
                    total = int(overall_match.group(2))
                    self.progress_updated.emit(current, total)
                except (ValueError, IndexError):
                    pass
            # Then check for file progress updates
            else:
                self._check_for_file_progress(text)

    def flush(self) -> None:
        """
        Flush the original stream
        """
        self.original_stream.flush()

    def write_to_text_edit(self, text: str) -> None:
        """
        Append text to the text edit widget
        """
        self.text_edit.append(text)
        
    def update_progress_bar(self, current: int, total: int) -> None:
        """
        Update the progress bar with current progress
        """
        if self.progress_bar and total > 0:
            percent = min(100, int(current * 100 / total))
            self.progress_bar.setValue(percent)
            
    def _check_for_file_progress(self, text: str) -> None:
        """
        Check if the text contains file progress information
        For the initial 70% of the progress bar
        """
        # Look for progress pattern like "5 / 10"
        match = self.file_progress_pattern.match(text.strip())
        if match and self.conversion_in_progress:
            try:
                current = int(match.group(1))
                total = int(match.group(2))
                
                self.current_file = current
                self.total_files = total
                
                # Calculate progress (0-70%)
                if total > 0:
                    # Scale to 70% of the progress bar
                    percent = min(70, int((current * 70) / total))
                    # Use the signal to ensure UI updates happen on the main thread
                    self.progress_updated.emit(percent, 100)
                    
            except (ValueError, IndexError):
                pass