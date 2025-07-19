"""
cli_common.py
Shared command-line interface utilities for Presentation Clicker.
"""
import argparse
import os
import yaml
from typing import Optional

def create_common_parser(description: str) -> argparse.ArgumentParser:
    """
    Create a common argument parser with shared options.
    
    Args:
        description: Description for the parser.
        
    Returns:
        argparse.ArgumentParser: Configured parser.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--host', type=str, help='MQTT broker host')
    parser.add_argument('--port', type=int, help='MQTT broker port (1-65535)')
    parser.add_argument('--keepalive', type=int, help='MQTT keepalive interval (positive integer)')
    parser.add_argument('--open-config-dir', action='store_true', help='Open the folder containing the config file and exit')
    parser.add_argument('--transport', type=str, choices=['tcp', 'websockets'], help='MQTT transport: tcp or websockets')
    parser.add_argument('--theme', type=str, help='UI theme (e.g., flatly, darkly)')
    return parser

def validate_args(args) -> bool:
    """
    Validate common command-line arguments.
    
    Args:
        args: Parsed arguments from argparse.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if args.host is not None and (not isinstance(args.host, str) or not args.host.strip()):
        print("Error: --host must be a non-empty string.")
        return False
    
    if args.port is not None:
        if not (1 <= args.port <= 65535):
            print("Error: --port must be an integer between 1 and 65535.")
            return False
    
    if args.keepalive is not None:
        if args.keepalive <= 0:
            print("Error: --keepalive must be a positive integer.")
            return False
    
    if args.transport is not None and args.transport not in ('tcp', 'websockets'):
        print("Error: --transport must be 'tcp' or 'websockets'.")
        return False
    
    return True

def load_theme_from_config(config_path: str, default_theme: str = "flatly") -> str:
    """
    Load theme from config file.
    
    Args:
        config_path: Path to config file.
        default_theme: Default theme if none found.
        
    Returns:
        str: Theme name.
    """
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception:
            pass
    return config.get('theme', default_theme)

def handle_config_operations(args, config_path: str, app_theme: str) -> tuple[bool, bool]:
    """
    Handle common config operations based on arguments.
    
    Args:
        args: Parsed arguments.
        config_path: Path to config file.
        app_theme: Theme for the app.
        
    Returns:
        tuple: (config_changed, should_exit)
    """
    from .mqtt_config import update_mqtt_config
    
    config_dir = os.path.dirname(config_path)
    config_changed = False
    
    # If any config argument is provided, update config
    if args.host is not None or args.port is not None or args.keepalive is not None or args.transport is not None or args.theme is not None:
        update_mqtt_config(config_path, args.host, args.port, args.keepalive, args.transport, theme=args.theme)
        print(f"Config updated: {config_path}")
        config_changed = True

    # If --open-config-dir is provided, open the folder and exit
    if args.open_config_dir:
        os.startfile(config_dir)
        return config_changed, True

    # If config was changed, exit (do not launch app)
    if config_changed:
        return config_changed, True
    
    return config_changed, False
