"""
Reusable GUI components for mk4
"""
import os
import subprocess
import tempfile

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QProgressBar, QLabel, QFileDialog,
    QHBoxLayout, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QComboBox, QTextEdit, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPalette

from lib.gui.styles import *
from lib.utils import logger

class ThumbnailGenerator(QObject):
    """Worker thread for generating thumbnails"""
    thumbnailReady = pyqtSignal(str, str)  # file_path, thumbnail_path
    
    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
    
    def generate_thumbnail(self, file_path):
        """Generate thumbnail for a video file"""
        try:
            # create unique filename for thumbanil
            thumbnail_path = os.path.join(
                self.temp_dir, 
                f"thumb_{os.path.basename(file_path)}.jpg"
            )
            
            # extract a picture 10s from the start of the video (based)
            subprocess.run([
                "ffmpeg", "-y", "-ss", "10", "-i", file_path,
                "-vframes", "1", "-vf", "scale=120:-1", 
                thumbnail_path
            ], capture_output=True)
            
            # emit signal with thumbnail path
            self.thumbnailReady.emit(file_path, thumbnail_path)
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {str(e)}")
            # emit empty string if error occured
            self.thumbnailReady.emit(file_path, "")

class FileItemWidget(QWidget):
    """Custom widget for file items with thumbnail and cancel button"""
    cancelClicked = pyqtSignal(str)
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(120, 68)  # 16:9 ratio
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setStyleSheet("border: 1px solid #aaa; background-color: #eee;")
        layout.addWidget(self.thumbnail_label)
        
        # File info container
        file_info_layout = QVBoxLayout()
        file_info_layout.setSpacing(2)
        file_info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filename and badge container
        filename_layout = QHBoxLayout()
        filename_layout.setSpacing(5)
        filename_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filename
        self.filename_label = QLabel(os.path.basename(file_path))
        self.filename_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.filename_label.setToolTip(file_path)
        filename_layout.addWidget(self.filename_label)
        
        # Subtitle badge
        self.sub_badge = QLabel("Sub: Auto")
        self.sub_badge.setStyleSheet("""
            background-color: #3498db; 
            color: white; 
            border-radius: 3px; 
            padding: 1px 4px; 
            font-size: 8pt;
        """)
        self.sub_badge.setFixedHeight(16)
        self.sub_badge.setVisible(False)  # Hidden by default
        filename_layout.addWidget(self.sub_badge)
        
        # Audio badge
        self.audio_badge = QLabel("Audio: Auto")
        self.audio_badge.setStyleSheet("""
            background-color: #2ecc71; 
            color: white; 
            border-radius: 3px; 
            padding: 1px 4px; 
            font-size: 8pt;
        """)
        self.audio_badge.setFixedHeight(16)
        self.audio_badge.setVisible(False)  # Hidden by default
        filename_layout.addWidget(self.audio_badge)
        
        file_info_layout.addLayout(filename_layout)
        layout.addLayout(file_info_layout)
        
        # Cancel button
        cancel_button = QPushButton("×")
        cancel_button.setFixedSize(24, 24)
        cancel_button.setToolTip("Remove from list")
        cancel_button.clicked.connect(self._on_cancel_clicked)
        layout.addWidget(cancel_button)
        
        self.setLayout(layout)
    
    def _on_cancel_clicked(self):
        """Handle cancel button click"""
        self.cancelClicked.emit(self.file_path)
    
    def set_thumbnail(self, thumbnail_path):
        """Set the thumbnail image"""
        if thumbnail_path and os.path.exists(thumbnail_path):
            pixmap = QPixmap(thumbnail_path)
            self.thumbnail_label.setPixmap(pixmap)
        else:
            # Thumbnail not available, show placeholder
            self.thumbnail_label.setText("No Preview")

    def update_tracks_info(self, subtitle_info, audio_info):
        """Update the tracks information display with badges"""
        # Update subtitle badge
        if subtitle_info != "Auto-select":
            # only extract language if possible (it's often the case idk)
            lang = subtitle_info
            if "(" in subtitle_info:
                lang = subtitle_info.split("(")[0].strip()
            
            self.sub_badge.setText(f"Sub: {lang}")
            self.sub_badge.setVisible(True)
        else:
            self.sub_badge.setVisible(False)
        
        # Update audio badge
        if audio_info != "Auto-select":
            # same here about languyage
            lang = audio_info
            if "(" in audio_info:
                lang = audio_info.split("(")[0].strip()
            
            self.audio_badge.setText(f"Audio: {lang}")
            self.audio_badge.setVisible(True)
        else:
            self.audio_badge.setVisible(False)

