"""
topics.py
Shared MQTT topic utilities for Presentation Clicker.
"""

def get_base_topic(room: str) -> str:
    """
    Returns the base MQTT topic for the given room.
    
    Args:
        room: Room code.
        
    Returns:
        str: Base topic string.
    """
    return f"presentationclicker/{room}"
