# config.py
import json
import os
import threading
import time
from pathlib import Path
from PyQt6.QtCore import QStandardPaths

# Thread-safe config access
_config_lock = threading.RLock()
_config_cache = None
_cache_time = 0
CACHE_DURATION = 5  # Cache config for 5 seconds to reduce file I/O

# Use system-appropriate config location
def get_config_path():
    """Get platform-appropriate config file path"""
    try:
        # Try to use system config directory
        config_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        if config_dir:
            Path(config_dir).mkdir(parents=True, exist_ok=True)
            return os.path.join(config_dir, "config.json")
    except:
        pass
    
    # Fallback to local directory
    return "config.json"

CONFIG_FILE = get_config_path()

DEFAULT_CONFIG = {
    "window_geometry": None,
    "right_panel_width": 250,
    "right_panel_collapsed": False,  # Track collapse state
    "zoom_factor": 1.0,
    "open_external": True,  # True = separate windows, False = in-game browser
    "tool_window_geometry": [200, 200, 900, 700],  # x, y, width, height
    "theme": "dark_pastel",
    "chat_panel_visible": True,  # Chat panel visible by default
    "chat_panel_height": 300,  # Increased default chat panel height
    "chat_zoom_factor": 0.8,  # Default chat zoom
    "resource_optimization": True,  # Enable resource optimizations
    "cache_cleanup_interval": 300,  # Cleanup cache every 5 minutes
    "max_tool_windows": 10,  # Limit concurrent tool windows
    # Individual tool window geometries will be stored with keys like:
    # "tool_window_geometry_Forums": [x, y, w, h]
    # "tool_window_geometry_Clue_Coordinates": [x, y, w, h]
    # etc.
}

