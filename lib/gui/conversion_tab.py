"""
Conversion tab for mk4 GUI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QCheckBox, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject

from lib.gui.components import (
    FileListWidget, ConversionProgressWidget, TrackSelectorWidget,
    FileSelector, LogViewer
)
from lib.utils import get_output_path, logger
from lib.gui.conversion import (
    process_file_gui
)
from lib.gui.subtitles import analyze_file_streams

from lib.config import config_manager

class ConversionWorker(QObject):
    """
    Worker thread for file conversion
    """
    progressChanged = pyqtSignal(dict)
    fileStarted = pyqtSignal(str)
    fileFinished = pyqtSignal(str, bool)
    allFilesFinished = pyqtSignal()
    logMessage = pyqtSignal(str, int)
    
    def __init__(self):
        super().__init__()
        self.files = []
        self.output_dir = None
        self.delete_after = False
        self.subtitle_index = None
        self.audio_index = None
        self._is_running = False
        self._cancel_requested = False
        self._skip_files = set()
    
    def set_files(self, files, output_dir=None, delete_after=False,
                 subtitle_index=None, audio_index=None):
        """Set files to process"""
        self.files = files
        self.output_dir = output_dir
        self.delete_after = delete_after
        self.subtitle_index = subtitle_index if subtitle_index != -1 else None
        self.audio_index = audio_index if audio_index != -1 else None
        self._skip_files.clear() 

    def skip_file(self, file_path):
        """Skip specific file from conversion"""
        # Ajouter à l'ensemble des fichiers à ignorer
        if not hasattr(self, '_skip_files'):
            self._skip_files = set()
        self._skip_files.add(file_path)
        self.logMessage.emit(f"Skipping file: {file_path}", 1)
        
        # Si le fichier est en cours de traitement, annuler le processus actuel
        if hasattr(self, '_current_file') and self._is_running and self._current_file == file_path:
            self._cancel_requested = True
            self.logMessage.emit("Canceling current conversion...", 1)


    def cancel(self):
        """Cancel the conversion process"""
        self._cancel_requested = True
    
    def run(self):
        """Process all files"""
        self._is_running = True
        self._cancel_requested = False

        if not hasattr(self, '_skip_files'):
            self._skip_files = set()

        
        # Setup logger callback
        def log_callback(message, level):
            self.logMessage.emit(message, level)
        
        total_files = len(self.files)
        successful_files = 0
        
        for i, file_path in enumerate(self.files):
            # Skip file if requested or global cancel
            if self._cancel_requested or file_path in self._skip_files:
                self.logMessage.emit(f"Skipping file {i+1}/{total_files}: {file_path}", 1)
                self.fileFinished.emit(file_path, False)
                continue

            self._current_file = file_path
            self.fileStarted.emit(file_path)
            self.logMessage.emit(f"Processing file {i+1}/{total_files}: {file_path}", 0)

            # Determine output path
            output_path = get_output_path(file_path, self.output_dir)

            # Process progress updates
            def progress_callback(progress_data):
                # Vérifier si l'annulation a été demandée
                if self._cancel_requested or file_path in self._skip_files:
                    progress_data["cancel_requested"] = True

                # Add overall file progress
                overall = (i + progress_data.get("overall_progress", 0)) / total_files
                progress_data["overall_file_progress"] = overall
                progress_data["current_file"] = file_path
                progress_data["current_file_index"] = i
                progress_data["total_files"] = total_files
                self.progressChanged.emit(progress_data)

            # Process the file
            success = process_file_gui(
                file_path,
                self.delete_after,
                self.subtitle_index,
                self.audio_index,
                output_path,
                progress_callback
            )

            if success:
                successful_files += 1
                self.logMessage.emit(f"Successfully converted: {file_path}", 0)
            else:
                self.logMessage.emit(f"Failed to convert: {file_path}", 2)

            self.fileFinished.emit(file_path, success)

            self._cancel_requested = False
        
        self.logMessage.emit(f"Conversion completed. {successful_files}/{total_files} files converted successfully.", 0)
        self._is_running = False
        self._current_file = None
        self.allFilesFinished.emit()

class ConversionTab(QWidget):
    """
    Conversion tab with file selection and conversion controls
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup main layout
        main_layout = QVBoxLayout(self)
        
        # Create two main sections with splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Top section: File selection and options
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        # Files group
        files_group = QGroupBox("Files")
        files_layout = QVBoxLayout()
        
        self.file_list = FileListWidget()
        self.file_list.selectionChanged.connect(self.on_file_selection_changed)
        files_layout.addWidget(self.file_list)
        
        files_group.setLayout(files_layout)
        top_layout.addWidget(files_group)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        # Track selection
        self.track_selector = TrackSelectorWidget()
        options_layout.addWidget(self.track_selector)
        
        # Output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Directory:"))
        
        self.output_dir_selector = FileSelector(file_type="directory")
        output_layout.addWidget(self.output_dir_selector)
        
        options_layout.addLayout(output_layout)
        
        # Delete original checkbox
        self.delete_checkbox = QCheckBox("Delete original MKV files after conversion")
        self.delete_checkbox.setChecked(config_manager.config.getboolean('GUI', 'AutoDeleteMKV', fallback=False))
        options_layout.addWidget(self.delete_checkbox)
        
        options_group.setLayout(options_layout)
        top_layout.addWidget(options_group)
        
        # Bottom section: Progress and log
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        
        # Left: Conversion progress
        progress_group = QGroupBox("Conversion Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_widget = ConversionProgressWidget()
        self.progress_widget.start_button.clicked.connect(self.start_conversion)
        self.progress_widget.cancel_button.clicked.connect(self.cancel_conversion)
        progress_layout.addWidget(self.progress_widget)
        
        progress_group.setLayout(progress_layout)
        bottom_layout.addWidget(progress_group, 1)
        
        # Right: Log viewer
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.log_viewer = LogViewer()
        log_layout.addWidget(self.log_viewer)
        
        log_group.setLayout(log_layout)
        bottom_layout.addWidget(log_group, 1)
        
        # Add sections to splitter
        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([300, 300])  # Initial sizes
        
        main_layout.addWidget(splitter)
        
        # Setup worker thread
        self.worker = ConversionWorker()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker.progressChanged.connect(self.update_progress)
        self.worker.fileStarted.connect(self.on_file_started)
        self.worker.fileFinished.connect(self.on_file_finished)
        self.worker.allFilesFinished.connect(self.on_all_files_finished)
        self.worker.logMessage.connect(self.log_viewer.add_log)
        self.file_list.fileRemoved.connect(self.on_file_removed)
        
        # Connect worker.run to thread start
        self.worker_thread.started.connect(self.worker.run)
        
        # Initialize custom logger
        self._setup_logger()
        self.file_track_selections = {}
        self.track_selector.subtitle_combo.currentIndexChanged.connect(self.on_track_selection_changed)
        self.track_selector.audio_combo.currentIndexChanged.connect(self.on_track_selection_changed)

    def on_track_selection_changed(self, index):
        """Handle track selection change"""
        # check if a file is selected
        if hasattr(self, '_last_selected_file') and self._last_selected_file:
            subtitle_index, audio_index = self.track_selector.get_selected_tracks()
            self.file_track_selections[self._last_selected_file] = (subtitle_index, audio_index)
            
            # get the display texts
            subtitle_text = self.track_selector.subtitle_combo.currentText()
            audio_text = self.track_selector.audio_combo.currentText()
            
            # extract the actual track info
            if subtitle_text != "Auto-select" and ":" in subtitle_text:
                subtitle_text = subtitle_text.split(":", 1)[1].strip()
            
            if audio_text != "Auto-select" and ":" in audio_text:
                audio_text = audio_text.split(":", 1)[1].strip()
            
            # update displau
            self.file_list.update_file_tracks(self._last_selected_file, subtitle_text, audio_text)

    def on_file_removed(self, file_path):
        """Handle when a file is removed from the list"""
        # if a conversion is in progress, skip the file
        if self.worker_thread.isRunning():
            self.worker.skip_file(file_path)
            self.log_viewer.add_log(f"Cancelled conversion for: {file_path}", 1)


    def _setup_logger(self):
        """Setup logger for GUI mode"""
        global logger
        from lib.utils import logger, Logger
        
        gui_logger = Logger(gui_mode=True)
        gui_logger.set_callback(self.log_viewer.add_log)
        logger = gui_logger
    
    def on_file_selection_changed(self, selected_files):
        """Handle file selection change"""
        current_subtitle, current_audio = self.track_selector.get_selected_tracks()
        if hasattr(self, '_last_selected_file') and self._last_selected_file:
            self.file_track_selections[self._last_selected_file] = (current_subtitle, current_audio)
            
            subtitle_text = self.track_selector.subtitle_combo.currentText()
            audio_text = self.track_selector.audio_combo.currentText()
            if ":" in subtitle_text:
                subtitle_text = subtitle_text.split(":", 1)[1].strip()
            if ":" in audio_text:
                audio_text = audio_text.split(":", 1)[1].strip()
            self.file_list.update_file_tracks(self._last_selected_file, subtitle_text, audio_text)

        if len(selected_files) == 1:
            file_path = selected_files[0]
            self._last_selected_file = file_path
            
            try:
                # analyzed ata from the file
                file_info = analyze_file_streams(file_path)
                
                # prepare track lists
                subtitle_tracks = []
                audio_tracks = []
                
                if "streams" in file_info:
                    # count all tracks for audio subtitle
                    subtitle_count = 0
                    audio_count = 0
                    
                    for stream in file_info["streams"]:
                        codec_type = stream.get("codec_type", "unknown")
                        
                        # get info from the stream
                        lang = stream.get("tags", {}).get("language", "unknown")
                        codec_name = stream.get("codec_name", "unknown")
                        
                        # check if its a default track
                        is_default = stream.get("disposition", {}).get("default", 0) == 1
                        
                        # create desc for the track
                        display_info = f"{lang} ({codec_name})"
                        
                        if codec_type == "subtitle":
                            subtitle_tracks.append({
                                "index": subtitle_count, 
                                "info": display_info,
                                "default": is_default
                            })
                            subtitle_count += 1
                        elif codec_type == "audio":
                            audio_tracks.append({
                                "index": audio_count, 
                                "info": display_info,
                                "default": is_default
                            })
                            audio_count += 1

                # Show different tracks on the selector
                self.track_selector.set_tracks(subtitle_tracks, audio_tracks)
                if file_path in self.file_track_selections:
                    subtitle_index, audio_index = self.file_track_selections[file_path]
                    self.track_selector.set_selected_tracks(subtitle_index, audio_index)
                    
                    # Update badge display
                    subtitle_text = "Auto-select"
                    audio_text = "Auto-select"
                    
                    for track in subtitle_tracks:
                        if track['index'] == subtitle_index:
                            subtitle_text = track['info']
                            break
                            
                    for track in audio_tracks:
                        if track['index'] == audio_index:
                            audio_text = track['info']
                            break
                            
                    self.file_list.update_file_tracks(file_path, subtitle_text, audio_text)

                # print logss
                self.log_viewer.add_log(f"Found {len(subtitle_tracks)} subtitle tracks and {len(audio_tracks)} audio tracks", 0)
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to read tracks from file: {str(e)}")
                self.log_viewer.add_log(f"Error reading tracks: {str(e)}", 2)


        
    def update_progress(self, progress_data):
        """Update progress display"""
        self.progress_widget.update_progress(progress_data)
    
    def on_file_started(self, file_path):
        """Handle file processing started"""
        self.progress_widget.set_current_file(file_path)
        self.progress_widget.set_status("Converting...")
    
    def on_file_finished(self, file_path, success):
        """Handle file processing finished"""
        status = "Successfully converted" if success else "Failed to convert"
        self.progress_widget.set_status(status)
    
    def on_all_files_finished(self):
        """Handle all files finished"""
        self.progress_widget.set_status("All files processed")
        self.progress_widget.start_button.setEnabled(True)
        self.progress_widget.cancel_button.setEnabled(False)
    
    def start_conversion(self):
        """Start conversion process"""
        files = self.file_list.get_all_files()
        
        if not files:
            QMessageBox.warning(self, "No Files", "Please add at least one MKV file to convert.")
            return
        
        # Get options
        output_dir = self.output_dir_selector.get_path()
        delete_after = self.delete_checkbox.isChecked()
        subtitle_index, audio_index = self.track_selector.get_selected_tracks()
        
        # Save delete preference
        config_manager.update_config('GUI', 'AutoDeleteMKV', str(delete_after))
        
        # Setup worker
        self.worker.set_files(
            files,
            output_dir if output_dir else None,
            delete_after,
            subtitle_index,
            audio_index
        )
        
        # Clear log and reset progress
        self.log_viewer.clear_logs()
        self.progress_widget.reset()
        
        # Update UI
        self.progress_widget.start_button.setEnabled(False)
        self.progress_widget.cancel_button.setEnabled(True)
        
        # Start thread
        if not self.worker_thread.isRunning():
            self.worker_thread.start()
        else:
            self.worker.run()
    
    def cancel_conversion(self):
        """Cancel conversion process"""
        self.worker.cancel()
        self.progress_widget.set_status("Cancelling...")
        self.progress_widget.cancel_button.setEnabled(False)