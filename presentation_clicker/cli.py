"""
Main CLI entry point for Presentation Clicker.

Provides subcommands for running client or server components.
"""
import argparse
import sys
from .client import client_main
from .server import server_main


def main():
    """Main entry point with subcommands."""
    parser = argparse.ArgumentParser(
        description="Presentation Clicker - Wireless presentation remote control system",
        prog="presentation-clicker"
    )
    
    subparsers = parser.add_subparsers(
        dest='command', 
        help='Available commands',
        title='Commands',
        description='Choose which component to run'
    )
    
    # Client subcommand
    client_parser = subparsers.add_parser(
        'client', 
        help='Run the presentation remote client'
    )
    client_parser.add_argument('--host', type=str, help='MQTT broker host')
    client_parser.add_argument('--port', type=int, help='MQTT broker port (1-65535)')
    client_parser.add_argument('--keepalive', type=int, help='MQTT keepalive interval (positive integer)')
    client_parser.add_argument('--open-config-dir', action='store_true', help='Open the folder containing the config file and exit')
    client_parser.add_argument('--transport', type=str, choices=['tcp', 'websockets'], help='MQTT transport: tcp or websockets')
    client_parser.add_argument('--theme', type=str, help='UI theme (e.g., flatly, darkly)')
    
    # Server subcommand  
    server_parser = subparsers.add_parser(
        'server', 
        help='Run the presentation receiver server'
    )
    server_parser.add_argument('--host', type=str, help='MQTT broker host')
    server_parser.add_argument('--port', type=int, help='MQTT broker port (1-65535)')
    server_parser.add_argument('--keepalive', type=int, help='MQTT keepalive interval (positive integer)')
    server_parser.add_argument('--open-config-dir', action='store_true', help='Open the folder containing the config file and exit')
    server_parser.add_argument('--transport', type=str, choices=['tcp', 'websockets'], help='MQTT transport: tcp or websockets')
    server_parser.add_argument('--theme', type=str, help='UI theme (e.g., flatly, darkly)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate function
    try:
        if args.command == 'client':
            # Set sys.argv for the client main function to parse
            original_argv = sys.argv.copy()
            sys.argv = ['presentation-clicker-client']
            if args.host:
                sys.argv.extend(['--host', args.host])
            if args.port:
                sys.argv.extend(['--port', str(args.port)])
            if args.keepalive:
                sys.argv.extend(['--keepalive', str(args.keepalive)])
            if args.open_config_dir:
                sys.argv.append('--open-config-dir')
            if args.transport:
                sys.argv.extend(['--transport', args.transport])
            if args.theme:
                sys.argv.extend(['--theme', args.theme])
            
            try:
                return client_main()
            finally:
                sys.argv = original_argv
                
        elif args.command == 'server':
            # Set sys.argv for the server main function to parse
            original_argv = sys.argv.copy()
            sys.argv = ['presentation-clicker-server']
            if args.host:
                sys.argv.extend(['--host', args.host])
            if args.port:
                sys.argv.extend(['--port', str(args.port)])
            if args.keepalive:
                sys.argv.extend(['--keepalive', str(args.keepalive)])
            if args.open_config_dir:
                sys.argv.append('--open-config-dir')
            if args.transport:
                sys.argv.extend(['--transport', args.transport])
            if args.theme:
                sys.argv.extend(['--theme', args.theme])
            
            try:
                return server_main()
            finally:
                sys.argv = original_argv
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