class Theme:
    """
    Theme manager for the application
    """
    @staticmethod
    def apply_theme(app, widget, theme_name="light"):
        """Apply theme to widget and all children"""
        if theme_name not in THEMES:
            theme_name = "light"
        
        theme = THEMES[theme_name]
        
        # Set application-wide palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(theme["primary"]))
        palette.setColor(QPalette.WindowText, QColor(theme["text"]))
        palette.setColor(QPalette.Base, QColor(theme["secondary"]))
        palette.setColor(QPalette.AlternateBase, QColor(theme["primary"]))
        palette.setColor(QPalette.ToolTipBase, QColor(theme["primary"]))
        palette.setColor(QPalette.ToolTipText, QColor(theme["text"]))
        palette.setColor(QPalette.Text, QColor(theme["text"]))
        palette.setColor(QPalette.Button, QColor(theme["secondary"]))
        palette.setColor(QPalette.ButtonText, QColor(theme["text"]))
        palette.setColor(QPalette.Link, QColor(theme["accent"]))
        palette.setColor(QPalette.Highlight, QColor(theme["accent"]))
        palette.setColor(QPalette.HighlightedText, QColor(theme["text"]))
        
        app.setPalette(palette)
        
        # Apply styles to specific widgets
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {theme["primary"]};
                color: {theme["text"]};
            }}
            
            QMainWindow, QDialog {{
                background-color: {theme["primary"]};
            }}
            
            QTabWidget::pane {{ 
                border: 1px solid {theme["border"]};
                background-color: {theme["primary"]};
            }}
            
            QTabBar::tab {{
                background-color: {theme["secondary"]};
                padding: 8px 12px;
                margin-right: 4px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {theme["accent"]};
                color: white;
            }}
            
            {BUTTON_STYLE}
            QPushButton {{
                background-color: {theme["accent"]};
                color: white;
                border: none;
            }}
            
            QPushButton:disabled {{
                background-color: {theme["border"]};
            }}
            
            {PROGRESS_BAR_STYLE}
            QProgressBar {{
                background-color: {theme["secondary"]};
                color: {theme["text"]};
            }}
            
            QProgressBar::chunk {{
                background-color: {theme["accent"]};
            }}
            
            {TEXTBOX_STYLE}
            QLineEdit, QTextEdit {{
                background-color: {theme["secondary"]};
                color: {theme["text"]};
                border-color: {theme["border"]};
            }}
            
            {COMBOBOX_STYLE}
            QComboBox {{
                background-color: {theme["secondary"]};
                color: {theme["text"]};
                border-color: {theme["border"]};
            }}
            
            {LIST_VIEW_STYLE}
            QListView, QListWidget {{
                background-color: {theme["secondary"]};
                color: {theme["text"]};
                border-color: {theme["border"]};
            }}
            
            QGroupBox {{
                border: 1px solid {theme["border"]};
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            
            QStatusBar {{
                background-color: {theme["secondary"]};
                color: {theme["text"]};
            }}
        """)

class StyledButton(QPushButton):
    """
    Styled button with primary and secondary variants
    """
    def __init__(self, text, variant="primary", icon=None, parent=None):
        super().__init__(text, parent)
        self.variant = variant
        
        if icon:
            self.setIcon(QIcon(icon))
            self.setIconSize(QSize(ICON_NORMAL, ICON_NORMAL))
        
        # Set fixed height for consistent look
        self.setMinimumHeight(32)

    def update_style(self, theme):
        """Update button style based on theme and variant"""
        if self.variant == "primary":
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme["accent"]};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {theme["accent"]};
                    opacity: 0.9;
                }}
                QPushButton:pressed {{
                    opacity: 0.8;
                }}
                QPushButton:disabled {{
                    background-color: {theme["border"]};
                    opacity: 0.6;
                }}
            """)
        else:  # secondary button
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme["secondary"]};
                    color: {theme["text"]};
                    border: 1px solid {theme["border"]};
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {theme["primary"]};
                }}
                QPushButton:pressed {{
                    opacity: 0.8;
                }}
                QPushButton:disabled {{
                    opacity: 0.6;
                }}
            """)

class FileSelector(QWidget):
    """
    File selector widget with browse button
    """
    fileSelected = pyqtSignal(str)
    
    def __init__(self, file_type="file", file_filter="MKV Files (*.mkv)", parent=None):
        super().__init__(parent)
        self.file_type = file_type  # "file" or "directory"
        self.file_filter = file_filter
        
        # Setup layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Path input
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(f"Select {file_type}...")
        layout.addWidget(self.path_input, 1)
        
        # Browse button
        self.browse_button = StyledButton("Browse", "secondary")
        self.browse_button.setMaximumWidth(100)
        self.browse_button.clicked.connect(self.browse)
        layout.addWidget(self.browse_button)
        
        self.setLayout(layout)
    
    def browse(self):
        """Open file dialog to select file or directory"""
        if self.file_type == "directory":
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", "", self.file_filter)
        
        if path:
            self.path_input.setText(path)
            self.fileSelected.emit(path)
    
    def get_path(self):
        """Get the currently selected path"""
        return self.path_input.text()
    
    def set_path(self, path):
        """Set the path"""
        self.path_input.setText(path)

class LogViewer(QWidget):
    """
    Log viewer widget with colored log messages
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup layout
        layout = QVBoxLayout(self)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        self.setLayout(layout)
    
    def add_log(self, message, level=0):
        """
        Add a log message with appropriate styling
        
        Args:
            message: The log message
            level: 0=info, 1=warning, 2=error
        """
        color = "white"
        if level == 1:  # warning
            color = THEMES["light"]["warning"]
        elif level == 2:  # error
            color = THEMES["light"]["error"]
        
        # Add timestamp and message
        self.log_display.append(f'<span style="color:{color};">{message}</span>')
        
        # Auto-scroll to bottom
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )
    
    def clear_logs(self):
        """Clear all logs"""
        self.log_display.clear()

