# main_window.py - Improved collapse handling and window state persistence
import gc
import time
import uuid
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QSplitter, 
                             QVBoxLayout, QTabWidget, QPushButton, QLabel)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QBrush, QColor
from game_view import GameViewWidget
from right_panel import RightToolsPanel, InGameBrowser
from chat_panel import ChatPanel
import config
from styles import MAIN_STYLESHEET, get_icon_path
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Generate unique instance ID for multiple window support
        self.instance_id = uuid.uuid4().hex[:8]
        
        # Set window title with instance ID for debugging
        self.setWindowTitle(f"LostKit")
        
        # Set window icon if it exists
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
        
        # Larger font
        font = QFont("RuneScape UF", 14)
        if not font.exactMatch():
            font = QFont("runescape_uf", 14)
        self.setFont(font)
        
        # Load config with instance-specific handling
        self.config = config.load_config()
        
        # Add instance tracking to prevent conflicts
        self.is_closing = False
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.save_window_state_debounced)
        
        # Set window geometry from config with improved defaults
        self.setup_window_geometry()
        
        # Set black background
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Apply Windows 98 styled stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)
        
        # Set larger minimum size
        self.setMinimumSize(1000, 700)

        # Create central widget and main layout
        central_widget = QWidget()
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(8)

        # Create main horizontal splitter (left: game+chat, right: tools)
        self.main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create left section: game view with tabs and chat panel
        self.create_left_section()
        
        # Create right section: tools panel
        self.create_right_section()

        self.setCentralWidget(central_widget)
        
        # Track browser tabs for cleanup
        self.browser_tabs = {}
        
        # Setup resource management timer
        self.setup_resource_management()

    def setup_window_geometry(self):
        """Setup window geometry with multiple instance support"""
        try:
            if self.config.get("window_geometry"):
                geom = self.config["window_geometry"]
                if isinstance(geom, list) and len(geom) == 4:
                    x, y, w, h = [int(val) for val in geom]
                    
                    # Offset subsequent instances to avoid complete overlap
                    offset = hash(self.instance_id) % 5 * 30
                    x += offset
                    y += offset
                    
                    # Ensure window appears on screen
                    x = max(0, min(x, 1920 - w))
                    y = max(0, min(y, 1080 - h))
                    
                    self.setGeometry(x, y, w, h)
                else:
                    self.setGeometry(100, 100, 1440, 900)
            else:
                # Default geometry with slight offset for multiple instances
                offset = hash(self.instance_id) % 5 * 30
                self.setGeometry(100 + offset, 100 + offset, 1440, 900)
        except (ValueError, TypeError) as e:
            print(f"Error setting window geometry: {e}, using defaults")
            offset = hash(self.instance_id) % 5 * 30
            self.setGeometry(100 + offset, 100 + offset, 1440, 900)

    def setup_resource_management(self):
        """Setup periodic resource management"""
        if config.get_config_value("resource_optimization", True):
            self.resource_timer = QTimer(self)
            self.resource_timer.timeout.connect(self.perform_resource_cleanup)
            # Run cleanup every 5 minutes
            self.resource_timer.start(300000)

    def perform_resource_cleanup(self):
        """Perform periodic resource cleanup"""
        try:
            if self.is_closing:
                return
                
            # Force garbage collection
            gc.collect()
            
            # Clean up dead browser tab references
            dead_tabs = []
            for tab_index, browser in list(self.browser_tabs.items()):
                try:
                    if not hasattr(browser, 'isVisible') or not browser.parent():
                        dead_tabs.append(tab_index)
                except RuntimeError:
                    dead_tabs.append(tab_index)
            
            for tab_index in dead_tabs:
                if tab_index in self.browser_tabs:
                    del self.browser_tabs[tab_index]
            
            if dead_tabs:
                print(f"Cleaned up {len(dead_tabs)} dead browser tab references")
                
        except Exception as e:
            print(f"Error during resource cleanup: {e}")

    def create_left_section(self):
        """Create the left section with game view and chat panel"""
        # Left widget container
        self.left_widget = QWidget()
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # Create vertical splitter for game view and chat
        self.left_vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Create game section
        self.create_game_section()
        
        # Create chat panel with instance ID
        self.chat_panel = ChatPanel()
        self.chat_panel.instance_id = self.instance_id
        
        # Add to vertical splitter
        self.left_vertical_splitter.addWidget(self.game_widget)
        self.left_vertical_splitter.addWidget(self.chat_panel)
        
        # Set initial sizes - game gets most space, chat gets smaller portion
        game_height = 600
        chat_height = self.config.get("chat_panel_height", 200)
        self.left_vertical_splitter.setSizes([game_height, chat_height])
        
        # Connect splitter moved signal to save config
        self.left_vertical_splitter.splitterMoved.connect(self.on_vertical_splitter_moved)
        
        # Hide chat panel initially if configured
        if not self.config.get("chat_panel_visible", False):
            self.chat_panel.hide()
        
        left_layout.addWidget(self.left_vertical_splitter)
        
        # Add left section to horizontal splitter
        self.main_horizontal_splitter.addWidget(self.left_widget)

    def create_game_section(self):
        """Create the main game section with tabs"""
        # Game view with tabs
        self.game_widget = QWidget()
        game_layout = QVBoxLayout(self.game_widget)
        game_layout.setContentsMargins(0, 0, 0, 0)
        game_layout.setSpacing(5)
        
        # Tab widget for game and tools
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_browser_tab)
        
        # Updated tab styling with slightly smaller height but larger font
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #2a2a2a;
                border-radius: 0px;
            }
            QTabBar::tab {
                background-color: #4a4a4a;
                border: 2px solid #2a2a2a;
                border-radius: 0px;
                padding: 5px 14px;
                margin: 1px;
                min-width: 80px;
                max-height: 30px;
                color: #f5e6c0;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                border-color: #2a2a2a;
                color: #f5e6c0;
            }
            QTabBar::tab:hover:!selected {
                background-color: #505050;
                border-color: #8b4a4a;
            }
        """)
        
        # Game view tab with proper icon and updated URL - Server list
        game_url = f"https://2004.lostcity.rs/detail"
        self.game_view = GameViewWidget(game_url)
        self.game_view.instance_id = self.instance_id
        self.game_view.setZoomFactor(self.config.get("zoom_factor", 1.0))
        
        # Get Lost City icon
        lost_city_icon_path = get_icon_path("Lost City")
        tab_index = self.tab_widget.addTab(self.game_view, "Lost City")
        
        # Set icon if PNG exists
        if os.path.exists(lost_city_icon_path) and lost_city_icon_path.endswith('.png'):
            icon = QIcon(lost_city_icon_path)
            self.tab_widget.setTabIcon(tab_index, icon)
        
        # Make game tab unclosable
        self.tab_widget.tabBar().setTabButton(0, self.tab_widget.tabBar().ButtonPosition.RightSide, None)
        
        game_layout.addWidget(self.tab_widget)

    def create_right_section(self):
        """Create the right tools panel"""
        self.tools_panel = RightToolsPanel()
        self.tools_panel.browser_requested.connect(self.open_browser_tab)
        self.tools_panel.chat_toggle_requested.connect(self.toggle_chat_panel)
        self.tools_panel.panel_collapse_requested.connect(self.on_panel_collapse_requested)
        self.main_horizontal_splitter.addWidget(self.tools_panel)

        # Set initial horizontal splitter sizes based on collapse state
        if self.tools_panel.collapsed:
            # Panel is collapsed - set to minimal width
            total_width = 1440  # Default window width
            left_width = total_width - 25  # 25px for collapsed panel
            self.main_horizontal_splitter.setSizes([left_width, 25])
        else:
            # Panel is expanded - set to normal width
            panel_width = 200
            total_width = 1440  # Default window width
            left_width = total_width - panel_width
            self.main_horizontal_splitter.setSizes([left_width, panel_width])
        
        # Connect splitter moved signal to handle collapse/expand via dragging
        self.main_horizontal_splitter.splitterMoved.connect(self.on_horizontal_splitter_moved)

        # Add horizontal splitter to main layout
        self.main_layout.addWidget(self.main_horizontal_splitter)

    def on_panel_collapse_requested(self, expanded):
        """Handle panel expand request from the tools panel"""
        if expanded:
            # Panel wants to expand
            panel_width = 200
            total_width = self.main_horizontal_splitter.width()
            left_width = total_width - panel_width
            self.main_horizontal_splitter.setSizes([left_width, panel_width])

    def toggle_chat_panel(self):
        """Toggle visibility of chat panel"""
        if self.chat_panel.isVisible():
            self.chat_panel.hide()
            self.config["chat_panel_visible"] = False
        else:
            self.chat_panel.show()
            self.config["chat_panel_visible"] = True
        
        # Update the right panel button color
        self.tools_panel.update_chat_button_style(self.config["chat_panel_visible"])
        
        config.save_config(self.config)

    def open_browser_tab(self, url, title):
        """Open a tool in a new tab within the main window"""
        print(f"Opening browser tab: {title} - {url}")
        
        # Get icon for this tool
        icon_path = get_icon_path(title)
        
        # Create tab title based on whether we have PNG icon or emoji
        if os.path.exists(icon_path) and icon_path.endswith('.png'):
            tab_title = title
        else:
            tab_title = f"{icon_path} {title}"
        
        # Check if tab already exists
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_title or self.tab_widget.tabText(i) == f"{icon_path} {title}":
                self.tab_widget.setCurrentIndex(i)
                return
        
        try:
            # Add instance parameter to URL to avoid conflicts
            if '?' in url:
                unique_url = f"{url}&instance={self.instance_id}"
            else:
                unique_url = f"{url}?instance={self.instance_id}"
                
            # Create new browser tab
            browser = InGameBrowser(unique_url, title)
            browser.closed.connect(lambda: self.close_browser_by_widget(browser))
            
            # Add tab with proper icon handling
            tab_index = self.tab_widget.addTab(browser, tab_title)
            
            # Set PNG icon if available
            if os.path.exists(icon_path) and icon_path.endswith('.png'):
                icon = QIcon(icon_path)
                self.tab_widget.setTabIcon(tab_index, icon)
            
            self.tab_widget.setCurrentIndex(tab_index)
            
            # Store reference for cleanup
            self.browser_tabs[tab_index] = browser
            
        except Exception as e:
            print(f"Error creating browser tab: {e}")

    def close_browser_tab(self, index):
        """Close a browser tab with proper cleanup"""
        if index == 0:  # Don't close the main game tab
            return
            
        widget = self.tab_widget.widget(index)
        if widget:
            # Clean up browser cache if it has cleanup method
            if hasattr(widget, 'cleanup_cache_files'):
                try:
                    widget.cleanup_cache_files()
                except Exception as e:
                    print(f"Error cleaning up browser tab cache: {e}")
            
            # Remove from tracking
            if index in self.browser_tabs:
                del self.browser_tabs[index]
            
            # Remove tab
            self.tab_widget.removeTab(index)
            
            # Delete widget to free resources
            widget.deleteLater()
            
            # Force garbage collection
            if config.get_config_value("resource_optimization", True):
                gc.collect()

    def close_browser_by_widget(self, browser_widget):
        """Close browser tab by widget reference"""
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == browser_widget:
                self.close_browser_tab(i)
                break

    def on_vertical_splitter_moved(self, pos, index):
        """Save vertical splitter position to config with debouncing"""
        if not self.is_closing:
            # Use timer to debounce rapid splitter movements  
            self.resize_timer.start(500)  # Save after 500ms of no movement

    def moveEvent(self, event):
        """Handle window move with debounced saving"""
        super().moveEvent(event)
        if not self.is_closing:
            # Debounce move events
            self.resize_timer.start(500)

    def on_horizontal_splitter_moved(self, pos, index):
        """Handle horizontal splitter movement to detect collapse/expand via dragging"""
        if not self.is_closing:
            sizes = self.main_horizontal_splitter.sizes()
            if len(sizes) >= 2:
                right_width = sizes[1]
                
                # If panel is dragged to very small width (< 50px), collapse it
                if right_width < 50:
                    self.tools_panel.set_collapsed_state(True)
                    # Force minimal width
                    total_width = self.main_horizontal_splitter.width()
                    self.main_horizontal_splitter.setSizes([total_width - 25, 25])
                elif right_width >= 50 and self.tools_panel.collapsed:
                    # Panel is being expanded from collapsed state
                    self.tools_panel.set_collapsed_state(False)
                    # Set to normal width
                    total_width = self.main_horizontal_splitter.width()
                    self.main_horizontal_splitter.setSizes([total_width - 200, 200])
                
                # Use timer to debounce rapid splitter movements
                self.resize_timer.start(500)

    def save_window_state_debounced(self):
        """Save window state after debouncing timer expires"""
        if self.is_closing:
            return
            
        try:
            # Save window geometry
            geom = self.geometry()
            self.config["window_geometry"] = [geom.x(), geom.y(), geom.width(), geom.height()]
            
            # Save vertical splitter sizes  
            v_sizes = self.left_vertical_splitter.sizes()
            if len(v_sizes) >= 2:
                self.config["chat_panel_height"] = v_sizes[1]
            
            config.save_config(self.config)
            print(f"Saved window state: {geom.width()}x{geom.height()}")
        except Exception as e:
            print(f"Error saving window state: {e}")

    def resizeEvent(self, event):
        """Handle window resize with debounced saving"""
        super().resizeEvent(event)
        if not self.is_closing:
            # Maintain panel widths on window resize
            if self.tools_panel.collapsed:
                # Keep collapsed
                total_width = self.width()
                left_width = total_width - 25
                self.main_horizontal_splitter.setSizes([left_width, 25])
            else:
                # Keep expanded at fixed width
                total_width = self.width()
                panel_width = 200
                left_width = total_width - panel_width
                self.main_horizontal_splitter.setSizes([left_width, panel_width])
            
            # Debounce resize events
            self.resize_timer.start(500)

    def closeEvent(self, event):
        """Save window state when closing with improved cleanup"""
        self.is_closing = True
        
        try:
            # Stop timers
            if hasattr(self, 'resource_timer'):
                self.resource_timer.stop()
            if hasattr(self, 'resize_timer'):
                self.resize_timer.stop()
            
            # Save window geometry
            geom = self.geometry()
            self.config["window_geometry"] = [geom.x(), geom.y(), geom.width(), geom.height()]
            print(f"Saved main window size: {geom.width()}x{geom.height()}")
            
            # Save zoom factor
            if hasattr(self, 'game_view'):
                self.config["zoom_factor"] = self.game_view.zoom_factor
            
            # Save vertical splitter sizes  
            sizes = self.left_vertical_splitter.sizes()
            if len(sizes) >= 2:
                self.config["chat_panel_height"] = sizes[1]
            
            # Save chat panel visibility
            self.config["chat_panel_visible"] = self.chat_panel.isVisible()
            
            # Save chat zoom factor
            if hasattr(self.chat_panel, 'chat_zoom_factor'):
                self.config["chat_zoom_factor"] = self.chat_panel.chat_zoom_factor
            
            config.save_config(self.config)
            
            # Close all browser tabs with cleanup
            for i in range(self.tab_widget.count() - 1, 0, -1):  # Skip game tab (index 0)
                self.close_browser_tab(i)
            
            # Clean up game view cache
            if hasattr(self.game_view, 'cleanup_cache_files'):
                try:
                    self.game_view.cleanup_cache_files()
                except Exception as e:
                    print(f"Error cleaning up game view cache: {e}")
            
            # Clean up chat panel cache
            if hasattr(self.chat_panel, 'cleanup_cache_files'):
                try:
                    self.chat_panel.cleanup_cache_files()
                except Exception as e:
                    print(f"Error cleaning up chat panel cache: {e}")
            
            # Clean up tools panel
            if hasattr(self.tools_panel, 'close_all_tool_windows'):
                self.tools_panel.close_all_tool_windows()
            
            # Final garbage collection
            gc.collect()
            
        except Exception as e:
            print(f"Error during window close cleanup: {e}")
        
        event.accept()