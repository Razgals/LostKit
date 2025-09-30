# font_loader.py - Fixed TTF font loading with proper scaling and detection
import os
import sys
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import QStandardPaths


class FontLoader:
    def __init__(self):
        self.custom_font_loaded = False
        self.font_family_name = None
        self.fallback_fonts = ["RuneScape UF", "runescape_uf", "Arial"]
        
    def load_custom_font(self):
        """Load the custom TTF font from the application directory"""
        try:
            # Determine correct app directory
            if getattr(sys, "frozen", False):
                # Running as a standalone exe
                app_dir = os.path.dirname(sys.executable)
            else:
                # Running as a script
                app_dir = os.path.dirname(os.path.abspath(__file__))
                
            ttf_files = [f for f in os.listdir(app_dir) if f.lower().endswith('.ttf')]
            
            if not ttf_files:
                print("No TTF files found in application directory")
                return False
            
            print(f"Found TTF files: {ttf_files}")
                
            # Prioritize Runescape-Quill-Caps.ttf specifically
            ttf_file = None
            
            # First priority: exact match for Runescape-Quill-Caps.ttf
            for f in ttf_files:
                if f.lower() == 'runescape-quill-caps.ttf':
                    ttf_file = f
                    print(f"Found exact match: {ttf_file}")
                    break
            
            # Second priority: any file containing 'runescape' and 'quill'
            if not ttf_file:
                for f in ttf_files:
                    if 'runescape' in f.lower() and 'quill' in f.lower():
                        ttf_file = f
                        print(f"Found runescape-quill match: {ttf_file}")
                        break
            
            # Third priority: any file containing 'runescape'
            if not ttf_file:
                for f in ttf_files:
                    if 'runescape' in f.lower():
                        ttf_file = f
                        print(f"Found runescape match: {ttf_file}")
                        break
            
            # Last resort: use first TTF file
            if not ttf_file:
                ttf_file = ttf_files[0]
                print(f"Using first available TTF: {ttf_file}")
                
            font_path = os.path.join(app_dir, ttf_file)
            
            if not os.path.exists(font_path):
                print(f"TTF font file not found: {font_path}")
                return False
            
            # Load the font into Qt's font database
            font_id = QFontDatabase.addApplicationFont(font_path)
            
            if font_id == -1:
                print(f"Failed to load custom font: {font_path}")
                return False
            
            # Get the family names from the loaded font
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            
            if not font_families:
                print("No font families found in TTF file")
                return False
            
            self.font_family_name = font_families[0]
            self.custom_font_loaded = True
            
            print(f"✅ Custom font loaded successfully: {self.font_family_name}")
            print(f"   From file: {ttf_file}")
            print(f"   All available families: {font_families}")
            return True
            
        except Exception as e:
            print(f"Error loading custom font: {e}")
            return False
    
    def get_font(self, size=14, weight=QFont.Weight.Normal):
        """Get a QFont object with the custom font or fallback - 1.7x scaling for readability"""
        # Scale font size by 1.7x for readable but larger text (was 5x before)
        scaled_size = int(size * 1.7)
        
        if self.custom_font_loaded and self.font_family_name:
            font = QFont(self.font_family_name, scaled_size, weight)
            if font.exactMatch():
                print(f"Using custom font: {self.font_family_name} at {scaled_size}pt")
                return font
            else:
                print(f"Custom font {self.font_family_name} not exact match, trying fallbacks")
        
        # Try fallback fonts
        for fallback in self.fallback_fonts:
            font = QFont(fallback, scaled_size, weight)
            if font.exactMatch():
                print(f"Using fallback font: {fallback} at {scaled_size}pt")
                return font
        
        # Ultimate fallback
        print(f"Using ultimate fallback: Arial at {scaled_size}pt")
        return QFont("Arial", scaled_size, weight)
    
    def get_font_family_name(self):
        """Get the loaded custom font family name or first fallback"""
        if self.custom_font_loaded and self.font_family_name:
            return self.font_family_name
        return self.fallback_fonts[0]
    
    def is_custom_font_available(self):
        """Check if custom font is successfully loaded"""
        return self.custom_font_loaded
    
    def get_font_stylesheet_family(self):
        """Get font family string for use in stylesheets"""
        if self.custom_font_loaded and self.font_family_name:
            # Include both custom and fallbacks for maximum compatibility
            return f"'{self.font_family_name}', 'RuneScape UF', 'runescape_uf', 'Arial', sans-serif"
        return "'RuneScape UF', 'runescape_uf', 'Arial', sans-serif"


# Global font loader instance
font_loader = FontLoader()

def initialize_fonts():
    """Initialize the font system - call this early in main()"""
    return font_loader.load_custom_font()
