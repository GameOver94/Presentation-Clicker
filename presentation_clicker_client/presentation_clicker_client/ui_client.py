"""
ui_client.py
Presentation Clicker Client UI using Tkinter and ttkbootstrap.
Provides a user interface for connecting to the server, sending navigation commands, and viewing logs.
"""
import argparse
import datetime
import json
import os
import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
from ttkbootstrap.constants import PRIMARY, SUCCESS, DANGER
from presentation_clicker_client.mqtt_client import PresentationMqttClient
from typing import Optional

class PresentationClickerApp:
    """
    Presentation Clicker Client UI application.
    Handles user input, MQTT communication, and log display.
    """
    def __init__(self, mqtt_client: Optional[PresentationMqttClient] = None, theme: str = "flatly", config_path: str = None) -> None:
        """
        Initialize the UI, MQTT client, and callbacks.
        Args:
            mqtt_client: Optional custom MQTT client instance.
            theme: ttkbootstrap theme name.
            config_path: Path to config file for saving theme.
        """
        self._theme_list = ["flatly", "darkly"]
        self._theme_index = self._theme_list.index(theme) if theme in self._theme_list else 0
        self._config_path = config_path
        # --- Theming & root ---
        self.style: Style = Style(theme=theme)
        self.root: tk.Tk = self.style.master
        self.root.title("Presentation Clicker")
        self.root.resizable(False, True)  # Fix width, allow height resize
        self._set_fonts()

        # --- MQTT setup & callbacks ---
        self.mqtt: PresentationMqttClient = mqtt_client or PresentationMqttClient()
        self.mqtt.on_connect    = self._on_mqtt_connect
        self.mqtt.on_disconnect = self._on_mqtt_disconnect
        self.mqtt.on_publish    = self._on_mptt_publish
        self.mqtt.on_message    = self._on_mqtt_message

        # --- build UI ---
        self._create_widgets()
        self._layout_widgets()

    def _set_fonts(self) -> None:
        """Set fonts: default, monospace for log, and icon font for icons."""
        self.font_mono = ("Consolas, Courier New, monospace", 9)
        self.font_icon = ("Segoe MDL2 Assets", 12)
        # Define a custom style for icon buttons
        self.style.configure("Icon.TButton", font=self.font_icon)

    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        # -- Top frame: contains Connection & Navigation --
        self.frm_top: ttk.Frame = ttk.Frame(self.root)
        # ── Top left frame: Connection ──
        self.frm_connect: ttk.LabelFrame = ttk.LabelFrame(
            self.frm_top, text="Connection",
            padding=(10,10), bootstyle="primary")
        # -- Top right frame: Navigation --
        self.frm_nav: ttk.LabelFrame = ttk.LabelFrame(
            self.frm_top, text="Navigation",
            padding=(10,10), bootstyle="secondary"
        )
        # get misc icons for buttons
        misc_icons = self._get_misc_icons()
        # Connection inputs
        self.lbl_name: ttk.Label = ttk.Label(self.frm_connect, text="Display Name:")
        self.ent_name: ttk.Entry = ttk.Entry(self.frm_connect, width=26)
        self.lbl_room: ttk.Label = ttk.Label(self.frm_connect, text="Room Code:")
        self.ent_room: ttk.Entry = ttk.Entry(self.frm_connect, width=15)
        self.btn_paste_room: ttk.Button = ttk.Button(self.frm_connect, text=misc_icons['paste'], width=4, style="Icon.TButton", command=lambda: self._paste_to_entry(self.ent_room))
        self.lbl_pwd: ttk.Label  = ttk.Label(self.frm_connect, text="Password:")
        self.ent_pwd: ttk.Entry  = ttk.Entry(self.frm_connect, width=15, show="*")
        self.btn_paste_pwd: ttk.Button = ttk.Button(self.frm_connect, text=misc_icons['paste'], width=4, style="Icon.TButton", command=lambda: self._paste_to_entry(self.ent_pwd))
        # Connect / Disconnect
        self.btn_connect: ttk.Button = ttk.Button(
            self.frm_connect, text="Connect", bootstyle="success-outline",
            width=12, command=self.on_connect)
        self.btn_disconnect: ttk.Button = ttk.Button(
            self.frm_connect, text="Disconnect", bootstyle="danger-outline",
            width=12, state=tk.DISABLED, command=self.on_disconnect)
        # Navigation
        nav_bs = dict(bootstyle="info", width=4, state=tk.DISABLED, style="Icon.TButton")
        self.btn_prev     = ttk.Button(self.frm_nav, text=misc_icons['prev'],   command=self.on_prev,     **nav_bs)
        self.btn_next     = ttk.Button(self.frm_nav, text=misc_icons['next'],   command=self.on_next,     **nav_bs)
        self.btn_start    = ttk.Button(self.frm_nav, text=misc_icons['start'],  command=self.on_start,    **nav_bs)
        self.btn_end      = ttk.Button(self.frm_nav, text=misc_icons['end'],    command=self.on_end,      **nav_bs)
        self.btn_blackout = ttk.Button(self.frm_nav, text=misc_icons['blackout'], command=self.on_blackout, **nav_bs)
        # ── Bottom frame: Log ──
        self.frm_bottom: ttk.Frame = ttk.Frame(self.root, padding=(5))
        self.frm_log: ttk.LabelFrame = ttk.LabelFrame(
            self.frm_bottom, text="Log", padding=(10,10), bootstyle="secondary")
        self.txt_log: tk.Text = tk.Text(
            self.frm_log, font=self.font_mono, wrap="none",
            state=tk.DISABLED, bg=self.style.colors.bg, relief=tk.SOLID, height=10)
        self.scr_log: ttk.Scrollbar = ttk.Scrollbar(
            self.frm_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log['yscrollcommand'] = self.scr_log.set
        # Add Switch Theme button with icon
        self.btn_switch_theme = ttk.Button(
            self.frm_nav,
            text=self._get_theme_icon(),
            width=3,
            command=self._switch_theme,
            style="Icon.TButton"
        )

    def _layout_widgets(self) -> None:
        """Lay out all widgets in the UI."""
        pad = dict(padx=5, pady=5)
        # root grid
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        # top frame
        self.frm_top.grid(row=0, column=0, sticky="ew", **pad)
        self.frm_top.columnconfigure(0, weight=1)
        self.frm_top.columnconfigure(1, weight=1)
        # connection and navigation frames side by side
        self.frm_connect.grid(row=0, column=0, sticky="nsew", **pad)
        self.frm_nav.grid(row=0, column=1, sticky="nsew", **pad)
        # connection fields
        self.lbl_name.grid( row=0, column=0, sticky="e", **pad)
        self.ent_name.grid( row=0, column=1, columnspan=2, sticky="w", **pad)
        self.lbl_room.grid( row=1, column=0, sticky="e", **pad)
        self.ent_room.grid( row=1, column=1, sticky="w", **pad)
        self.btn_paste_room.grid(row=1, column=2, sticky="w", **pad)
        self.lbl_pwd.grid(  row=2, column=0, sticky="e", **pad)
        self.ent_pwd.grid(  row=2, column=1, sticky="w", **pad)
        self.btn_paste_pwd.grid(row=2, column=2, sticky="w", **pad)
        self.btn_connect.grid(    row=1, column=3, **pad)
        self.btn_disconnect.grid( row=2, column=3, **pad)
        # navigation frame grid
        self.frm_nav.rowconfigure(2, weight=1)
        # navigation buttons in frm_nav
        self.btn_prev.    grid(row=1, column=0, **pad)
        self.btn_next.    grid(row=1, column=1, **pad)
        self.btn_start.   grid(row=0, column=0, **pad)
        self.btn_end.     grid(row=0, column=1, **pad)
        self.btn_blackout.grid(row=0, column=2, **pad)
        # log outer frame
        self.frm_bottom.grid(row=1, column=0, sticky="nsew", **pad)
        self.frm_bottom.rowconfigure(0, weight=1)
        self.frm_bottom.columnconfigure(0, weight=1)
        # log frame inside outer
        self.frm_log.grid(row=0, column=0, sticky="nsew")
        self.frm_log.rowconfigure(0, weight=1)
        self.frm_log.columnconfigure(0, weight=1)
        self.txt_log.grid(row=0, column=0, sticky="nsew")
        self.scr_log.grid(row=0, column=1, sticky="ns")
        # Switch theme button
        self.btn_switch_theme.grid(row=2, column=3, sticky="se", **pad)

    def _get_theme_icon(self) -> str:
        """Return the icon for the current theme using Segoe MDL2 Assets (E706 for sun, E708 for moon)."""
        return "\uE706" if self._theme_list[self._theme_index] == "flatly" else "\uE708"

    def _get_misc_icons(self):
        """Return a dict of navigation icons using Segoe MDL2 Assets Unicode."""
        return {
            'prev': "\uE100",    # Chevron Left
            'next': "\uE101",    # Chevron Right
            'start': "\uE768",   # Play
            'end': "\uE71A",     # Stop
            'blackout': "\uE890", # View
            'paste': "\uE77F"  # Paste
        }

    # ─── UI ↔ MQTT Glue ─────────────────────────────────────────────────

    def on_connect(self) -> None:
        """
        Handle connect button click. Validates input and connects via MQTT.
        """
        user: str = self.ent_name.get().strip()
        room: str = self.ent_room.get().strip()
        pwd: str  = self.ent_pwd.get().strip()
        if not (user and room and pwd):
            self._log("ERROR: All fields required.")
            return
        self._log(f"Connecting as '{user}'…")
        try:
            self.mqtt.connect(user, room, pwd)
        except TimeoutError as e:
            self._log(f"ERROR: {e}")

    def on_disconnect(self) -> None:
        """
        Handle disconnect button click. Disconnects from MQTT.
        """
        self._log("Disconnecting…")
        self.mqtt.disconnect()

    def on_prev(self) -> None:
        """
        Send 'previous' action to server.
        """
        self.mqtt.publish_action("previous")
    def on_next(self) -> None:
        """
        Send 'next' action to server.
        """
        self.mqtt.publish_action("next")
    def on_start(self) -> None:
        """
        Send 'start' action to server.
        """
        self.mqtt.publish_action("start")
    def on_end(self) -> None:
        """
        Send 'end' action to server.
        """
        self.mqtt.publish_action("end")
    def on_blackout(self) -> None:
        """
        Send 'blackout' action to server.
        """
        self.mqtt.publish_action("blackout")

    # MQTT client callbacks
    def _set_title_with_server(self):
        """
        Set the window title to include the connected MQTT server host and port.
        """
        host = self.mqtt.config.get('host', 'unknown')
        port = self.mqtt.config.get('port', 'unknown')
        self.root.title(f"Presentation Clicker - MQTT: {host}:{port}")

    def _on_mqtt_connect(self) -> None:
        """
        MQTT callback: connected. Enables navigation and disables input fields.
        """
        self.root.after(0, lambda: (self._set_connected(True), self._set_title_with_server()))

    def _on_mqtt_disconnect(self) -> None:
        """
        MQTT callback: disconnected. Disables navigation and enables input fields.
        """
        self.root.after(0, lambda: (self._set_connected(False), self.root.title("Presentation Clicker")))
        
    def _on_mptt_publish(self, topic: str, payload: str) -> None:
        """
        MQTT callback: message published. Logs outgoing messages.
        """
        self.root.after(0, lambda: self._log(f"[SENT] {topic}: {payload}"))

    def _on_mqtt_message(self, topic: str, payload: str) -> None:
        """
        MQTT callback: message received. Logs incoming messages.
        """
        self.root.after(0, lambda: self._log(f"[RCV] {topic}: {payload}"))

    # ─── Helpers ────────────────────────────────────────────────────────

    def _set_connected(self, is_connected: bool) -> None:
        """
        Enable/disable navigation and input fields based on connection state.
        Args:
            is_connected: True if connected, False otherwise.
        """
        state: str = tk.NORMAL if is_connected else tk.DISABLED
        for btn in (self.btn_prev, self.btn_next,
                    self.btn_start, self.btn_end,
                    self.btn_blackout):
            btn.config(state=state)
        self.btn_disconnect.config(state=state)
        self.btn_connect.config(state=tk.DISABLED if is_connected else tk.NORMAL)
        entry_state: str = tk.DISABLED if is_connected else tk.NORMAL
        self.ent_name.config(state=entry_state)
        self.ent_room.config(state=entry_state)
        self.ent_pwd.config(state=entry_state)
        self._log("Connected ✅" if is_connected else "Disconnected ❌")

    def _log(self, msg: str) -> None:
        """
        Append a timestamped message to the log window.
        Args:
            msg: Message string.
        """
        timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert("end", f"[{timestamp}] {msg}\n")
        self.txt_log.see("end")
        self.txt_log.config(state=tk.DISABLED)

    def _paste_to_entry(self, entry: ttk.Entry) -> None:
        """
        Paste clipboard contents into a given entry widget.
        Args:
            entry: Entry widget.
        """
        try:
            entry.delete(0, tk.END)
            entry.insert(0, self.root.clipboard_get())
        except tk.TclError:
            pass

    def _switch_theme(self):
        """Toggle between light and dark themes and save to config. Update icon and re-apply icon font style."""
        self._theme_index = (self._theme_index + 1) % len(self._theme_list)
        new_theme = self._theme_list[self._theme_index]
        self.style.theme_use(new_theme)
        # Re-apply icon font style after theme change
        self.style.configure("Icon.TButton", font=self.font_icon)
        # Re-apply monospace font for log
        self.txt_log.configure(font=self.font_mono)
        # Update button icon
        self.btn_switch_theme.config(text=self._get_theme_icon())
        # Save theme to config
        if self._config_path:
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception:
                config = {}
            config['theme'] = new_theme
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

    def run(self) -> None:
        """
        Start the Tkinter main loop.
        """
        self.root.mainloop()

def update_mqtt_config(config_path, host=None, port=None, keepalive=None, transport=None, theme=None):
    """
    Update the MQTT config file with provided values.
    """
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
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
            json.dump(config, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Presentation Clicker Client UI")
    parser.add_argument('--host', type=str, help='MQTT broker host')
    parser.add_argument('--port', type=int, help='MQTT broker port (1-65535)')
    parser.add_argument('--keepalive', type=int, help='MQTT keepalive interval (positive integer)')
    parser.add_argument('--open-config-dir', action='store_true', help='Open the folder containing the config file and exit')
    parser.add_argument('--transport', type=str, choices=['tcp', 'websockets'], help='MQTT transport: tcp or websockets')
    parser.add_argument('--theme', type=str, help='UI theme (e.g., flatly, darkly)')
    args = parser.parse_args()

    # Fixed config file path (relative to this file)
    config_path = os.path.join(os.path.dirname(__file__), 'mqtt_config.json')
    config_dir = os.path.dirname(config_path)

    # Load config to get theme (if present)
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            pass
    theme = args.theme or config.get('theme', 'flatly')

    # Validate arguments
    if args.host is not None and (not isinstance(args.host, str) or not args.host.strip()):
        print("Error: --host must be a non-empty string.")
        return
    if args.port is not None:
        if not (1 <= args.port <= 65535):
            print("Error: --port must be an integer between 1 and 65535.")
            return
    if args.keepalive is not None:
        if args.keepalive <= 0:
            print("Error: --keepalive must be a positive integer.")
            return
    if args.transport is not None and args.transport not in ('tcp', 'websockets'):
        print("Error: --transport must be 'tcp' or 'websockets'.")
        return

    # If any config argument is provided, update config
    config_changed = False
    if args.host is not None or args.port is not None or args.keepalive is not None or args.transport is not None or args.theme is not None:
        update_mqtt_config(config_path, args.host, args.port, args.keepalive, args.transport, theme=args.theme)
        print(f"Config updated: {config_path}")
        config_changed = True

    # If --open-config-dir is provided, open the folder and exit
    if args.open_config_dir:
        os.startfile(config_dir)
        return

    # If config was changed, exit (do not launch app)
    if config_changed:
        return

    # Otherwise, launch the app
    app = PresentationClickerApp(theme=theme, config_path=config_path)
    app.run()

if __name__ == "__main__":
    main()