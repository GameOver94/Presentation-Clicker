# Presentation Clicker

A cross-platform, secure, and user-friendly remote presentation control system. This project enables users to control presentation slides from any device over a network using MQTT, with a graphical interface for both presenters (Listener) and remote controllers (Client).

## Purpose

Presentation Clicker is designed to make remote presentation control seamless, secure, and intuitive. It is especially useful for online conferences, meetings, and town halls where multiple presenters need to control a centrally hosted presentation. With this tool, presenters can advance their own slides without needing to ask someone else to do it — eliminating the need for the "Next slide, please." The system ensures ease of use for all participants.

## What's New in v0.3.0

Version 0.3.0 introduces a major code refactoring with a simplified, flat folder structure across all modules. This update improves:

- **Developer Experience:** Easier navigation and simplified imports
- **Code Maintainability:** Consistent structure across client, server, and common modules  
- **Build Process:** Streamlined build scripts and configuration files
- **Project Organization:** All module files are now at the root level of each package

The functionality remains the same, but the codebase is now cleaner and more maintainable for future development.

## Components

### Listener (Server)
- **Role:** Acts as the presentation host.
- **Function:** Runs on the presentation computer, listens for commands from clients, manages user permissions, and simulates keyboard events to control the presentation software (e.g., PowerPoint, PDF viewers).
- **Features:**
  - Secure MQTT communication with encryption
  - User management and permission control
  - GUI for monitoring connected users and logs

### Client
- **Role:** Acts as the remote control.
- **Function:** Runs on any device (laptop, tablet, etc.), connects to the listener, and sends navigation commands (next, previous, start, end, blackout) to control the presentation.
- **Features:**
  - Secure MQTT communication with encryption
  - Simple GUI for connecting and sending commands
  - Log window for feedback

### Theming: Light/Dark
- Both the Client and Listener UIs now support switching between a light and a dark theme at runtime.
- Use the ☀️/🌛 button in the UI to toggle between light ("flatly") and dark ("darkly") modes instantly.
- You can also set the theme at launch with the `--theme` command line option (e.g., `--theme darkly`).

## Installation

### 1. Download the Project

Clone the repository or download the source code:

```powershell
git clone https://github.com/GameOver94/Presentation-Clicker-Development.git
cd Presentation-Clicker-Development
```

### 2. Install Dependencies and Modules

Install all modules in development mode:

```powershell
# Install the common module (required by both client and server)
cd presentation_clicker_common
pip install -e .
cd ..

# Install the client module
cd presentation_clicker_client
pip install -e .
cd ..

# Install the server module
cd presentation_clicker_listener
pip install -e .
cd ..
```

### 3. Alternative: Install with pipx

For isolated installations with pipx, you have two options:

#### Option A: Install with Dependencies (Recommended)
```powershell
# Install client with common library as dependency
pipx install ./presentation_clicker_client --include-deps

# Install listener with common library as dependency  
pipx install ./presentation_clicker_listener --include-deps
```

#### Option B: Manual Dependency Installation
If the above doesn't work, install the common library first, then inject it:

```powershell
# Install the client or listener first
pipx install ./presentation_clicker_client

# Then inject the common library into the same environment
pipx inject presentation-clicker-client ./presentation_clicker_common

# For the listener:
pipx install ./presentation_clicker_listener
pipx inject presentation-clicker-listener ./presentation_clicker_common
```

> **Note:** pipx has limited support for local package dependencies. If you encounter issues, use the development installation method instead.