def load_config():
    """Load configuration with caching and thread safety"""
    global _config_cache, _cache_time
    
    with _config_lock:
        current_time = time.time()
        
        # Return cached config if still valid
        if _config_cache and (current_time - _cache_time) < CACHE_DURATION:
            return _config_cache.copy()
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Ensure all default keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                
                # Convert geometry values to integers if they exist
                if config.get("window_geometry") and isinstance(config["window_geometry"], list):
                    try:
                        config["window_geometry"] = [int(x) for x in config["window_geometry"]]
                    except (ValueError, TypeError):
                        config["window_geometry"] = None
                        
                if config.get("tool_window_geometry") and isinstance(config["tool_window_geometry"], list):
                    try:
                        config["tool_window_geometry"] = [int(x) for x in config["tool_window_geometry"]]
                    except (ValueError, TypeError):
                        config["tool_window_geometry"] = DEFAULT_CONFIG["tool_window_geometry"]
                
                # Convert individual tool window geometries
                for key, value in list(config.items()):
                    if key.startswith("tool_window_geometry_") and isinstance(value, list):
                        try:
                            config[key] = [int(x) for x in value]
                        except (ValueError, TypeError):
                            # Remove invalid geometry
                            del config[key]
                
                # Ensure numeric values are correct type with bounds checking
                try:
                    zoom = float(config.get("zoom_factor", 1.0))
                    config["zoom_factor"] = max(0.25, min(zoom, 5.0))
                except (ValueError, TypeError):
                    config["zoom_factor"] = 1.0
                    
                try:
                    chat_zoom = float(config.get("chat_zoom_factor", 0.8))
                    config["chat_zoom_factor"] = max(0.25, min(chat_zoom, 3.0))
                except (ValueError, TypeError):
                    config["chat_zoom_factor"] = 0.8
                    
                try:
                    config["right_panel_width"] = max(200, min(int(config.get("right_panel_width", 250)), 800))
                except (ValueError, TypeError):
                    config["right_panel_width"] = 250
                    
                try:
                    config["chat_panel_height"] = max(100, min(int(config.get("chat_panel_height", 300)), 600))
                except (ValueError, TypeError):
                    config["chat_panel_height"] = 300
                
                try:
                    config["max_tool_windows"] = max(1, min(int(config.get("max_tool_windows", 10)), 50))
                except (ValueError, TypeError):
                    config["max_tool_windows"] = 10
                    
                # Ensure boolean values are correct type
                config["open_external"] = bool(config.get("open_external", True))
                config["chat_panel_visible"] = bool(config.get("chat_panel_visible", True))
                config["resource_optimization"] = bool(config.get("resource_optimization", True))
                config["right_panel_collapsed"] = bool(config.get("right_panel_collapsed", False))
                
                # Cache the config
                _config_cache = config.copy()
                _cache_time = current_time
                
                return config
                
            except (json.JSONDecodeError, IOError, KeyError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                _config_cache = DEFAULT_CONFIG.copy()
                _cache_time = current_time
                return DEFAULT_CONFIG.copy()
        
        # No config file exists, use defaults
        _config_cache = DEFAULT_CONFIG.copy()
        _cache_time = current_time
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration with error handling and atomic writes"""
    global _config_cache, _cache_time
    
    with _config_lock:
        try:
            # Validate config before saving
            validated_config = {}
            for key, default_value in DEFAULT_CONFIG.items():
                if key in config:
                    validated_config[key] = config[key]
                else:
                    validated_config[key] = default_value
            
            # Also include any tool-specific geometries
            for key, value in config.items():
                if key.startswith("tool_window_geometry_"):
                    validated_config[key] = value
            
            # Create backup of existing config
            backup_file = CONFIG_FILE + ".backup"
            if os.path.exists(CONFIG_FILE):
                try:
                    import shutil
                    shutil.copy2(CONFIG_FILE, backup_file)
                except:
                    pass  # Backup failed, but continue
            
            # Atomic write using temporary file
            temp_file = CONFIG_FILE + ".tmp"
            try:
                with open(temp_file, "w", encoding='utf-8') as f:
                    json.dump(validated_config, f, indent=4, ensure_ascii=False)
                
                # Move temp file to final location (atomic on most systems)
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
                os.rename(temp_file, CONFIG_FILE)
                
                # Update cache
                _config_cache = validated_config.copy()
                _cache_time = time.time()
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                raise e
                
        except Exception as e:
            print(f"Error saving config: {e}")
            # Try to restore from backup
            backup_file = CONFIG_FILE + ".backup"
            if os.path.exists(backup_file):
                try:
                    import shutil
                    shutil.copy2(backup_file, CONFIG_FILE)
                    print("Restored config from backup")
                except:
                    pass

def get_config_value(key, default=None):
    """Get a single config value with caching"""
    config = load_config()
    return config.get(key, default)

def set_config_value(key, value):
    """Set a single config value efficiently"""
    config = load_config()
    config[key] = value
    save_config(config)

def get_unique_cache_path(base_name, instance_id=None):
    """Get a unique cache path for this instance"""
    import tempfile
    import time
    import os
    
    if instance_id is None:
        instance_id = str(int(time.time() * 1000))  # Use timestamp if no ID provided
    
    temp_dir = tempfile.gettempdir()
    cache_name = f"lostkit_{base_name}_{instance_id}_{os.getpid()}"  # Include process ID
    cache_path = os.path.join(temp_dir, cache_name)
    
    # Ensure directory exists and is writable
    try:
        os.makedirs(cache_path, exist_ok=True)
        # Test write permissions
        test_file = os.path.join(cache_path, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return cache_path
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create cache at {cache_path}: {e}")
        # Fallback to a different location
        fallback_path = os.path.join(temp_dir, f"fallback_cache_{instance_id}_{os.getpid()}")
        try:
            os.makedirs(fallback_path, exist_ok=True)
            return fallback_path
        except:
            return None

def cleanup_old_backups():
    """Clean up old config backups"""
    try:
        backup_file = CONFIG_FILE + ".backup"
        if os.path.exists(backup_file):
            # Keep backup only if it's newer than 1 week
            backup_age = time.time() - os.path.getmtime(backup_file)
            if backup_age > 7 * 24 * 3600:  # 1 week in seconds
                os.remove(backup_file)
                print("Cleaned up old config backup")
    except Exception as e:
        print(f"Error cleaning up backups: {e}")

# Clean up old backups on module import
cleanup_old_backups()