class FileListWidget(QWidget):
    """
    Widget to display and manage a list of files
    """
    fileRemoved = pyqtSignal(str)
    selectionChanged = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup layout
        layout = QVBoxLayout(self)
        
        # Create list widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)
        
        # Supprimer cette ligne qui cause l'erreur
        # self.setSelectionMode(QListWidget.ExtendedSelection)
        # self.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Setup thumbnail generator thread
        self.thumbnail_generator = ThumbnailGenerator()
        self.thumbnail_thread = QThread()
        self.thumbnail_generator.moveToThread(self.thumbnail_thread)
        self.thumbnail_generator.thumbnailReady.connect(self._on_thumbnail_ready)
        self.thumbnail_thread.start()
        
        # Buttons row
        button_layout = QHBoxLayout()
        
        self.add_button = StyledButton("Add Files", "secondary")
        self.add_button.clicked.connect(self.add_files)
        button_layout.addWidget(self.add_button)
        
        self.add_dir_button = StyledButton("Add Folder", "secondary")
        self.add_dir_button.clicked.connect(self.add_directory)
        button_layout.addWidget(self.add_dir_button)
        
        self.remove_button = StyledButton("Remove", "secondary")
        self.remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(self.remove_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self.file_paths = []  # Store actual file paths
        self.file_items = {}

    def update_file_tracks(self, file_path, subtitle_info, audio_info):
        """Update tracks info for a file"""
        if file_path in self.file_items:
            _, item_widget = self.file_items[file_path]
            item_widget.update_tracks_info(subtitle_info, audio_info)

    def _on_thumbnail_ready(self, file_path, thumbnail_path):
        """Handle thumbnail generation completion"""
        if file_path in self.file_items:
            _, item_widget = self.file_items[file_path]
            item_widget.set_thumbnail(thumbnail_path)

    def _on_file_removed(self, file_path):
        """Handle file removed from UI"""
        self.remove_file(file_path)

    def add_files(self, file_paths=None):
        """Add files to the list"""
        # Si aucun chemin n'est fourni, ouvrir la boîte de dialogue
        if file_paths is None or isinstance(file_paths, bool):
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Select MKV Files", "", "MKV Files (*.mkv)"
            )
        
        # Si file_paths est une chaîne unique, la convertir en liste
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        # Ajouter les fichiers
        for file_path in file_paths:
            if file_path not in self.file_items:
                # Create item widget
                item_widget = FileItemWidget(file_path)
                item_widget.cancelClicked.connect(self._on_file_removed)
                
                # Create list item and set widget
                item = QListWidgetItem(self.list_widget)
                item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, item_widget)
                
                # Store mapping
                self.file_items[file_path] = (item, item_widget)
                
                # Generate thumbnail in background
                QThread.currentThread().msleep(100)  # Small delay to avoid UI freeze
                self.thumbnail_generator.generate_thumbnail(file_path)


    def remove_file(self, file_path):
        """Remove a file from the list"""
        if file_path in self.file_items:
            item, _ = self.file_items[file_path]
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            del self.file_items[file_path]
            self.fileRemoved.emit(file_path)


    def add_directory(self):
        """Add all MKV files from a directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        
        if directory:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(".mkv"):
                        file_path = os.path.join(root, file)
                        if file_path not in self.file_paths:
                            self.file_paths.append(file_path)
                            self.list_widget.addItem(os.path.basename(file_path))
    
    def remove_selected(self):
        """Remove selected files from the list"""
        selected_indexes = [self.list_widget.row(item) for item in self.list_widget.selectedItems()]
        # Remove from highest index to lowest to avoid changing indexes
        for index in sorted(selected_indexes, reverse=True):
            self.list_widget.takeItem(index)
            self.file_paths.pop(index)
    
    def get_selected_files(self):
        """Get currently selected files"""
        selected_items = self.list_widget.selectedItems()
        selected_files = []
        
        for item in selected_items:
            for file_path, (item_ref, _) in self.file_items.items():
                if item_ref == item:
                    selected_files.append(file_path)
        
        return selected_files

        
    def get_all_files(self):
        """Get list of all file paths"""
        return list(self.file_items.keys())
    
    def clear(self):
        """Clear the file list"""
        self.list_widget.clear()
        self.file_paths = []
    
    def _on_selection_changed(self):
        """Emit signal when selection changes"""
        self.selectionChanged.emit(self.get_selected_files())

class ConversionProgressWidget(QWidget):
    """
    Widget to display conversion progress with detailed steps
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup layout
        main_layout = QVBoxLayout(self)
        
        # Current file display
        self.current_file_label = QLabel("No file selected")
        main_layout.addWidget(self.current_file_label)
        
        # Overall progress bar
        self.overall_progress_label = QLabel("Overall Progress:")
        main_layout.addWidget(self.overall_progress_label)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        main_layout.addWidget(self.overall_progress)
        
        # Step progress
        self.step_frame = QFrame()
        step_layout = QVBoxLayout(self.step_frame)
        
        self.current_step_label = QLabel("Current Step:")
        step_layout.addWidget(self.current_step_label)
        
        self.step_progress = QProgressBar()
        self.step_progress.setRange(0, 100)
        self.step_progress.setValue(0)
        step_layout.addWidget(self.step_progress)
        
        self.step_frame.setLayout(step_layout)
        main_layout.addWidget(self.step_frame)
        
        # Status display
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = StyledButton("Start Conversion", "primary")
        button_layout.addWidget(self.start_button)
        
        self.cancel_button = StyledButton("Cancel", "secondary")
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Add a spacer
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def update_progress(self, progress_data):
        """Update progress displays"""
        if "overall_progress" in progress_data:
            self.overall_progress.setValue(int(progress_data["overall_progress"] * 100))
        
        if "step" in progress_data and "step_progress" in progress_data:
            self.current_step_label.setText(f"Current Step: {progress_data['step']}")
            self.step_progress.setValue(int(progress_data["step_progress"] * 100))
    
    def set_current_file(self, filename):
        """Set the current file being processed"""
        self.current_file_label.setText(f"Processing: {os.path.basename(filename)}")
    
    def set_status(self, status):
        """Set the status message"""
        self.status_label.setText(status)
    
    def reset(self):
        """Reset the progress displays"""
        self.current_file_label.setText("No file selected")
        self.overall_progress.setValue(0)
        self.step_progress.setValue(0)
        self.current_step_label.setText("Current Step:")
        self.status_label.setText("Ready")

