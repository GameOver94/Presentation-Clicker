"""
mqtt_config.py
Shared MQTT configuration utilities for Presentation Clicker.
"""
import os
import yaml

DEFAULT_CONFIG = {
    "host": "test.mosquitto.org",
    "port": 1883,
    "keepalive": 15,
    "transport": "tcp"  # 'tcp' or 'websockets'
}

def load_mqtt_config(config_path: str) -> dict:
    """
    Load MQTT configuration from a YAML file.
    Returns default config if file is missing or invalid.
    
    Args:
        config_path: Path to the MQTT config file.
        
    Returns:
        dict: Configuration dictionary with default values merged.
    """
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return {**DEFAULT_CONFIG, **config}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def update_mqtt_config(config_path: str, host=None, port=None, keepalive=None, transport=None, theme=None):
    """
    Update the MQTT config file with provided values.
    
    Args:
        config_path: Path to the config file.
        host: MQTT broker host.
        port: MQTT broker port.
        keepalive: MQTT keepalive interval.
        transport: MQTT transport protocol.
        theme: UI theme name.
    """
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception:
            pass
    
    changed = False
    if host is not None:
        config['host'] = host
        changed = True
    if port is not None:
        config['port'] = port
        changed = True
    if keepalive is not None:
        config['keepalive'] = keepalive
        changed = True
    if transport is not None:
        config['transport'] = transport
        changed = True
    if theme is not None:
        config['theme'] = theme
        changed = True
    
    if changed:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f)
