import os, sys
import shutil
from pathlib import Path
from typing import List, Optional
from rich.console import Console

console = Console()

class LogLevel:
    INFO = 0
    WARNING = 1
    ERROR = 2

class Logger:
    """Logger class that can output to console or be captured for GUI"""
    
    def __init__(self, gui_mode: bool = False):
        self.gui_mode = gui_mode
        self.log_queue = []
        self.console = Console(highlight=False) if not gui_mode else None
        self.callback = None
    
    def set_callback(self, callback) -> None:
        """Set callback function for GUI mode"""
        self.callback = callback
    
    def log(self, message: str, level: int = LogLevel.INFO) -> None:
        """Log a message with a specific level"""
        if self.gui_mode:
            self.log_queue.append((message, level))
            if self.callback:
                self.callback(message, level)
        else:
            if level == LogLevel.ERROR:
                self.console.print(f"[red]{message}[/red]")
            elif level == LogLevel.WARNING:
                self.console.print(f"[yellow]{message}[/yellow]")
            else:
                self.console.print(message)
    
    def info(self, message: str) -> None:
        """Log an info message"""
        self.log(message, LogLevel.INFO)
    
    def warning(self, message: str) -> None:
        """Log a warning message"""
        self.log(message, LogLevel.WARNING)
    
    def error(self, message: str) -> None:
        """Log an error message"""
        self.log(message, LogLevel.ERROR)
    
    def get_logs(self) -> List[tuple]:
        """Get all logs (for GUI mode)"""
        return self.log_queue

# Create default logger instance
logger = Logger()

def is_ffmpeg_installed() -> bool:
    """Check if ffmpeg is installed"""
    return shutil.which("ffmpeg") is not None

def get_file_name(filename: str) -> str:
    """Get the file name without the extension"""
    return os.path.splitext(filename)[0]

def get_subtitle_file() -> str:
    """Generate a random name for the srt file"""
    return "subtitle-" + str(os.urandom(6).hex()) + ".srt"

def delete_mkv(filename: str) -> bool:
    """Delete the MKV file after conversion"""
    try:
        # Delete the file if it's a valid mkv file
        if os.path.isfile(filename) and (filename.endswith(".mkv") or filename.endswith(".MKV")):
            os.remove(filename)
            logger.info(f"File deleted: {filename}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete file: {filename}")
        logger.error(f"Error: {str(e)}")
        return False

def find_mkv_files(directory: str) -> List[str]:
    """Find all MKV files in a directory recursively"""
    mkv_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".mkv"):
                mkv_files.append(os.path.join(root, file))
    return mkv_files

def validate_mkv_file(file_path: str) -> bool:
    """Validate that a file is a readable MKV file"""
    return (
        os.path.exists(file_path) and 
        os.path.isfile(file_path) and 
        os.access(file_path, os.R_OK) and
        file_path.lower().endswith(".mkv")
    )

def ensure_directory_exists(directory: str) -> None:
    """Ensure that a directory exists, create it if it doesn't"""
    Path(directory).mkdir(parents=True, exist_ok=True)

def get_output_path(input_path: str, output_dir: Optional[str] = None) -> str:
    """Get the output path for a converted file"""
    file_name = get_file_name(input_path)
    if output_dir:
        ensure_directory_exists(output_dir)
        return os.path.join(output_dir, os.path.basename(file_name) + "-mk4.mp4")
    return file_name + "-mk4.mp4"

def print_error(message: str) -> None:
    console.print(f"[red]{message}[/red]")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)