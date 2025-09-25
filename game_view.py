# game_view.py
import gc
import os
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import Qt, QUrl, QDir, pyqtSignal, QTimer
import config
import tempfile


class GameViewWidget(QWebEngineView):
    zoom_changed = pyqtSignal(float)
    
    def __init__(self, url, parent=None):
        super().__init__(parent)

        try:
            # FIXED: Use process ID to ensure unique cache paths
            process_id = os.getpid()
            profile_name = f"LostClient_{process_id}"
            
            # Setup persistent profile with performance optimizations
            profile = QWebEngineProfile(profile_name, self)
            
            # Use temp directory with PID for completely separate cache locations
            temp_dir = tempfile.gettempdir()
            cache_path = os.path.join(temp_dir, f"lostkit_web_cache_{process_id}")
            storage_path = os.path.join(temp_dir, f"lostkit_web_storage_{process_id}")
            
            # Create directories if they don't exist
            os.makedirs(cache_path, exist_ok=True)
            os.makedirs(storage_path, exist_ok=True)
                
            profile.setCachePath(cache_path)
            profile.setPersistentStoragePath(storage_path)
            
            # Performance optimizations
            settings = profile.settings()
            
            # Enable hardware acceleration and GPU features for game
            settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
            
            # Game-specific optimizations
            settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
            
            # Enable features for better game performance
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, False)
            
            # Enable images but disable plugins
            settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
            
            # Resource optimization settings
            if config.get_config_value("resource_optimization", True):
                # Disable unnecessary features for better performance
                settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, False)
                settings.setAttribute(QWebEngineSettings.WebAttribute.TouchIconsEnabled, False)
                settings.setAttribute(QWebEngineSettings.WebAttribute.FocusOnNavigationEnabled, True)

            page = QWebEnginePage(profile, self)
            self.setPage(page)
            
            # Store paths for cleanup
            self.cache_path = cache_path
            self.storage_path = storage_path

            # Load the game
            self.setUrl(QUrl(url))

            # Load zoom factor from config
            self.zoom_factor = config.get_config_value("zoom_factor", 1.0)
            self.setZoomFactor(self.zoom_factor)

            # Connect signals
            self.page().loadFinished.connect(self.on_load_finished)
            
            # Enable focus for keyboard events
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
            # Setup periodic cleanup for better resource management
            self.cleanup_timer = QTimer(self)
            self.cleanup_timer.timeout.connect(self.perform_cleanup)
            cleanup_interval = config.get_config_value("cache_cleanup_interval", 300) * 1000  # Convert to ms
            self.cleanup_timer.start(cleanup_interval)
            
        except Exception as e:
            print(f"Error initializing GameViewWidget: {e}")
            # Set a basic zoom factor as fallback
            self.zoom_factor = 1.0
            self.cache_path = None
            self.storage_path = None

    def perform_cleanup(self):
        """Perform periodic cleanup to optimize performance"""
        try:
            if config.get_config_value("resource_optimization", True):
                # Force garbage collection
                gc.collect()
                
                # Clear visited links to free memory
                try:
                    self.page().profile().clearAllVisitedLinks()
                except:
                    pass  # Ignore errors during cleanup
                
                print("Performed game view cleanup")
        except Exception as e:
            print(f"Error during game view cleanup: {e}")

    def on_load_finished(self, ok: bool):
        """Handle page load completion"""
        if ok:
            print("✅ Game page loaded successfully with performance optimizations.")
            # Apply saved zoom factor after page loads
            try:
                self.setZoomFactor(self.zoom_factor)
            except Exception as e:
                print(f"Error setting zoom factor: {e}")
        else:
            print("❌ Failed to load game page.")

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        try:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                # Ctrl + wheel = zoom
                delta = event.angleDelta().y()
                zoom_step = 0.1
                
                if delta > 0:
                    self.zoom_factor += zoom_step
                else:
                    self.zoom_factor -= zoom_step
                    
                # Clamp zoom factor to reasonable bounds
                self.zoom_factor = max(0.25, min(self.zoom_factor, 5.0))
                
                # Apply zoom
                self.setZoomFactor(self.zoom_factor)
                
                # Save to config
                config.set_config_value("zoom_factor", self.zoom_factor)
                
                # Emit signal
                self.zoom_changed.emit(self.zoom_factor)
                
                # Accept event to prevent scrolling
                event.accept()
            else:
                # Normal scrolling
                super().wheelEvent(event)
        except Exception as e:
            print(f"Error in wheelEvent: {e}")
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        try:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if event.key() == Qt.Key.Key_0:
                    # Ctrl+0: Reset zoom to 100%
                    self.zoom_factor = 1.0
                    self.setZoomFactor(self.zoom_factor)
                    config.set_config_value("zoom_factor", self.zoom_factor)
                    self.zoom_changed.emit(self.zoom_factor)
                    event.accept()
                    return
                elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
                    # Ctrl++: Zoom in
                    self.zoom_factor = min(self.zoom_factor + 0.1, 5.0)
                    self.setZoomFactor(self.zoom_factor)
                    config.set_config_value("zoom_factor", self.zoom_factor)
                    self.zoom_changed.emit(self.zoom_factor)
                    event.accept()
                    return
                elif event.key() == Qt.Key.Key_Minus:
                    # Ctrl+-: Zoom out
                    self.zoom_factor = max(self.zoom_factor - 0.1, 0.25)
                    self.setZoomFactor(self.zoom_factor)
                    config.set_config_value("zoom_factor", self.zoom_factor)
                    self.zoom_changed.emit(self.zoom_factor)
                    event.accept()
                    return
            
            # Pass other key events to the web view
            super().keyPressEvent(event)
        except Exception as e:
            print(f"Error in keyPressEvent: {e}")
            super().keyPressEvent(event)

    def reset_zoom(self):
        """Reset zoom to 100%"""
        try:
            self.zoom_factor = 1.0
            self.setZoomFactor(self.zoom_factor)
            config.set_config_value("zoom_factor", self.zoom_factor)
            self.zoom_changed.emit(self.zoom_factor)
        except Exception as e:
            print(f"Error resetting zoom: {e}")

    def zoom_in(self):
        """Zoom in by one step"""
        try:
            self.zoom_factor = min(self.zoom_factor + 0.1, 5.0)
            self.setZoomFactor(self.zoom_factor)
            config.set_config_value("zoom_factor", self.zoom_factor)
            self.zoom_changed.emit(self.zoom_factor)
        except Exception as e:
            print(f"Error zooming in: {e}")

    def zoom_out(self):
        """Zoom out by one step"""
        try:
            self.zoom_factor = max(self.zoom_factor - 0.1, 0.25)
            self.setZoomFactor(self.zoom_factor)
            config.set_config_value("zoom_factor", self.zoom_factor)
            self.zoom_changed.emit(self.zoom_factor)
        except Exception as e:
            print(f"Error zooming out: {e}")

    def get_zoom_percentage(self):
        """Get current zoom as percentage string"""
        try:
            return f"{int(self.zoom_factor * 100)}%"
        except Exception:
            return "100%"

    def cleanup_cache_files(self):
        """Clean up cache files when widget is destroyed"""
        try:
            if self.cache_path and os.path.exists(self.cache_path):
                import shutil
                shutil.rmtree(self.cache_path, ignore_errors=True)
                print(f"Cleaned up game cache: {self.cache_path}")
        except Exception as e:
            print(f"Error cleaning game cache: {e}")

def closeEvent(self, event):
    """Clean up when widget is closed"""
    # Stop cleanup timer
    if hasattr(self, 'cleanup_timer'):
        self.cleanup_timer.stop()
        
    # FIX: Properly cleanup web engine components to avoid profile release errors
    if hasattr(self, 'page') and self.page():
        try:
            # Clear page before deleting
            self.setPage(None)
            # Delete the page
            self.page().deleteLater()
        except Exception as e:
            print(f"Error cleaning up game view page: {e}")
    
    # Clean up cache files
    self.cleanup_cache_files()
    
    # Force garbage collection
    gc.collect()
    
    super().closeEvent(event)