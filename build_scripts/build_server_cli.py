#!/usr/bin/env python3
"""
CLI entry point for the server that can be used with PyInstaller.
This script provides a simple entry point that calls the main CLI with server subcommand.
"""

import sys
import os

# Add the parent directory to the path so we can import presentation_clicker
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Now we can import the CLI
from presentation_clicker.cli import main

if __name__ == "__main__":
    # Set sys.argv to simulate calling "presentation-clicker server"
    sys.argv = ["presentation-clicker", "server"]
    main()
