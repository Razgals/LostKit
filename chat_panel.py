# chat_panel.py
import gc
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import QUrl, Qt, QTimer, QStandardPaths
from PyQt6.QtGui import QFont, QPalette, QColor
from pathlib import Path
import config


def get_persistent_storage_paths():
    """Get platform-appropriate persistent storage paths for chat data"""
    try:
        # Use system-appropriate app data directory for persistent storage
        app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        if app_data_dir:
            base_path = Path(app_data_dir) / "ChatPanel"
            base_path.mkdir(parents=True, exist_ok=True)
            
            cache_path = base_path / "cache"
            storage_path = base_path / "storage"
            
            cache_path.mkdir(exist_ok=True)
            storage_path.mkdir(exist_ok=True)
            
            return str(cache_path), str(storage_path)
    except Exception as e:
        print(f"Warning: Could not create persistent storage directories: {e}")
    
    # Fallback to local directories if system paths fail
    fallback_base = Path("chat_data")
    fallback_base.mkdir(exist_ok=True)
    
    cache_path = fallback_base / "cache"
    storage_path = fallback_base / "storage"
    
    cache_path.mkdir(exist_ok=True)
    storage_path.mkdir(exist_ok=True)
    
    return str(cache_path), str(storage_path)


class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set font matching the application theme
        font = QFont("RuneScape UF", 13)
        if not font.exactMatch():
            font = QFont("runescape_uf", 13)
        self.setFont(font)
        
        # Set black background
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Load chat zoom factor from config (default 0.8 = 80% zoom)
        self.chat_zoom_factor = config.get_config_value("chat_zoom_factor", 0.8)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the chat panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Chat title label - MUCH smaller height but same font size
        title_label = QLabel("IRC Chat")
        title_label.setStyleSheet("""
            QLabel {
                color: #f5e6c0;
                font-weight: bold;
                font-size: 16px;
                background-color: #2a2a2a;
                border: 2px solid #2a2a2a;
                padding: 2px 10px;
                border-radius: 0px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFixedHeight(22)  # Reduced from 35px to 22px
        layout.addWidget(title_label)
        
        # Web view for IRC chat
        self.create_chat_browser()
        layout.addWidget(self.chat_browser)
        
        # Set minimum height for the chat panel
        self.setMinimumHeight(150)
        
        # Apply styling to the panel
        self.setStyleSheet("""
            ChatPanel {
                background-color: #000000;
                border: 2px solid #2a2a2a;
                border-radius: 0px;
            }
        """)
        
    def create_chat_browser(self):
        """Create the web browser for IRC chat with persistent storage"""
        try:
            # Use persistent storage paths instead of temporary directories
            profile_name = "ChatPanel_Persistent"
            
            # Create profile for chat browser with persistent name
            profile = QWebEngineProfile(profile_name, self)
            
            # Get persistent storage paths that survive program restarts and OS reboots
            cache_path, storage_path = get_persistent_storage_paths()
                
            profile.setCachePath(cache_path)
            profile.setPersistentStoragePath(storage_path)
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
            
            # Optimize settings for chat
            settings = profile.settings()
            if config.get_config_value("resource_optimization", True):
                # Disable unnecessary features for chat
                settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
                settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, False)  # Chat doesn't need WebGL
                settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, False)  # Not needed for chat
                settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, False)
                settings.setAttribute(QWebEngineSettings.WebAttribute.TouchIconsEnabled, False)
            
            # Create page and web view
            page = QWebEnginePage(profile, self)
            self.chat_browser = QWebEngineView()
            self.chat_browser.setPage(page)
            
            # Store paths for cleanup
            self.cache_path = cache_path
            self.storage_path = storage_path
            
            # Set initial zoom factor (default 0.8 = 80% zoom)
            self.chat_browser.setZoomFactor(self.chat_zoom_factor)
            
            # Style the web view
            self.chat_browser.setStyleSheet("""
                QWebEngineView {
                    background-color: #000000;
                    border: 2px solid #2a2a2a;
                    border-radius: 0px;
                }
            """)
            
            # Load the placeholder URL
            placeholder_url = "https://irc.losthq.rs"
            print(f"Loading chat placeholder URL: {placeholder_url}")
            self.chat_browser.setUrl(QUrl(placeholder_url))
            
            # Connect signals
            self.chat_browser.loadFinished.connect(self.on_chat_load_finished)
            
            # Enable mouse wheel zoom control for chat
            self.chat_browser.wheelEvent = self.chat_wheel_event
            
            # Setup cleanup timer for chat
            self.cleanup_timer = QTimer(self)
            self.cleanup_timer.timeout.connect(self.perform_cleanup)
            cleanup_interval = config.get_config_value("cache_cleanup_interval", 300) * 1000  # Convert to ms
            self.cleanup_timer.start(cleanup_interval)
            
        except Exception as e:
            print(f"Error creating chat browser: {e}")
            # Create a fallback label if web view fails
            self.chat_browser = QLabel("Chat will be available soon!")
            self.chat_browser.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.chat_browser.setStyleSheet("""
                QLabel {
                    color: #f5e6c0;
                    background-color: #2a2a2a;
                    border: 2px solid #2a2a2a;
                    padding: 20px;
                    font-size: 14px;
                }
            """)
            self.cache_path = None
            self.storage_path = None

    def perform_cleanup(self):
        """Perform periodic cleanup for chat browser"""
        try:
            if config.get_config_value("resource_optimization", True):
                # Force garbage collection
                gc.collect()
                
                # Clear chat browser cache if available
                if hasattr(self.chat_browser, 'page') and self.chat_browser.page():
                    try:
                        self.chat_browser.page().profile().clearAllVisitedLinks()
                    except:
                        pass  # Ignore errors during cleanup
                
                print("Performed chat panel cleanup")
        except Exception as e:
            print(f"Error during chat cleanup: {e}")
    
    def chat_wheel_event(self, event):
        """Handle mouse wheel events for chat zoom control"""
        try:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                # Ctrl + wheel = zoom
                delta = event.angleDelta().y()
                zoom_step = 0.1
                
                if delta > 0:
                    self.chat_zoom_factor += zoom_step
                else:
                    self.chat_zoom_factor -= zoom_step
                    
                # Clamp zoom factor to reasonable bounds
                self.chat_zoom_factor = max(0.25, min(self.chat_zoom_factor, 3.0))
                
                # Apply zoom
                self.chat_browser.setZoomFactor(self.chat_zoom_factor)
                
                # Save to config
                config.set_config_value("chat_zoom_factor", self.chat_zoom_factor)
                print(f"Chat zoom set to: {int(self.chat_zoom_factor * 100)}%")
                
                # Accept event to prevent scrolling
                event.accept()
            else:
                # Normal scrolling - call original wheelEvent
                QWebEngineView.wheelEvent(self.chat_browser, event)
        except Exception as e:
            print(f"Error in chat wheelEvent: {e}")
            QWebEngineView.wheelEvent(self.chat_browser, event)
    
    def on_chat_load_finished(self, ok: bool):
        """Handle chat page load completion"""
        if ok:
            print("✅ Chat panel loaded successfully")
            # Apply saved zoom factor after page loads
            try:
                self.chat_browser.setZoomFactor(self.chat_zoom_factor)
                print(f"Applied chat zoom: {int(self.chat_zoom_factor * 100)}%")
            except Exception as e:
                print(f"Error setting chat zoom factor: {e}")
        else:
            print("❌ Failed to load chat panel")
    
    def load_chat_url(self, url):
        """Load a new URL in the chat browser"""
        if hasattr(self.chat_browser, 'setUrl'):
            print(f"Loading new chat URL: {url}")
            self.chat_browser.setUrl(QUrl(url))
        else:
            print("Chat browser not available for URL loading")
    
    def reload_chat(self):
        """Reload the chat browser"""
        if hasattr(self.chat_browser, 'reload'):
            print("Reloading chat browser")
            self.chat_browser.reload()
        else:
            print("Chat browser not available for reloading")

    def cleanup_cache_files(self):
        """Selective cleanup for persistent storage - only clear temporary cache, preserve settings"""
        try:
            # Only clear browsing cache, not the entire cache directory
            # This preserves important settings while clearing temporary files
            if self.cache_path and os.path.exists(self.cache_path):
                # Clear only temporary files, preserve important data
                cache_subdirs = ['GPUCache', 'Code Cache', 'WebStorage']
                import shutil
                for subdir in cache_subdirs:
                    subdir_path = os.path.join(self.cache_path, subdir)
                    if os.path.exists(subdir_path):
                        try:
                            shutil.rmtree(subdir_path, ignore_errors=True)
                            print(f"Cleaned up chat cache subdir: {subdir}")
                        except Exception as e:
                            print(f"Error cleaning chat cache subdir {subdir}: {e}")
                print(f"Cleaned up temporary chat cache files in: {self.cache_path}")
        except Exception as e:
            print(f"Error cleaning chat cache: {e}")
        
        # NOTE: We don't clean storage_path anymore since it contains persistent settings
        # that should survive between program restarts
        print("Preserved persistent chat storage (settings will persist between restarts)")

    def reset_chat_settings(self):
        """Completely reset all chat settings and storage (use with caution)"""
        try:
            if self.storage_path and os.path.exists(self.storage_path):
                import shutil
                shutil.rmtree(self.storage_path, ignore_errors=True)
                print(f"RESET: Cleared all chat storage: {self.storage_path}")
                
                # Recreate the directory
                os.makedirs(self.storage_path, exist_ok=True)
                print("Chat settings have been reset - all persistent data cleared")
                
                # Optionally reload the chat to apply the reset
                self.reload_chat()
        except Exception as e:
            print(f"Error resetting chat settings: {e}")

    def closeEvent(self, event):
        """Clean up when chat panel is closed (preserves persistent settings)"""
        # Stop cleanup timer
        if hasattr(self, 'cleanup_timer'):
            self.cleanup_timer.stop()
            
        # FIX: Properly cleanup web engine components to avoid profile release errors
        if hasattr(self, 'chat_browser') and self.chat_browser:
            try:
                # Clear page before deleting
                self.chat_browser.setPage(None)
                # Delete the browser
                self.chat_browser.deleteLater()
            except Exception as e:
                print(f"Error cleaning up chat browser: {e}")
        
        # Clean up temporary cache files only (preserves settings)
        self.cleanup_cache_files()
        
        # Force garbage collection
        gc.collect()
        
        super().closeEvent(event)