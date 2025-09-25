# right_panel.py - Fixed auto-sizing and non-resizable right panel
import weakref
import gc
import time
import os
import tempfile
import uuid
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QGroupBox, 
                             QCheckBox, QScrollArea, QLabel, QMainWindow, QMessageBox, QHBoxLayout)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import QUrl, Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPalette
from config import load_config, save_config, get_config_value, set_config_value
from styles import get_icon_path, get_tool_urls


class ToolWindow(QMainWindow):
    def __init__(self, url, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"LostKit - {title}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Normal window behavior
        self.setWindowFlags(Qt.WindowType.Window)
        
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
        
        # Larger font for tool windows
        font = QFont("RuneScape UF", 14)
        if not font.exactMatch():
            font = QFont("runescape_uf", 14)
        self.setFont(font)
        
        # Set black background
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Load user-configured tool window size with per-tool memory
        self.tool_name = title
        self.load_window_geometry()
        
        self.setMinimumSize(600, 400)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # FIXED: Use process ID and unique ID to avoid conflicts between tool windows
        process_id = os.getpid()
        timestamp = int(time.time() * 1000)
        profile_name = f"ToolWindow_{title.replace(' ', '_')}_{process_id}_{timestamp}"
        
        try:
            profile = QWebEngineProfile(profile_name, self)
            
            # Use unique cache paths with PID to prevent conflicts between instances
            temp_dir = tempfile.gettempdir()
            cache_path = os.path.join(temp_dir, f"lostkit_ToolWindow_{title.replace(' ', '_')}_{process_id}_{timestamp}")
            storage_path = os.path.join(temp_dir, f"lostkit_ToolWindow_storage_{title.replace(' ', '_')}_{process_id}_{timestamp}")
            
            # Create directories
            os.makedirs(cache_path, exist_ok=True)
            os.makedirs(storage_path, exist_ok=True)
            
            profile.setCachePath(cache_path)
            profile.setPersistentStoragePath(storage_path)
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
            
            # Optimize web engine settings for performance
            settings = profile.settings()
            if get_config_value("resource_optimization", True):
                settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
                settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, False)
                settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, False)

            page = QWebEnginePage(profile, self)
            self.web_view = QWebEngineView()
            self.web_view.setPage(page)
            
            # Store references for cleanup
            self.profile_name = profile_name
            self.cache_path = cache_path
            self.storage_path = storage_path
            self._profile = profile  # Store profile reference to prevent premature deletion
            
        except Exception as e:
            print(f"Error creating web engine profile: {e}")
            self.web_view = QWebEngineView()
            self.profile_name = None
            self.cache_path = None
            self.storage_path = None
            self._profile = None
        
        layout.addWidget(self.web_view)
        
        print(f"Loading URL in window: {url}")
        self.web_view.setUrl(QUrl(url))
        
        # Setup cleanup timer for memory management
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self.perform_cleanup)
        cleanup_interval = get_config_value("cache_cleanup_interval", 300) * 1000
        self.cleanup_timer.start(cleanup_interval)

    def load_window_geometry(self):
        """Load window geometry specific to this tool"""
        try:
            # Load tool-specific geometry
            config_key = f"tool_window_geometry_{self.tool_name.replace(' ', '_')}"
            geom = get_config_value(config_key, None)
            
            if geom and isinstance(geom, list) and len(geom) == 4:
                x, y, w, h = [int(val) for val in geom]
                # Ensure window appears on screen
                x = max(0, min(x, 1920 - w))
                y = max(0, min(y, 1080 - h))
                self.setGeometry(x, y, w, h)
                print(f"Loaded geometry for {self.tool_name}: {w}x{h} at ({x},{y})")
            else:
                # Fall back to general tool window geometry
                general_geom = get_config_value("tool_window_geometry", [200, 200, 1000, 800])
                if isinstance(general_geom, list) and len(general_geom) == 4:
                    x, y, w, h = [int(val) for val in general_geom]
                    # Add slight offset for multiple windows
                    offset = hash(self.tool_name) % 10 * 25
                    x += offset
                    y += offset
                    x = max(0, min(x, 1920 - w))
                    y = max(0, min(y, 1080 - h))
                    self.setGeometry(x, y, w, h)
                else:
                    self.setGeometry(200, 200, 1000, 800)
        except (ValueError, TypeError) as e:
            print(f"Error setting tool window geometry: {e}, using defaults")
            self.setGeometry(200, 200, 1000, 800)

    def save_window_geometry(self):
        """Save window geometry specific to this tool"""
        try:
            geom = self.geometry()
            config_key = f"tool_window_geometry_{self.tool_name.replace(' ', '_')}"
            set_config_value(config_key, [geom.x(), geom.y(), geom.width(), geom.height()])
            print(f"Saved geometry for {self.tool_name}: {geom.width()}x{geom.height()} at ({geom.x()},{geom.y()})")
        except Exception as e:
            print(f"Error saving tool window geometry: {e}")

    def perform_cleanup(self):
        """Perform periodic cleanup to free resources"""
        try:
            if get_config_value("resource_optimization", True):
                gc.collect()
                if hasattr(self, 'web_view') and self.web_view:
                    try:
                        self.web_view.page().profile().clearAllVisitedLinks()
                    except:
                        pass
        except Exception as e:
            print(f"Error during tool window cleanup: {e}")

    def cleanup_cache_files(self):
        """Clean up cache files for this window"""
        try:
            if self.cache_path and os.path.exists(self.cache_path):
                import shutil
                shutil.rmtree(self.cache_path, ignore_errors=True)
                print(f"Cleaned up cache: {self.cache_path}")
        except Exception as e:
            print(f"Error cleaning cache: {e}")
        
        try:
            if self.storage_path and os.path.exists(self.storage_path):
                import shutil
                shutil.rmtree(self.storage_path, ignore_errors=True)
                print(f"Cleaned up storage: {self.storage_path}")
        except Exception as e:
            print(f"Error cleaning storage: {e}")

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Save geometry on resize (debounced via timer)
        if not hasattr(self, 'save_timer'):
            self.save_timer = QTimer(self)
            self.save_timer.setSingleShot(True)
            self.save_timer.timeout.connect(self.save_window_geometry)
        self.save_timer.start(500)  # Save after 500ms of no resize events

    def moveEvent(self, event):
        """Handle window move events"""
        super().moveEvent(event)
        # Save geometry on move (debounced via timer)
        if not hasattr(self, 'save_timer'):
            self.save_timer = QTimer(self)
            self.save_timer.setSingleShot(True)
            self.save_timer.timeout.connect(self.save_window_geometry)
        self.save_timer.start(500)  # Save after 500ms of no move events

    def closeEvent(self, event):
        # Save geometry before closing
        self.save_window_geometry()
        
        if hasattr(self, 'cleanup_timer'):
            self.cleanup_timer.stop()
        
        # FIX: Properly cleanup web engine components to avoid profile release errors
        if hasattr(self, 'web_view') and self.web_view:
            try:
                # Clear page before deleting
                self.web_view.setPage(None)
                # Delete the web view
                self.web_view.deleteLater()
            except Exception as e:
                print(f"Error cleaning up web view: {e}")
        
        self.cleanup_cache_files()
        gc.collect()
        event.accept()