> **Note:** Pre-built standalone executables for Windows are available on the [GitHub Releases](https://github.com/GameOver94/Presentation-Clicker-Development/releases) page. You can download and run these without installing Python or any dependencies.

> **Note:** Make sure you have [pipx](https://pypa.github.io/pipx/) installed and available in your PATH if you want to install from source.

## Usage

### Run the Client
```powershell
presentation-clicker-client
```
Or run directly from the module:
```powershell
cd presentation_clicker_client
python -m ui_client
```

### Run the Listener
```powershell
presentation-clicker-listener
```
Or run directly from the module:
```powershell
cd presentation_clicker_listener
python -m ui_server
```

Both commands will launch a graphical interface. Follow the on-screen instructions to connect and control your presentation.

## Command Line Options (Advanced)

Both the client and listener support the following command line arguments for advanced configuration and troubleshooting:

| Option              | Description                                                      | Example                                 |
|---------------------|------------------------------------------------------------------|-----------------------------------------|
| `--host HOST`       | Set the MQTT broker host (overrides config file)                   | `--host mqtt.example.com`               |
| `--port PORT`       | Set the MQTT broker port (overrides config file)                   | `--port 1883`                           |
| `--keepalive SEC`   | Set the MQTT keepalive interval in seconds (overrides config file) | `--keepalive 30`                        |
| `--transport tcp|websockets` | Set the MQTT transport protocol (overrides config file)         | `--transport websockets`                |
| `--open-config-dir` | Open the folder containing the MQTT config file and exit           | `--open-config-dir`                     |
| `--theme THEME`    | Set the UI theme (e.g., `flatly`, `darkly`) (overrides config file) | `--theme darkly`                        |

- You can combine `--host`, `--port`, `--keepalive`, and `--transport` to update the config file.
- If you use `--open-config-dir` with other options, the config is updated first, then the folder opens.
- If you use command line options, the config is updated and the app does not launch.

**Examples:**

```powershell
# Update broker host, port, and use websockets
presentation-clicker-client --host mqtt.example.com --port 9001 --transport websockets

# Open the config folder
presentation-clicker-client --open-config-dir

# Update config and open the folder
presentation-clicker-client --host mqtt.example.com --open-config-dir
```

The same options are available for `presentation-clicker-listener`.

## Running an MQTT Broker with Docker

You can quickly set up a local MQTT broker using Docker and the provided `docker-compose.yaml` file.

### Steps

1. **Install Docker**  
   Make sure Docker is installed on your system.

2. **Start the Broker**  
   In the project’s `docker` folder, run:
   ```powershell
   cd docker
   docker compose up -d
   ```
   This will start a Mosquitto MQTT broker and optional tunneling services for remote access.

3. **Configuration**  
   - The broker is configured via `mosquitto.conf` in the same folder.
   - By default, ports are not exposed. Uncomment the `ports` section in `docker-compose.yaml` if you want direct access.

4. **Remote Access**  
   - The setup includes Pinggy and Cloudflare Tunnel for exposing the broker to the internet.
   - See comments in `docker-compose.yaml` for usage details.

5. **Stop the Broker**  
   ```powershell
   docker compose down
   ```

## Building Standalone Executables (PyInstaller)

You can build standalone Windows executables for both the client and server using PyInstaller. These builds do not require Python to be installed on the target machine.

### Build Instructions

1. **Install PyInstaller** (if not already installed):
   ```powershell
   pip install pyinstaller
   ```

2. **Run the Build Scripts**
   In the `build_scripts` folder, run the provided PowerShell scripts:
   ```powershell
   cd build_scripts
   
   # Build the client
   .\build_client.ps1

   # Build the server
   .\build_server.ps1
   ```
   Each script will build the application and create a `.zip` file containing the executable and all required files.

3. **Find the Executables**
   The zipped build artifacts will be located in the `build_scripts` folder:
   - `PresentationClickerClient.zip` - Client executable package
   - `PresentationClickerServer.zip` - Server executable package

4. **Download from GitHub Releases**
   Pre-built executables are also available for download from the [GitHub Releases](https://github.com/GameOver94/Presentation-Clicker-Development/releases) page. Download and extract the appropriate `.zip` file for your platform.

> **Note:** The build scripts have been updated for v0.3.0 to work with the new folder structure. The standalone executables include all dependencies and no Python installation is required to run them.

## Requirements
- Python 3.9+
- pipx
- MQTT broker (default: test.mosquitto.org)

## License

MIT License. See [LICENSE.md](LICENSE.md) for details.