class TrackSelectorWidget(QWidget):
    """
    Widget to select subtitle and audio tracks
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup layout
        layout = QVBoxLayout(self)
        
        # Subtitle tracks
        subtitle_layout = QHBoxLayout()
        subtitle_layout.addWidget(QLabel("Subtitle Track:"))
        
        self.subtitle_combo = QComboBox()
        self.subtitle_combo.addItem("Auto-select", -1)
        subtitle_layout.addWidget(self.subtitle_combo)
        
        layout.addLayout(subtitle_layout)
        
        # Audio tracks
        audio_layout = QHBoxLayout()
        audio_layout.addWidget(QLabel("Audio Track:"))
        
        self.audio_combo = QComboBox()
        self.audio_combo.addItem("Auto-select", -1)
        audio_layout.addWidget(self.audio_combo)
        
        layout.addLayout(audio_layout)
        
        self.setLayout(layout)

    def set_selected_tracks(self, subtitle_index, audio_index):
        """Set selected tracks by index"""
        # select subtitle track
        index = self.subtitle_combo.findData(subtitle_index)
        if index >= 0:
            self.subtitle_combo.setCurrentIndex(index)
        
        # select audio track
        index = self.audio_combo.findData(audio_index)
        if index >= 0:
            self.audio_combo.setCurrentIndex(index)

    def set_tracks(self, subtitle_tracks, audio_tracks):
        """Set available subtitle and audio tracks"""
        # save actual selected indexes
        current_subtitle_index = self.subtitle_combo.currentData()
        current_audio_index = self.audio_combo.currentData()
        
        # reset all list
        self.subtitle_combo.blockSignals(True)
        self.audio_combo.blockSignals(True)
        
        self.subtitle_combo.clear()
        self.audio_combo.clear()
        
        # add "auto select" option by default
        self.subtitle_combo.addItem("Auto select", -1)
        self.audio_combo.addItem("Auto select", -1)
        
        subtitle_select_index = 0
        audio_select_index = 0
        
        if subtitle_tracks:
            for i, track in enumerate(subtitle_tracks):
                is_default = track.get("default", False)
                display_text = f"Track {track['index']}: {track['info']}"
                
                if is_default:
                    display_text += " [Default]"
                
                self.subtitle_combo.addItem(display_text, track['index'])
                
                if track['index'] == current_subtitle_index:
                    subtitle_select_index = i + 1  # +1 for "Auto select" option
                elif is_default and current_subtitle_index == -1:
                    subtitle_select_index = i + 1
        
        # add audiot kracks
        if audio_tracks:
            for i, track in enumerate(audio_tracks):
                is_default = track.get("default", False)
                display_text = f"Track {track['index']}: {track['info']}"
                
                if is_default:
                    display_text += " [Default]"
                
                self.audio_combo.addItem(display_text, track['index'])
                
                if track['index'] == current_audio_index:
                    audio_select_index = i + 1 # +1 for "Auto select" option
                elif is_default and current_audio_index == -1:
                    audio_select_index = i + 1
        
        self.subtitle_combo.blockSignals(False)
        self.audio_combo.blockSignals(False)
        
        # define selections
        self.subtitle_combo.setCurrentIndex(subtitle_select_index)
        self.audio_combo.setCurrentIndex(audio_select_index)


    def get_selected_tracks(self):
        """Get selected track indexes"""
        subtitle_index = self.subtitle_combo.currentData()
        audio_index = self.audio_combo.currentData()
        
        return subtitle_index, audio_index