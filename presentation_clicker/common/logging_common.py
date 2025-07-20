"""
logging_common.py
Shared logging utilities for Presentation Clicker UI components.
"""
import datetime
import tkinter as tk
from typing import Optional, Callable, Dict, Any


class UILogger:
    """
    Common logging functionality for Presentation Clicker UI components.
    Handles timestamped logging with optional color tagging and theme-aware colors.
    """
    
    def __init__(self, text_widget: tk.Text, theme_manager=None):
        """
        Initialize the UI logger.
        
        Args:
            text_widget: The tkinter Text widget to log to.
            theme_manager: Optional theme manager for color calculations.
        """
        self.txt_log = text_widget
        self.theme_manager = theme_manager
        self._user_color_func: Optional[Callable[[str], str]] = None
    
    def set_user_color_function(self, color_func: Callable[[str], str]):
        """
        Set the function used to generate colors for users.
        
        Args:
            color_func: Function that takes a username and returns a color string.
        """
        self._user_color_func = color_func
    
    def log(self, msg: str, tag: str = None, user: str = None) -> None:
        """
        Append a timestamped message to the log window.
        
        Args:
            msg: Message string.
            tag: Optional tag for message type ('sent', 'received', etc.).
            user: Optional username for user-specific coloring.
        """
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.txt_log.config(state=tk.NORMAL)
        
        # Determine tag to use
        if user and self._user_color_func:
            # User-specific tag with color
            tag_name = f"userlog_{user}"
            user_color = self._user_color_func(user)
            self.txt_log.tag_configure(tag_name, background=user_color)
            self.txt_log.insert("end", f"[{timestamp}] {msg}\n", tag_name)
        elif tag:
            # Generic tag (sent, received, etc.)
            self.txt_log.insert("end", f"[{timestamp}] {msg}\n", tag)
        else:
            # No tag
            self.txt_log.insert("end", f"[{timestamp}] {msg}\n")
        
        self.txt_log.see("end")
        self.txt_log.config(state=tk.DISABLED)
    
    def update_theme_colors(self, color_updates: Dict[str, str] = None):
        """
        Update log tag colors and text widget background for theme changes.
        
        Args:
            color_updates: Optional dict of tag_name -> color mappings.
        """
        # Update text widget background to match theme
        if self.theme_manager and hasattr(self.theme_manager, 'style'):
            bg_color = self.theme_manager.style.colors.bg
            fg_color = self.theme_manager.style.colors.fg
            self.txt_log.configure(bg=bg_color, fg=fg_color)
        
        if color_updates:
            # Update specific colors provided
            for tag_name, color in color_updates.items():
                self.txt_log.tag_configure(tag_name, background=color)
        
        # Update user log colors if we have a color function
        if self._user_color_func:
            for tag_name in self.txt_log.tag_names():
                if tag_name.startswith("userlog_"):
                    user = tag_name.replace("userlog_", "")
                    user_color = self._user_color_func(user)
                    self.txt_log.tag_configure(tag_name, background=user_color)


def get_message_colors(is_dark_theme: bool) -> Dict[str, str]:
    """
    Get standard message colors for sent/received messages based on theme.
    
    Args:
        is_dark_theme: Whether the current theme is dark.
        
    Returns:
        Dict mapping message types to colors.
    """
    if is_dark_theme:
        return {
            "sent": "#2e4d36",      # dark green for sent
            "received": "#233c4e"   # dark blue for received
        }
    else:
        return {
            "sent": "#d1fad7",      # light green for sent
            "received": "#d6eaff"   # light blue for received
        }
