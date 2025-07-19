"""
ui_common.py
Shared UI utilities for Presentation Clicker.
"""
import os
import yaml
from typing import List, Optional
from ttkbootstrap import Style

class ThemeManager:
    """
    Manages theme switching and configuration for Presentation Clicker UIs.
    """
    
    def __init__(self, theme_list: List[str] = None, initial_theme: str = "flatly", config_path: str = None):
        """
        Initialize the theme manager.
        
        Args:
            theme_list: List of available themes.
            initial_theme: Initial theme name.
            config_path: Path to config file for saving theme.
        """
        self.theme_list = theme_list or ["flatly", "darkly"]
        self.theme_index = self.theme_list.index(initial_theme) if initial_theme in self.theme_list else 0
        self.config_path = config_path
        self.style: Optional[Style] = None
    
    def set_style(self, style: Style):
        """Set the ttkbootstrap Style object."""
        self.style = style
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self.theme_list[self.theme_index]
    
    def is_dark_theme(self) -> bool:
        """Detect if the current theme is dark based on the background color luminance."""
        if not self.style:
            return False
        bg = self.style.colors.bg
        if bg.startswith("#") and len(bg) == 7:
            r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
            luminance = 0.299*r + 0.587*g + 0.114*b
            return luminance < 128
        return False
    
    def get_theme_icon(self) -> str:
        """Return the icon for the current theme using Segoe MDL2 Assets (E706 for sun, E708 for moon)."""
        return "\uE706" if self.get_current_theme() == "flatly" else "\uE708"
    
    def switch_theme(self):
        """Switch to the next theme in the list and save to config."""
        self.theme_index = (self.theme_index + 1) % len(self.theme_list)
        new_theme = self.get_current_theme()
        
        if self.style:
            self.style.theme_use(new_theme)
        
        # Save theme to config
        if self.config_path:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            except Exception:
                config = {}
            config['theme'] = new_theme
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f)
        
        return new_theme

def get_misc_icons():
    """Return a dict of common icons using Segoe MDL2 Assets Unicode."""
    return {
        'copy': "\uE8C8",      # Copy
        'generate': "\uE72C",  # Refresh
        'paste': "\uE77F",     # Paste
        'prev': "\uE100",      # Chevron Left
        'next': "\uE101",      # Chevron Right
        'start': "\uE768",     # Play
        'end': "\uE71A",       # Stop
        'blackout': "\uE890",  # View
    }
