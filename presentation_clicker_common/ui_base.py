"""
ui_base.py
Base UI application with common functionality for Presentation Clicker.
Handles theme management, fonts, logging, and common UI patterns.
"""
import os
import tkinter as tk
from abc import ABC, abstractmethod
from typing import Optional

from ttkbootstrap import Style
from ttkbootstrap.constants import PRIMARY

from .ui_common import ThemeManager, get_misc_icons
from .logging_common import UILogger
from .cli_common import create_common_parser, validate_args, load_theme_from_config, handle_config_operations


class BaseApp(ABC):
    """
    Base UI application with common functionality for client and server.
    Handles theme management, fonts, logging, and window setup.
    """
    
    def __init__(self, app_title: str, theme: str = "flatly", config_path: str = None):
        """
        Initialize the base UI application.
        Args:
            app_title: Title for the application window.
            theme: ttkbootstrap theme name.
            config_path: Path to config file for saving theme.
        """
        # --- Theming & root ---
        self.style: Style = Style(theme=theme)
        self.root: tk.Tk = self.style.master
        self.root.title(app_title)
        self.root.resizable(False, True)  # Fix width, allow height resize
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(
            theme_list=["flatly", "darkly"], 
            initial_theme=theme, 
            config_path=config_path
        )
        self.theme_manager.set_style(self.style)
        
        self._set_fonts()
        
        # Will be set by subclasses
        self.txt_log = None
        self.logger = None

    def _set_fonts(self) -> None:
        """Set fonts: default, monospace for log, and icon font for icons."""
        self.font_mono = ("Courier New", 9)
        self.font_icon = ("Segoe MDL2 Assets", 12)
        # Define a custom style for icon buttons
        self.style.configure("Icon.TButton", font=self.font_icon)

    def _setup_text_widget_theme(self, text_widget: tk.Text) -> None:
        """
        Configure text widget colors and font to match the current theme.
        Call this after creating a text widget.
        """
        bg_color = self.style.colors.bg
        fg_color = self.style.colors.fg
        text_widget.configure(bg=bg_color, fg=fg_color, font=self.font_mono)

    def _is_dark_theme(self) -> bool:
        """Detect if the current theme is dark based on the background color luminance."""
        return self.theme_manager.is_dark_theme()

    def _get_theme_icon(self) -> str:
        """Get the appropriate theme toggle icon based on current theme."""
        return self.theme_manager.get_theme_icon()

    def _set_title_with_server(self, server_info: str) -> None:
        """
        Set the window title to include server information.
        Args:
            server_info: Server information string to append to title.
        """
        base_title = self.root.title().split(" - ")[0]  # Get base title without server info
        self.root.title(f"{base_title} - {server_info}")

    def _switch_theme(self) -> None:
        """Toggle between light and dark themes and save to config."""
        self.theme_manager.switch_theme()
        
        # Re-apply icon font style after theme change (required for ttkbootstrap)
        self.style.configure("Icon.TButton", font=self.font_icon)
        
        # Update the theme toggle button icon after switching
        if hasattr(self, 'btn_switch_theme'):
            self.btn_switch_theme.config(text=self._get_theme_icon())
        
        # Update log colors if logger exists
        if hasattr(self, 'logger') and self.logger:
            from .logging_common import get_message_colors
            message_colors = get_message_colors(self._is_dark_theme())
            self.logger.update_theme_colors(message_colors)
            
            # Also update any existing message tag colors
            if hasattr(self, 'txt_log'):
                self.txt_log.tag_config("sent", background=message_colors["sent"])
                self.txt_log.tag_config("received", background=message_colors["received"])
                
        # Update text widget theme (colors and font)
        if hasattr(self, 'txt_log') and self.txt_log:
            self._setup_text_widget_theme(self.txt_log)
            
        # Call subclass-specific theme update if available
        if hasattr(self, '_update_theme_specific'):
            self._update_theme_specific()

    def _log(self, msg: str, **kwargs) -> None:
        """
        Log a message using the UILogger.
        Args:
            msg: Message to log.
            **kwargs: Additional arguments passed to logger.
        """
        if self.logger:
            self.logger.log(msg, **kwargs)

    def run(self) -> None:
        """
        Start the Tkinter main loop.
        """
        self.root.mainloop()

    # ─── Abstract Methods ────────────────────────────────────
    
    @abstractmethod
    def _create_widgets(self) -> None:
        """
        Create all UI widgets. Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _layout_widgets(self) -> None:
        """
        Layout all UI widgets. Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _setup_mqtt_callbacks(self) -> None:
        """
        Setup MQTT callbacks. Must be implemented by subclasses.
        """
        pass

    # ─── Common MQTT Callback Patterns ────────────────────────────────────

    def _on_mqtt_connect(self) -> None:
        """
        Common MQTT callback: connected. Updates UI state.
        Subclasses can override for specific behavior.
        """
        self.root.after(0, lambda: self._set_connected(True))

    def _on_mqtt_disconnect(self) -> None:
        """
        Common MQTT callback: disconnected. Updates UI state.
        Subclasses can override for specific behavior.
        """
        self.root.after(0, lambda: self._set_connected(False))

    @abstractmethod
    def _set_connected(self, is_connected: bool) -> None:
        """
        Update UI elements based on connection state.
        Must be implemented by subclasses.
        """
        pass


def create_main_function(app_name: str, app_class, default_theme: str = "flatly"):
    """
    Factory function to create a standardized main() function for apps.
    Args:
        app_name: Name for the argument parser.
        app_class: The application class to instantiate.
        default_theme: Default theme if none specified.
    Returns:
        A main function that can be called or used as module entry point.
    """
    def main():
        # Fixed config file path (relative to caller's file)
        import inspect
        caller_file = inspect.stack()[1].filename
        config_path = os.path.join(os.path.dirname(caller_file), 'mqtt_config.yaml')
        
        # Create parser and validate arguments
        parser = create_common_parser(app_name)
        args = parser.parse_args()
        
        if not validate_args(args):
            return
        
        # Load theme from config or use provided theme
        theme = args.theme or load_theme_from_config(config_path, default_theme)
        
        # Handle config operations
        config_changed, should_exit = handle_config_operations(args, config_path, theme)
        if should_exit:
            return
        
        # Launch the app
        app = app_class(theme=theme, config_path=config_path)
        app.run()
    
    return main