class InGameBrowser(QWidget):
    closed = pyqtSignal()
    
    def __init__(self, url, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.url = url
        self.title = title
        
        font = QFont("RuneScape UF", 14)
        if not font.exactMatch():
            font = QFont("runescape_uf", 14)
        self.setFont(font)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # FIXED: Use process ID and timestamp to avoid conflicts
        process_id = os.getpid()
        timestamp = int(time.time() * 1000)
        profile_name = f"InGameBrowser_{title.replace(' ', '_')}_{process_id}_{timestamp}"
        
        try:
            profile = QWebEngineProfile(profile_name, self)
            
            # Use unique cache paths with PID to prevent conflicts
            temp_dir = tempfile.gettempdir()
            cache_path = os.path.join(temp_dir, f"lostkit_InGameBrowser_{title.replace(' ', '_')}_{process_id}_{timestamp}")
            storage_path = os.path.join(temp_dir, f"lostkit_InGameBrowser_storage_{title.replace(' ', '_')}_{process_id}_{timestamp}")
            
            # Create directories
            os.makedirs(cache_path, exist_ok=True)
            os.makedirs(storage_path, exist_ok=True)
                
            profile.setCachePath(cache_path)
            profile.setPersistentStoragePath(storage_path)
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
            
            # Optimize for in-game browser
            settings = profile.settings()
            if get_config_value("resource_optimization", True):
                settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)

            page = QWebEnginePage(profile, self)
            self.web_view = QWebEngineView()
            self.web_view.setPage(page)
            
            # Store for cleanup
            self.profile_name = profile_name
            self.cache_path = cache_path
            self.storage_path = storage_path
            self._profile = profile  # Store profile reference
            
        except Exception as e:
            print(f"Error creating in-game browser profile: {e}")
            self.web_view = QWebEngineView()
            self.profile_name = None
            self.cache_path = None
            self.storage_path = None
            self._profile = None
        
        layout.addWidget(self.web_view)
        
        print(f"Loading URL in tab: {url}")
        self.web_view.setUrl(QUrl(url))

    def cleanup_cache_files(self):
        """Clean up cache files for this browser"""
        try:
            if self.cache_path and os.path.exists(self.cache_path):
                import shutil
                shutil.rmtree(self.cache_path, ignore_errors=True)
        except:
            pass
        
        try:
            if self.storage_path and os.path.exists(self.storage_path):
                import shutil
                shutil.rmtree(self.storage_path, ignore_errors=True)
        except:
            pass

    def closeEvent(self, event):
        # FIX: Properly cleanup web engine components
        if hasattr(self, 'web_view') and self.web_view:
            try:
                # Clear page before deleting
                self.web_view.setPage(None)
                # Delete the web view
                self.web_view.deleteLater()
            except Exception as e:
                print(f"Error cleaning up web view: {e}")
        
        self.cleanup_cache_files()
        self.closed.emit()
        event.accept()


