"""
Main application class for mk4 GUI
"""
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QStatusBar, QMessageBox,
    QDesktopWidget, QAction, 
)
from PyQt5.QtGui import QKeySequence, QIcon

from lib.gui.conversion_tab import ConversionTab
from lib.gui.settings_tab import SettingsTab
from lib.gui.components import Theme
from lib.gui.styles import WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
from lib.config import config_manager
from lib.utils import is_ffmpeg_installed, resource_path

class Mk4GuiApp(QMainWindow):
    """
    Main application window for mk4 GUI
    """
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("mio_JEc_1.ico")))

        
        # Check if ffmpeg is installed
        if not is_ffmpeg_installed():
            QMessageBox.critical(
                self, "FFmpeg Not Found",
                "FFmpeg is required but not found in your system PATH.\n"
                "Please install FFmpeg and restart the application."
            )
            sys.exit(1)
        
        # Setup UI
        self.setWindowTitle("mk4 - MKV to MP4 Converter")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        # Center the window
        self._center_window()
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.conversion_tab = ConversionTab()
        self.settings_tab = SettingsTab()
        
        # Add tabs
        self.tabs.addTab(self.conversion_tab, "Conversion")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Set central widget
        self.setCentralWidget(self.tabs)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create menu bar
        self._create_menus()
        
        # Connect signals
        self.settings_tab.settingsChanged.connect(self._on_settings_changed)
        self.settings_tab.themeChanged.connect(self._on_theme_changed)
        
        # Apply theme from settings
        self._apply_theme()
    
    def _create_menus(self):
        """Create application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Add MKV file action
        add_file_action = QAction("&Add MKV File", self)
        add_file_action.setShortcut(QKeySequence.Open)
        add_file_action.triggered.connect(self._add_mkv_file)
        file_menu.addAction(add_file_action)
        
        # Add directory action
        add_dir_action = QAction("Add Director&y", self)
        add_dir_action.triggered.connect(self._add_directory)
        file_menu.addAction(add_dir_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _center_window(self):
        """Center the window on the screen"""
        frame_geometry = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
    
    def _add_mkv_file(self):
        """Add MKV file from file dialog"""
        self.tabs.setCurrentIndex(0)  # Switch to conversion tab
        self.conversion_tab.file_list.add_files()
    
    def _add_directory(self):
        """Add directory with MKV files"""
        self.tabs.setCurrentIndex(0)  # Switch to conversion tab
        self.conversion_tab.file_list.add_directory()
    
    def _start_conversion(self):
        """Start conversion process"""
        self.tabs.setCurrentIndex(0)  # Switch to conversion tab
        self.conversion_tab.start_conversion()
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About mk4",
            """
            <h1>mk4</h1>
            <p><em>Convert your MKV videos into MP4 effortlessly</em></p>
            <p><strong>mk4</strong> is a tool to convert MKV videos into MP4, embedding subtitles into the output file.</p>
            <p>You can customize the subtitle font and size in the settings tab.</p>
            <p><strong>Authors:</strong> <a href='https://github.com/dilaouid/'>dilaouid</a>, <a href='https://github.com/Dastan21'>Dastan21</a></p>
            <p><strong>License:</strong> MIT</p>
            <p><strong>Version:</strong> 1.1.0</p>
            <p><strong>Source Code:</strong> <a href='https://github.com/dilaouid/mk4'>GitHub</a></p>
            <p><strong>Dependencies:</strong> PyQt5, ffmpeg (must be installed and in system PATH)</p>
            """
        )

    def _on_settings_changed(self):
        """Handle settings changed"""
        self.status_bar.showMessage("Settings saved", 3000)
    
    def _on_theme_changed(self, theme):
        """Handle theme changed"""
        self._apply_theme(theme)
    
    def _apply_theme(self, theme=None):
        """Apply theme to application"""
        if theme is None:
            theme = config_manager.config.get('GUI', 'Theme', fallback='light').lower()
        
        Theme.apply_theme(QApplication.instance(), self, theme)
        self.status_bar.showMessage(f"Theme changed to {theme}", 3000)

def run_gui():
    """
    Run the mk4 GUI application
    """
    app = QApplication(sys.argv)
    app.setApplicationName("mk4")
    app.setApplicationDisplayName("mk4 - MKV to MP4 Converter")
    app.setWindowIcon(QIcon(resource_path("mio_JEc_1.ico")))

    
    window = Mk4GuiApp()
    window.show()
    
    sys.exit(app.exec_())