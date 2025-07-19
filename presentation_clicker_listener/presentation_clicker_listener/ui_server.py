"""
ui_server.py
Presentation Clicker Server UI using Tkinter and ttkbootstrap.
Provides a user interface for managing room, users, permissions, and logs.
"""
import argparse
import datetime
import json
import os
import random
import string
import tkinter as tk
from tkinter import ttk
from typing import Optional, Any

import keyboard
import yaml
from presentation_clicker_listener.mqtt_server import PresentationMqttServer
from ttkbootstrap import Style
from ttkbootstrap.constants import PRIMARY, SUCCESS, DANGER

class ServerListenerApp:
    """
    Presentation Clicker Server UI application.
    Handles room management, user permissions, MQTT communication, and log display.
    """
    def __init__(self, mqtt_server: Optional[PresentationMqttServer] = None, theme: str = "flatly", config_path: str = None) -> None:
        """
        Initialize the UI, MQTT server, and callbacks.
        Args:
            mqtt_server: Optional custom MQTT server instance.
            theme: ttkbootstrap theme name.
        """
        self._theme_list = ["flatly", "darkly"]
        self._theme_index = self._theme_list.index(theme) if theme in self._theme_list else 0
        self._config_path = config_path
        self.style: Style = Style(theme=theme)
        self.root: tk.Tk = self.style.master
        self.root.title("Presentation Clicker Server")
        self.root.resizable(False, True)  # Fix width, allow height resize
        self._set_fonts()
        self.connected_users: dict[str, Any] = {}
        self.mqtt: PresentationMqttServer = mqtt_server or PresentationMqttServer()
        self.mqtt.on_connect    = self._on_mqtt_connect
        self.mqtt.on_disconnect = self._on_mqtt_disconnect
        self.mqtt.on_message    = self._on_mqtt_message
        self._create_widgets()
        self._layout_widgets()
        self._generate_room()
        self._generate_pwd()

    def _set_fonts(self) -> None:
        """Set fonts: default, monospace for log, and icon font for icons."""
        self.font_mono = ("Courier New", 9)
        self.font_icon = ("Segoe MDL2 Assets", 12)
        self.style.configure("Icon.TButton", font=self.font_icon)

    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        # Make Treeview headers bold
        self.style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))

        self.frm_top: ttk.Frame = ttk.Frame(self.root)
        self.frm_connect: ttk.LabelFrame = ttk.LabelFrame(
            self.frm_top, text="Connection",
            padding=(10,10), bootstyle="primary")
        self.lbl_room: ttk.Label = ttk.Label(self.frm_connect, text="Room Code:")
        self.ent_room: ttk.Entry = ttk.Entry(self.frm_connect, width=20)
        misc_icons = self._get_misc_icons()
        self.btn_gen_room: ttk.Button = ttk.Button(self.frm_connect, text=misc_icons['generate'], width=4, command=self._generate_room, style="Icon.TButton")
        self.btn_copy_room: ttk.Button = ttk.Button(self.frm_connect, text=misc_icons['copy'], width=4, command=lambda: self._copy_from_entry(self.ent_room), style="Icon.TButton")
        self.lbl_pwd: ttk.Label  = ttk.Label(self.frm_connect, text="Password:")
        self.ent_pwd: ttk.Entry  = ttk.Entry(self.frm_connect, width=20)
        self.btn_gen_pwd: ttk.Button = ttk.Button(self.frm_connect, text=misc_icons['generate'], width=4, command=self._generate_pwd, style="Icon.TButton")
        self.btn_copy_pwd: ttk.Button = ttk.Button(self.frm_connect, text=misc_icons['copy'], width=4, command=lambda: self._copy_from_entry(self.ent_pwd), style="Icon.TButton")
        self.frm_connect_btns: ttk.Frame = ttk.Frame(self.frm_connect)
        self.btn_connect: ttk.Button = ttk.Button(
            self.frm_connect_btns, text="Connect", bootstyle="success-outline",
            width=15, command=self.on_connect)
        self.btn_disconnect: ttk.Button = ttk.Button(
            self.frm_connect_btns, text="Disconnect", bootstyle="danger-outline",
            width=15, state=tk.DISABLED, command=self.on_disconnect)
        self.style.configure("Treeview.Heading")
        self.frm_users: ttk.LabelFrame = ttk.LabelFrame(
            self.frm_top, text="Connected Users",
            padding=(10,10), bootstyle="secondary")
        self.user_rows: dict[str, dict[str, Any]] = {}
        self.tree_users: ttk.Treeview = ttk.Treeview(self.frm_users, columns=("name", "nav", "control"), show="headings", height=10)
        self.tree_users.heading("name", text="User", anchor=tk.W)
        self.tree_users.heading("nav", text="Navigation", anchor=tk.CENTER)
        self.tree_users.heading("control", text="Control", anchor=tk.CENTER)
        self.tree_users.column("name", width=150, anchor=tk.W)
        self.tree_users.column("nav", width=100, anchor=tk.CENTER)
        self.tree_users.column("control", width=100, anchor=tk.CENTER)
        self.scr_users: ttk.Scrollbar = ttk.Scrollbar(self.frm_users, orient=tk.VERTICAL, command=self.tree_users.yview)
        self.tree_users.configure(yscrollcommand=self.scr_users.set)
        self.tree_users.bind('<Button-1>', self.on_treeview_click)
        self.frm_bottom: ttk.Frame = ttk.Frame(self.root, padding=(5))
        self.frm_log: ttk.LabelFrame = ttk.LabelFrame(
            self.frm_bottom, text="Log", padding=(10,10), bootstyle="secondary")
        self.txt_log: tk.Text = tk.Text(
            self.frm_log, font=self.font_mono, wrap="none",
            state=tk.DISABLED, bg=self.style.colors.bg, relief=tk.SOLID, height=10)
        self.scr_log: ttk.Scrollbar = ttk.Scrollbar(
            self.frm_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log['yscrollcommand'] = self.scr_log.set
        # Add Switch Theme button with emoji
        self.btn_switch_theme: ttk.Button = ttk.Button(
            self.frm_connect,
            text=self._get_theme_icon(),
            width=3,
            command=self._switch_theme,
            style="Icon.TButton"
        )

    def _layout_widgets(self) -> None:
        """Lay out all widgets in the UI."""
        pad = dict(padx=5, pady=5)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.frm_top.grid(row=0, column=0, sticky="ew", **pad)
        self.frm_top.columnconfigure(0, weight=1)
        self.frm_top.columnconfigure(1, weight=2)
        self.frm_connect.grid(row=0, column=0, sticky="nsew", **pad)
        self.frm_users.grid(row=0, column=1, sticky="nsew", **pad)
        self.frm_connect.rowconfigure(0, weight=0)
        self.frm_connect.rowconfigure(1, weight=0)
        self.frm_connect.rowconfigure(2, weight=1)
        self.frm_connect.columnconfigure(0, weight=0)
        self.frm_connect.columnconfigure(1, weight=1)
        self.frm_connect.columnconfigure(2, weight=0)
        self.frm_connect.columnconfigure(3, weight=0)
        self.lbl_room.grid( row=0, column=0, sticky="se", **pad)
        self.ent_room.grid( row=0, column=1, sticky="sw", **pad)
        self.btn_gen_room.grid(row=0, column=2, sticky="sw", **pad)
        self.btn_copy_room.grid(row=0, column=3, sticky="sw", **pad)
        self.lbl_pwd.grid(  row=1, column=0, sticky="ne", **pad)
        self.ent_pwd.grid(  row=1, column=1, sticky="nw", **pad)
        self.btn_gen_pwd.grid(row=1, column=2, sticky="nw", **pad)
        self.btn_copy_pwd.grid(row=1, column=3, sticky="nw", **pad)
        self.frm_connect_btns.grid(row=2, column=0, columnspan=4, sticky="se")
        self.btn_connect.grid(row=0, column=0, padx=5, pady=5)
        self.btn_disconnect.grid(row=0, column=1, padx=5, pady=5)
        self.tree_users.grid(row=0, column=0, sticky="nsew")
        self.scr_users.grid(row=0, column=1, sticky="ns")
        self.frm_users.rowconfigure(0, weight=1)
        self.frm_users.columnconfigure(0, weight=1)
        self.frm_bottom.grid(row=1, column=0, sticky="nsew", **pad)
        self.frm_bottom.rowconfigure(0, weight=1)
        self.frm_bottom.columnconfigure(0, weight=1)
        self.frm_log.grid(row=0, column=0, sticky="nsew")
        self.frm_log.rowconfigure(0, weight=1)
        self.frm_log.columnconfigure(0, weight=1)
        self.txt_log.grid(row=0, column=0, sticky="nsew")
        self.scr_log.grid(row=0, column=1, sticky="ns")
        # Place the switch theme button in the connection frame
        self.btn_switch_theme.grid(row=2, column=0, sticky="sw", **pad)

    # ─── UI ↔ MQTT Glue ─────────────────────────────────────────────────

    def on_connect(self) -> None:
        """
        Handle connect button click. Validates input and connects via MQTT.
        """
        room: str = self.ent_room.get().strip()
        pwd: str = self.ent_pwd.get().strip()
        if not (room and pwd):
            self._log("ERROR: Room code and password required.")
            return
        self._log(f"Connecting as server for room '{room}'…")
        try:
            self.mqtt.connect(room, pwd)
        except TimeoutError as e:
            self._log(f"ERROR: {e}")

    def on_disconnect(self) -> None:
        """
        Handle disconnect button click. Disconnects from MQTT.
        """
        self._log("Disconnecting server…")
        self.mqtt.disconnect()

    def on_treeview_click(self, event: Any) -> None:
        """
        Handle click on the user permissions treeview to toggle permissions.
        Args:
            event: Tkinter event object.
        """
        region = self.tree_users.identify('region', event.x, event.y)
        if region != 'cell':
            return
        rowid = self.tree_users.identify_row(event.y)
        col = self.tree_users.identify_column(event.x)
        if not rowid or col not in ('#2', '#3'):
            return
        user = self.tree_users.item(rowid, 'values')[0]
        if user not in self.user_rows:
            return
        if col == '#2':
            self.user_rows[user]["nav"] = not self.user_rows[user]["nav"]
        elif col == '#3':
            self.user_rows[user]["control"] = not self.user_rows[user]["control"]
        self._update_user(user, self.user_rows[user]["nav"], self.user_rows[user]["control"])
        self._log(f"Permission changed for {user}: nav={self.user_rows[user]['nav']}, control={self.user_rows[user]['control']}")

    def _set_title_with_server(self):
        """
        Set the window title to include the connected MQTT server host and port.
        """
        host = self.mqtt.config.get('host', 'unknown')
        port = self.mqtt.config.get('port', 'unknown')
        self.root.title(f"Presentation Clicker Server - MQTT: {host}:{port}")

    def _on_mqtt_connect(self) -> None:
        """
        MQTT callback: connected. Enables/disables UI elements.
        """
        self.root.after(0, lambda: (self._set_connected(True), self._set_title_with_server()))

    def _on_mqtt_disconnect(self) -> None:
        """
        MQTT callback: disconnected. Enables/disables UI elements.
        """
        self.root.after(0, lambda: (self._set_connected(False), self.root.title("Presentation Clicker Server")))

    def _on_mqtt_message(self, topic: str, payload: str) -> None:
        """
        MQTT callback: message received. Handles user status and actions.
        Args:
            topic: MQTT topic string.
            payload: Decrypted message payload.
        """
        self.root.after(0, lambda: self._handle_message(topic, payload))

    def _handle_message(self, topic: str, payload: str) -> None:
        """
        Handle incoming MQTT messages for user status and presentation actions.
        Args:
            topic: MQTT topic string.
            payload: Decrypted message payload.
        """
        try:
            data = json.loads(payload)
        except Exception:
            self._log(f"Malformed message: {payload}")
            return
        if topic.endswith("/status"):
            user = data.get("user")
            status = data.get("status")
            if status == "online":
                self._update_user(user, nav=True, control=False)
            elif status == "offline":
                if user in self.user_rows:
                    self.tree_users.delete(self.user_rows[user]["iid"])
                    del self.user_rows[user]
            self._log(f"User '{user}' is now {status}.")
        elif topic.endswith("/presentation"):
            user = data.get("user")
            action = data.get("action")
            perms = self.user_rows.get(user, {})
            allowed = False
            if action in ("next", "previous") and perms.get("nav"):
                allowed = True
                if action == "next":
                    keyboard.send("right")
                elif action == "previous":
                    keyboard.send("left")
            elif action in ("start", "end", "blackout") and perms.get("control"):
                allowed = True
                if action == "start":
                    keyboard.send(["shift", "f5"])
                elif action == "end":
                    keyboard.send("esc")
                elif action == "blackout":
                    keyboard.send("b")
            if allowed:
                self._log(f"Action '{action}' from '{user}' allowed and executed.")
            else:
                self._log(f"Action '{action}' from '{user}' denied (insufficient permissions).")

    def _set_connected(self, is_connected: bool) -> None:
        """
        Enable/disable UI elements based on connection state.
        Args:
            is_connected: True if connected, False otherwise.
        """
        self.btn_disconnect.config(state=tk.NORMAL if is_connected else tk.DISABLED)
        self.btn_connect.config(state=tk.DISABLED if is_connected else tk.NORMAL)
        entry_state: str = tk.DISABLED if is_connected else tk.NORMAL
        self.ent_room.config(state=entry_state)
        self.ent_pwd.config(state=entry_state)
        btn_state: str = tk.DISABLED if is_connected else tk.NORMAL
        self.btn_gen_room.config(state=btn_state)
        self.btn_gen_pwd.config(state=btn_state)
        self._log("Connected ✅" if is_connected else "Disconnected ❌")

    def _update_user(self, user: str, nav: bool = False, control: bool = False) -> None:
        """
        Add or update a user in the treeview with permission toggles.
        Args:
            user: Username string.
            nav: Navigation permission.
            control: Control permission.
        """
        nav_disp = '✔' if nav else '✖'
        control_disp = '✔' if control else '✖'
        if user in self.user_rows:
            iid = self.user_rows[user]["iid"]
            self.tree_users.item(iid, values=(user, nav_disp, control_disp))
            self.user_rows[user]["nav"] = nav
            self.user_rows[user]["control"] = control
        else:
            iid = self.tree_users.insert('', 'end', values=(user, nav_disp, control_disp))
            self.user_rows[user] = {"iid": iid, "nav": nav, "control": control}

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

    def _generate_room(self) -> None:
        """
        Generate a random room code and insert it into the entry.
        """
        code: str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.ent_room.delete(0, tk.END)
        self.ent_room.insert(0, code)

    def _generate_pwd(self) -> None:
        """
        Generate a random password and insert it into the entry.
        """
        pwd: str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        self.ent_pwd.delete(0, tk.END)
        self.ent_pwd.insert(0, pwd)

    def _copy_from_entry(self, entry: ttk.Entry) -> None:
        """
        Copy the value from an entry widget to the clipboard.
        Args:
            entry: Entry widget.
        """
        value: str = entry.get()
        self.root.clipboard_clear()
        self.root.clipboard_append(value)

    def _get_theme_icon(self) -> str:
        """Return the icon for the current theme (☀️ for light, 🌛 for dark) using Segoe MDL2 Assets (E706 for sun, E708 for moon)."""
        return "\uE706" if self._theme_list[self._theme_index] == "flatly" else "\uE708"

    def _get_misc_icons(self):
        """Return a dict of icons using Segoe MDL2 Assets Unicode."""
        return {
            'copy': "\uE8C8",      # Copy
            'generate': "\uE72C",  # Refresh
        }

    def _switch_theme(self):
        self._theme_index = (self._theme_index + 1) % len(self._theme_list)
        new_theme = self._theme_list[self._theme_index]
        self.style.theme_use(new_theme)
        # Re-apply icon font style after theme change
        self.style.configure("Icon.TButton", font=self.font_icon)
        # Re-apply bold font for Treeview headers
        self.style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))
        # Re-apply monospace font for log (if needed)
        self.txt_log.configure(font=self.font_mono)
        self.btn_switch_theme.config(text=self._get_theme_icon())
        # Save theme to config
        if self._config_path:
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            except Exception:
                config = {}
            config['theme'] = new_theme
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f)

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

def main():
    parser = argparse.ArgumentParser(description="Presentation Clicker Server UI")
    parser.add_argument('--host', type=str, help='MQTT broker host')
    parser.add_argument('--port', type=int, help='MQTT broker port (1-65535)')
    parser.add_argument('--keepalive', type=int, help='MQTT keepalive interval (positive integer)')
    parser.add_argument('--open-config-dir', action='store_true', help='Open the folder containing the config file and exit')
    parser.add_argument('--transport', type=str, choices=['tcp', 'websockets'], help='MQTT transport: tcp or websockets')
    parser.add_argument('--theme', type=str, help='UI theme (e.g., flatly, darkly)')
    args = parser.parse_args()

    config_path = os.path.join(os.path.dirname(__file__), 'mqtt_config.yaml')
    config_dir = os.path.dirname(config_path)

    # Load config to get theme (if present)
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
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
    app = ServerListenerApp(theme=theme, config_path=config_path)
    app.run()

if __name__ == "__main__":
    main()
