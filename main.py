#!/usr/bin/env python3
# main.py - Updated with custom TTF font support and readable scaling
import sys
import traceback
import os
import atexit
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QDir, QStandardPaths
from PyQt6.QtGui import QFont, QIcon

# Import your main window class
from main_window import MainWindow
import config
from font_loader import font_loader, initialize_fonts

def cleanup_temp_files():
    """Clean up only temporary cache files, preserve persistent data"""
    try:
        import tempfile
        import shutil
        
        temp_dir = tempfile.gettempdir()
        # Only clean up truly temporary files, not persistent data
        temp_patterns = [
            "lostkit_temp_",
            "lostkit_tmp_",
        ]
        
        for pattern in temp_patterns:
            for item in os.listdir(temp_dir):
                if item.startswith(pattern):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                        else:
                            os.remove(item_path)
                        print(f"Cleaned up temporary file: {item_path}")
                    except Exception as e:
                        print(f"Could not clean temporary file {item_path}: {e}")
    except Exception as e:
        print(f"Error during temp cleanup: {e}")

def setup_application_paths():
    """Setup proper application data paths"""
    try:
        # Ensure persistent storage directories exist
        app_data_dir = config.get_app_data_dir()
        cache_dir = config.get_persistent_cache_dir()
        storage_dir = config.get_persistent_storage_dir()
        
        print(f"App data directory: {app_data_dir}")
        print(f"Cache directory: {cache_dir}")
        print(f"Storage directory: {storage_dir}")
        
        # Test write permissions
        for dir_path in [app_data_dir, cache_dir, storage_dir]:
            test_file = os.path.join(dir_path, "write_test.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print(f"Write access confirmed for: {dir_path}")
            except Exception as e:
                print(f"Warning: Write access issue for {dir_path}: {e}")
            
    except Exception as e:
        print(f"Warning: Could not setup application paths: {e}")

def main():
    try:
        # Change to the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        print(f"Working directory: {script_dir}")
        
        # Setup application paths and persistent storage
        setup_application_paths()
        
        # Register cleanup function (only for temp files, not persistent data)
        atexit.register(cleanup_temp_files)
        
        # Create QApplication instance
        app = QApplication(sys.argv)
        
        # Enable high DPI support
        try:
            if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
                app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
                app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            pass
        
        # Set application properties
        app.setApplicationName("LostKit")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("LostKit")
        app.setApplicationDisplayName("LostKit")
        
        app.setQuitOnLastWindowClosed(True)
        
        # Initialize custom font system FIRST
        print("Loading custom fonts...")
        font_loaded = initialize_fonts()
        
        if font_loaded:
            # Use the custom font as application default - readable 1.7x size
            app_font = font_loader.get_font(14)  # This will be scaled to ~24pt internally (1.7x)
            app.setFont(app_font)
            print(f"Custom font applied as default with 1.7x scaling: {font_loader.get_font_family_name()}")
        else:
            # Fallback to existing system - also readable 1.7x size
            print("Custom font not available, using fallback system")
            try:
                font = QFont("RuneScape UF", 24)  # 14 * 1.7 = ~24
                if not font.exactMatch():
                    font = QFont("runescape_uf", 24)  # 14 * 1.7 = ~24
                app.setFont(font)
                print("RuneScape font fallback loaded successfully with 1.7x scaling")
            except Exception as font_error:
                print(f"Warning: Could not load RuneScape font fallback: {font_error}")
                font = QFont("Arial", 24)  # 14 * 1.7 = ~24
                app.setFont(font)
        
        # Initialize config system
        print("Initializing configuration system...")
        initial_config = config.load_config()
        print(f"Config loaded from: {config.CONFIG_FILE}")
        print(f"Config contains {len(initial_config)} settings")
        
        # Create and show main window
        print("Creating main window...")
        main_window = MainWindow()
        main_window.setWindowIcon(QIcon("icon.ico"))
        main_window.show()
        print("Main window created and shown")
        
        # Optimize garbage collection
        import gc
        gc.set_threshold(700, 10, 10)
        
        font_status = "custom TTF font" if font_loaded else "fallback fonts"
        print(f"LostKit started successfully with {font_status}")
        print("Your settings, cookies, and login data will be preserved between restarts")
        
        # Start the application event loop
        exit_code = app.exec()
        
        print("Application shutting down...")
        
        # Final config save
        try:
            config.force_save_config()
            print("Final config save completed")
        except Exception as e:
            print(f"Error in final config save: {e}")
        
        # Clean up only temporary files
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