class RightToolsPanel(QWidget):
    browser_requested = pyqtSignal(str, str)
    chat_toggle_requested = pyqtSignal()
    panel_collapse_requested = pyqtSignal(bool)  # Signal when panel should collapse/expand
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config = load_config()
        self.tool_windows = weakref.WeakValueDictionary()
        self.window_count = 0
        
        # Collapse state
        self.collapsed = get_config_value("right_panel_collapsed", False)
        self.saved_width = self.config.get("right_panel_width", 220)  # Increased default width
        
        font = QFont("RuneScape UF", 13)
        if not font.exactMatch():
            font = QFont("runescape_uf", 13)
        self.setFont(font)
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Calculate optimal panel width
        self.optimal_width = self.calculate_optimal_width()
        
        # Set fixed width based on collapse state - NO RESIZING ALLOWED
        if self.collapsed:
            self.setFixedWidth(25)
        else:
            self.setFixedWidth(self.optimal_width)
        
        self.setup_ui()
        
    def calculate_optimal_width(self):
        """Calculate the optimal width to fit all buttons and scrollbar with proper gaps"""
        # Base width for button content
        base_button_width = 160  # Button text area
        
        # Additional spacing needed:
        # - Left/right margins: 8px each = 16px
        # - Scroll layout margins: left 3px + right 20px = 23px (extra for scrollbar gap)
        # - Border padding: 4px each side = 8px
        # - Group box padding: 5px each side = 10px
        # - Scrollbar width: 16px
        # - Safety margin: 8px
        
        total_width = base_button_width + 16 + 23 + 8 + 10 + 16 + 8
        return total_width  # Should be around 240-250px
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)  # Consistent margins
        main_layout.setSpacing(6)
        
        if self.collapsed:
            # When collapsed, show only the expand button centered
            self.setup_collapsed_ui(main_layout)
        else:
            # When expanded, show all content without collapse button
            self.setup_expanded_ui(main_layout)

    def setup_collapsed_ui(self, main_layout):
        """Setup UI for collapsed state - only expand button on right side middle"""
        # Clear existing layout
        self.clear_layout(main_layout)
        
        # Add stretch to center the button vertically
        main_layout.addStretch()
        
        # Create expand button container - positioned on right side
        expand_container = QWidget()
        expand_container.setFixedHeight(40)
        expand_layout = QHBoxLayout(expand_container)
        expand_layout.setContentsMargins(0, 0, 2, 0)  # Small margin from right edge
        
        # Expand button positioned on the right side
        self.expand_btn = QPushButton("▶")
        self.expand_btn.setFixedSize(18, 35)  # Slightly wider and taller for better visibility
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b4a4a;
                border: 1px solid #2a2a2a;
                border-radius: 2px;
                color: #f5e6c0;
                font-weight: bold;
                font-size: 10px;
                margin: 0px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #a55a5a;
                border-color: #8b4a4a;
            }
            QPushButton:pressed {
                background-color: #8b4a4a;
                border: 1px inset #2a2a2a;
            }
        """)
        self.expand_btn.clicked.connect(self.expand_panel)
        
        # Position button on the right side
        expand_layout.addStretch()
        expand_layout.addWidget(self.expand_btn)
        
        main_layout.addWidget(expand_container)
        main_layout.addStretch()  # Add stretch after button too

    def setup_expanded_ui(self, main_layout):
        """Setup UI for expanded state - no collapse button"""
        # Clear existing layout
        self.clear_layout(main_layout)
        
        # Settings panel
        settings_group = QGroupBox("Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                background: #000000;
                color: #f5e6c0;
                font-weight: bold;
                font-size: 15px;
                border: 2px solid #2a2a2a;
                border-radius: 0px;
                margin: 3px 0px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                font-size: 15px;
                background-color: #2a2a2a;
            }
        """)
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(8, 8, 8, 8)  # Consistent padding
        settings_layout.setSpacing(5)
        
        # External window toggle
        self.external_cb = QCheckBox("Open tools externally")
        self.external_cb.setChecked(self.config.get("open_external", True))
        self.external_cb.stateChanged.connect(self.toggle_external_mode)
        self.external_cb.setStyleSheet("""
            QCheckBox {
                color: #f5e6c0;
                spacing: 8px;
                font-size: 14px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #4a4a4a;
                border: 2px solid #2a2a2a;
                border-radius: 0px;
            }
            QCheckBox::indicator:checked {
                background-color: #8b4a4a;
                border: 2px solid #2a2a2a;
                border-radius: 0px;
            }
        """)
        settings_layout.addWidget(self.external_cb)
        
        settings_group.setLayout(settings_layout)
        settings_group.setMaximumHeight(70)
        main_layout.addWidget(settings_group)
        
        # IRC Chat toggle button
        self.chat_toggle_btn = QPushButton("IRC Chat")
        self.chat_toggle_btn.setFixedHeight(35)
        self.chat_toggle_btn.clicked.connect(self.toggle_chat)
        
        # Set initial button style
        is_visible = self.config.get("chat_panel_visible", False)
        self.update_chat_button_style(is_visible)
        
        main_layout.addWidget(self.chat_toggle_btn)
        
        # Tools panel - This should expand to fill available space
        tools_group = QGroupBox("Tools")
        tools_group.setStyleSheet("""
            QGroupBox {
                background: #000000;
                color: #f5e6c0;
                font-weight: bold;
                font-size: 15px;
                border: 2px solid #2a2a2a;
                border-radius: 0px;
                margin: 3px 0px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                font-size: 15px;
                background-color: #2a2a2a;
            }
        """)
        tools_layout = QVBoxLayout()
        tools_layout.setContentsMargins(5, 5, 5, 5)  # Consistent padding
        tools_layout.setSpacing(4)
        
        # Create scroll area with proper sizing for buttons and scrollbar
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: #000000;
                border: 1px solid #2a2a2a;
                margin: 0px;
                padding: 0px;
            }
            QScrollArea > QWidget > QWidget {
                background: #000000;
                margin: 0px;
                padding: 0px;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 14px;
                margin: 0px;
                border: 1px solid #2a2a2a;
            }
            QScrollBar::handle:vertical {
                background: #8b4a4a;
                min-height: 20px;
                border-radius: 0px;
                border: 1px solid #2a2a2a;
            }
            QScrollBar::handle:vertical:hover {
                background: #a55a5a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background: #000000; margin: 0px; padding: 0px;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(4)
        # Proper margins: left margin normal, right margin larger to leave gap from scrollbar
        self.scroll_layout.setContentsMargins(5, 5, 20, 5)  # Increased right margin for scrollbar gap
        
        # Get tool URLs and create buttons
        self.tool_buttons = []
        tool_urls = get_tool_urls()
        for tool_name, url in tool_urls.items():
            btn = self.create_tool_button(tool_name, url)
            self.scroll_layout.addWidget(btn)
            self.tool_buttons.append(btn)
        
        self.scroll_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_widget)
        tools_layout.addWidget(self.scroll_area)
        
        tools_group.setLayout(tools_layout)
        main_layout.addWidget(tools_group, 1)  # Add stretch factor to expand

    def clear_layout(self, layout):
        """Clear all widgets from a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def expand_panel(self):
        """Expand the panel from collapsed state"""
        self.collapsed = False
        set_config_value("right_panel_collapsed", False)
        
        # Set to optimal width for expanded state
        self.setFixedWidth(self.optimal_width)
        
        # Rebuild UI for expanded state
        main_layout = self.layout()
        self.setup_expanded_ui(main_layout)
        
        # Emit signal to parent to handle layout changes
        self.panel_collapse_requested.emit(False)

    def set_collapsed_state(self, collapsed):
        """Set collapse state and rebuild UI accordingly"""
        if self.collapsed != collapsed:
            self.collapsed = collapsed
            set_config_value("right_panel_collapsed", collapsed)
            
            # Set appropriate width
            if collapsed:
                self.setFixedWidth(25)
            else:
                self.setFixedWidth(self.optimal_width)
            
            # Rebuild UI based on new state
            main_layout = self.layout()
            if collapsed:
                self.setup_collapsed_ui(main_layout)
            else:
                self.setup_expanded_ui(main_layout)

    def update_chat_button_style(self, is_visible):
        """Update chat button style based on visibility"""
        if self.collapsed:
            return  # No chat button when collapsed
            
        if is_visible:
            self.chat_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a6a4a;
                    border: 1px solid #2a2a2a;
                    border-radius: 0px;
                    padding: 8px 12px;
                    color: #f5e6c0;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #5a7a5a;
                    border-color: #4a6a4a;
                }
                QPushButton:pressed {
                    background-color: #4a6a4a;
                    border: 1px inset #2a2a2a;
                }
            """)
        else:
            self.chat_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #8b4a4a;
                    border: 1px solid #2a2a2a;
                    border-radius: 0px;
                    padding: 8px 12px;
                    color: #f5e6c0;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #a55a5a;
                    border-color: #8b4a4a;
                }
                QPushButton:pressed {
                    background-color: #8b4a4a;
                    border: 1px inset #2a2a2a;
                }
            """)

    def toggle_chat(self):
        """Emit signal to toggle chat panel"""
        self.chat_toggle_requested.emit()

    def create_tool_button(self, name, url):
        """Create a tool button with optimal sizing"""
        icon_path = get_icon_path(name)
        
        display_name = name
        if len(name) > 12:
            if name == "Clue Coordinates":
                display_name = "Coordinates"
            elif name == "Clue Scroll Help":
                display_name = "Clue Help"
            elif name == "Market Prices":
                display_name = "Prices"
        
        if os.path.exists(icon_path) and icon_path.endswith('.png'):
            btn = QPushButton()
            icon = QIcon(icon_path)
            btn.setIcon(icon)
            btn.setIconSize(QSize(26, 26))  # Bigger icon size
            btn.setText(display_name)
        else:
            btn = QPushButton(f"{icon_path} {display_name}")
        
        # Store display name for later restoration
        btn.setProperty("display_name", display_name)
        btn.setProperty("icon_path", icon_path)
        
        # Set button style with proper sizing to fit in the calculated width
        btn.setStyleSheet(self.get_button_style())
        btn.setFixedHeight(42)  # Fixed height for all buttons
        btn.setMinimumWidth(160)  # Minimum width to ensure text fits
        btn.setMaximumWidth(200)  # Maximum width to fit in panel
        
        btn.clicked.connect(lambda checked, n=name, u=url: self.open_tool(n, u))
        return btn

    def get_button_style(self):
        """Get button style optimized for the panel width"""
        button_image_path = "button.jpg"
        base_style = """
            QPushButton {
                border: 2px solid #2a2a2a;
                border-radius: 0px;
                padding: 6px 10px;
                color: #f5e6c0;
                font-weight: bold;
                font-size: 13px;
                min-height: 38px;
                max-height: 42px;
                text-align: left;
        """
        
        if os.path.exists(button_image_path):
            base_style += f"background: url({button_image_path}) center center stretch;"
        else:
            base_style += "background-color: #8b4a4a;"
        
        base_style += """
            }
            QPushButton:hover {
                border-color: #8b4a4a;
                background-color: rgba(139, 74, 74, 120);
            }
            QPushButton:pressed {
                border: 2px inset #2a2a2a;
                background-color: rgba(139, 74, 74, 150);
            }
        """
        
        return base_style
        
    def open_tool(self, name, url):
        """Open a tool either in external window or in-game browser"""
        print(f"Opening tool: {name} -> {url}")
        
        max_windows = get_config_value("max_tool_windows", 10)
        
        if self.config.get("open_external", True):
            self.cleanup_dead_windows()
            
            if len(self.tool_windows) >= max_windows:
                QMessageBox.warning(
                    self, 
                    "Window Limit Reached",
                    f"Maximum number of tool windows ({max_windows}) reached.\nPlease close some windows before opening new ones.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            window_key = f"{name}_{self.window_count}"
            
            try:
                tool_window = ToolWindow(url, name, self)
                tool_window.show()
                
                self.tool_windows[window_key] = tool_window
                self.window_count += 1
                
                print(f"Opened {name} in external window ({len(self.tool_windows)}/{max_windows})")
                
            except Exception as e:
                print(f"Error creating tool window: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to open {name}:\n{str(e)}",
                    QMessageBox.StandardButton.Ok
                )
        else:
            print(f"Emitting browser_requested signal for {name}")
            self.browser_requested.emit(url, name)

    def cleanup_dead_windows(self):
        """Remove references to closed windows"""
        dead_keys = []
        for key, window_ref in list(self.tool_windows.items()):
            try:
                if not hasattr(window_ref, 'isVisible') or not window_ref.isVisible():
                    dead_keys.append(key)
            except RuntimeError:
                dead_keys.append(key)
        
        for key in dead_keys:
            if key in self.tool_windows:
                del self.tool_windows[key]
        
        if dead_keys:
            print(f"Cleaned up {len(dead_keys)} dead window references")
            
    def toggle_external_mode(self, state):
        """Toggle between external windows and in-game browser"""
        external = state == Qt.CheckState.Checked.value
        self.config["open_external"] = external
        save_config(self.config)
        print(f"External mode set to: {external}")
        
        if not external:
            self.close_all_tool_windows()

    def close_all_tool_windows(self):
        """Close all external tool windows"""
        windows_to_close = []
        
        for window_ref in list(self.tool_windows.values()):
            try:
                if hasattr(window_ref, 'isVisible') and window_ref.isVisible():
                    windows_to_close.append(window_ref)
            except RuntimeError:
                pass
        
        for window in windows_to_close:
            try:
                window.close()
            except RuntimeError:
                pass
        
        self.tool_windows.clear()
        self.window_count = 0
        print("Closed all external tool windows")

    def closeEvent(self, event):
        """Clean up tool windows when panel is closed"""
        self.close_all_tool_windows()
        gc.collect()
        event.accept()