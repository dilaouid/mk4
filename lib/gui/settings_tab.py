"""
Settings tab for mk4 GUI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox,
    QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from lib.gui.components import StyledButton
from lib.config import config_manager, DEFAULT_CONFIG

class SettingsTab(QWidget):
    """
    Settings tab with configuration options
    """
    settingsChanged = pyqtSignal()
    themeChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup main layout
        main_layout = QVBoxLayout(self)
        
        # FFMPEG Settings
        ffmpeg_group = QGroupBox("FFMPEG Settings")
        ffmpeg_layout = QFormLayout()
        
        # Encoder selection
        self.encoder_combo = QComboBox()
        encoder_options = [
            "libx264", "libx265", "h264_nvenc", "hevc_nvenc", 
            "h264_qsv", "hevc_qsv", "libvpx-vp9"
        ]
        for option in encoder_options:
            self.encoder_combo.addItem(option)
        
        current_encoder = config_manager.config.get('FFMPEG', 'ENCODER', fallback='libx264')
        index = encoder_options.index(current_encoder) if current_encoder in encoder_options else 0
        self.encoder_combo.setCurrentIndex(index)
        
        ffmpeg_layout.addRow("Video Encoder:", self.encoder_combo)
        
        # CRF (quality) setting
        self.crf_spinbox = QSpinBox()
        self.crf_spinbox.setRange(0, 51)
        self.crf_spinbox.setValue(int(config_manager.config.get('FFMPEG', 'CRF', fallback='23')))
        self.crf_spinbox.setToolTip("0 = lossless, 51 = worst quality")
        ffmpeg_layout.addRow("CRF (Quality):", self.crf_spinbox)
        
        ffmpeg_group.setLayout(ffmpeg_layout)
        main_layout.addWidget(ffmpeg_group)
        
        # Font Settings
        font_group = QGroupBox("Subtitle Font Settings")
        font_layout = QFormLayout()
        
        # Font name
        self.font_name = QLineEdit()
        self.font_name.setText(config_manager.config.get('FONT', 'Name', fallback='Arial'))
        font_layout.addRow("Font Name:", self.font_name)
        
        # Font size
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 48)
        self.font_size.setValue(int(config_manager.config.get('FONT', 'Size', fallback='24')))
        font_layout.addRow("Font Size:", self.font_size)
        
        font_group.setLayout(font_layout)
        main_layout.addWidget(font_group)
        
        # UI Settings
        ui_group = QGroupBox("UI Settings")
        ui_layout = QFormLayout()
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light")
        self.theme_combo.addItem("Dark")
        
        current_theme = config_manager.config.get('GUI', 'Theme', fallback='light').lower()
        if current_theme == 'dark':
            self.theme_combo.setCurrentIndex(1)
        else:
            self.theme_combo.setCurrentIndex(0)
        
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        ui_layout.addRow("Theme:", self.theme_combo)
        
        ui_group.setLayout(ui_layout)
        main_layout.addWidget(ui_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = StyledButton("Save Settings", "primary")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.reset_button = StyledButton("Reset to Defaults", "secondary")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        main_layout.addLayout(button_layout)
        
        # Add a spacer
        main_layout.addStretch()
    
    def save_settings(self):
        """Save settings to config file"""
        # Update FFMPEG settings
        config_manager.update_config('FFMPEG', 'ENCODER', self.encoder_combo.currentText())
        config_manager.update_config('FFMPEG', 'CRF', str(self.crf_spinbox.value()))
        
        # Update Font settings
        config_manager.update_config('FONT', 'Name', self.font_name.text())
        config_manager.update_config('FONT', 'Size', str(self.font_size.value()))
        
        # Update GUI settings
        theme = 'dark' if self.theme_combo.currentIndex() == 1 else 'light'
        config_manager.update_config('GUI', 'Theme', theme)
        
        # Reload config
        config_manager.load_config()
        
        # Emit signal to notify about settings change
        self.settingsChanged.emit()
        
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")

    def reset_to_defaults(self):
        """Reset settings to default values"""
        # Ask for confirmation
        result = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if result == QMessageBox.Yes:
            # Reset FFMPEG settings
            self.encoder_combo.setCurrentText(DEFAULT_CONFIG['FFMPEG']['ENCODER'])
            self.crf_spinbox.setValue(int(DEFAULT_CONFIG['FFMPEG']['CRF']))
            
            # Reset Font settings
            self.font_name.setText(DEFAULT_CONFIG['FONT']['Name'])
            self.font_size.setValue(int(DEFAULT_CONFIG['FONT']['Size']))
            
            # Reset GUI settings
            self.theme_combo.setCurrentIndex(0)  # Light theme
    
    def on_theme_changed(self, index):
        """Handle theme change"""
        theme = 'dark' if index == 1 else 'light'
        self.themeChanged.emit(theme)