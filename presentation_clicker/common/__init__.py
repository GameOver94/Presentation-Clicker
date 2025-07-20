"""
Presentation Clicker Common Library
Shared functionality between client and server components.
"""

__version__ = "0.1.0"

# Import all commonly used functions and classes for convenient access
from .mqtt_config import load_mqtt_config, update_mqtt_config, DEFAULT_CONFIG
from .encryption import get_fernet
from .ui_common import ThemeManager, get_misc_icons
from .cli_common import create_common_parser, validate_args, load_theme_from_config, handle_config_operations
from .topics import get_base_topic
from .logging_common import UILogger, get_message_colors
from .mqtt_base import BaseMqttHandler
from .ui_base import BaseApp, create_main_function

# Make all imports available at package level
__all__ = [
    'load_mqtt_config',
    'update_mqtt_config', 
    'DEFAULT_CONFIG',
    'get_fernet',
    'ThemeManager',
    'get_misc_icons',
    'create_common_parser',
    'validate_args',
    'load_theme_from_config',
    'handle_config_operations',
    'get_base_topic',
    'UILogger',
    'get_message_colors',
    'BaseMqttHandler',
    'BaseApp',
    'create_main_function'
]
