#!/usr/bin/env python3
# main.py
import sys
import traceback
import os
import tempfile
import atexit
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QDir, QStandardPaths
from PyQt6.QtGui import QFont

# Import your main window class
from main_window import MainWindow

def cleanup_temp_files():
    """Clean up temporary cache files on exit"""
    try:
        temp_dir = tempfile.gettempdir()
        cache_dirs = [
            "lostkit_web_cache",
            "lostkit_chat_cache", 
            "lostkit_chat_storage"
        ]
        
        for cache_dir in cache_dirs:
            cache_path = os.path.join(temp_dir, cache_dir)
            if os.path.exists(cache_path):
                try:
                    import shutil
                    shutil.rmtree(cache_path, ignore_errors=True)
                    print(f"Cleaned up cache: {cache_path}")
                except Exception as e:
                    print(f"Could not clean cache {cache_path}: {e}")
    except Exception as e:
        print(f"Error during cleanup: {e}")

def setup_application_paths():
    """Setup proper application data paths"""
    try:
        # Create application data directory
        app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        if not QDir().mkpath(app_data_dir):
            print(f"Warning: Could not create app data directory: {app_data_dir}")
        
        # Ensure temp directory exists and is writable
        temp_dir = tempfile.gettempdir()
        if not os.access(temp_dir, os.W_OK):
            print(f"Warning: Temp directory not writable: {temp_dir}")
            
    except Exception as e:
        print(f"Warning: Could not setup application paths: {e}")

def main():
    try:
        # Change to the directory where the script is located
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Setup application paths
        setup_application_paths()
        
        # Register cleanup function
        atexit.register(cleanup_temp_files)
        
        # Create QApplication instance - REMOVED SingleApplication to allow multiple instances
        app = QApplication(sys.argv)
        
        # Enable high DPI support for better scaling (PyQt6 compatible)
        try:
            # These attributes may not exist in all PyQt6 versions
            if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
                app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
                app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            # PyQt6 handles high DPI automatically in newer versions
            pass
        
        # Set application properties
        app.setApplicationName("LostKit")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("LostKit")
        app.setApplicationDisplayName("LostKit")
        
        # Set quit on last window closed to False for multiple instance support
        app.setQuitOnLastWindowClosed(True)
        
        # Try to load and set the RuneScape font with larger size
        try:
            font = QFont("RuneScape UF", 14)  # Increased from 12 to 14
            if not font.exactMatch():
                font = QFont("runescape_uf", 14)  # Increased from 12 to 14
            app.setFont(font)
        except Exception as font_error:
            print(f"Warning: Could not load RuneScape font: {font_error}")
            # Fallback to Arial with larger size
            font = QFont("Arial", 14)  # Increased from 12 to 14
            app.setFont(font)
        
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        # Optimize garbage collection for better resource management
        import gc
        gc.set_threshold(700, 10, 10)  # More aggressive garbage collection
        
        # Start the application event loop
        exit_code = app.exec()
        
        # Clean up before exit
        cleanup_temp_files()
        
        sys.exit(exit_code)
        
    except ImportError as e:
        error_msg = f"Import Error: {e}\n\nMissing required modules. Please install:\npip install PyQt6 PyQt6-WebEngine"
        print(error_msg)
        try:
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Import Error")
            msg.setText(error_msg)
            msg.exec()
        except:
            pass
    except Exception as e:
        error_msg = f"Unexpected error: {e}\n\nFull traceback:\n{traceback.format_exc()}"
        print(error_msg)
        try:
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Application Error")
            msg.setText(str(e))
            msg.setDetailedText(traceback.format_exc())
            msg.exec()
        except:
            pass

if __name__ == "__main__":
    main()