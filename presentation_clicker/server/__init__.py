"""
Server module for Presentation Clicker.

Contains the server-side components for receiving presentation remote commands.
"""

from .ui_server import main as server_main

__all__ = ['server_main']
