"""
ui_server.py
Presentation Clicker Server UI using Tkinter and ttkbootstrap.
Provides a user interface for managing room, users, permissions, and logs.
"""
import datetime
import json
import os
import random
import string
import tkinter as tk
from tkinter import ttk
from typing import Optional, Any

import keyboard
from presentation_clicker_listener.mqtt_server import PresentationMqttServer
from ttkbootstrap import Style
from ttkbootstrap.constants import PRIMARY, SUCCESS, DANGER
from presentation_clicker_common import (
    ThemeManager, get_misc_icons, create_common_parser, validate_args, 
    load_theme_from_config, handle_config_operations, UILogger
)

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
        self.style: Style = Style(theme=theme)
        self.root: tk.Tk = self.style.master
        self.root.title("Presentation Clicker Server")
        self.root.resizable(False, True)  # Fix width, allow height resize
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(
            theme_list=["flatly", "darkly"], 
            initial_theme=theme, 
            config_path=config_path
        )
        self.theme_manager.set_style(self.style)
        
        self._set_fonts()
        self.connected_users: dict[str, Any] = {}
        self.mqtt: PresentationMqttServer = mqtt_server or PresentationMqttServer()
        self.mqtt.on_connect    = self._on_mqtt_connect
        self.mqtt.on_disconnect = self._on_mqtt_disconnect
        self.mqtt.on_message    = self._on_mqtt_message
        self._create_widgets()
        
        # Initialize logger after widgets are created
        self.logger = UILogger(self.txt_log, self.theme_manager)
        self.logger.set_user_color_function(self._get_user_color)
        
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
        misc_icons = get_misc_icons()
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
            text=self.theme_manager.get_theme_icon(),
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
                self._log(f"User '{user}' is now online.", user=user)
            elif status == "offline":
                if user in self.user_rows:
                    self.tree_users.delete(self.user_rows[user]["iid"])
                    del self.user_rows[user]
                self._log(f"User '{user}' is now offline.", user=user)
            elif status == "connection_lost":
                if user in self.user_rows:
                    self.tree_users.delete(self.user_rows[user]["iid"])
                    del self.user_rows[user]
                self._log(f"User '{user}' connection lost (unexpected disconnect).", user=user)
            else:
                self._log(f"User '{user}' status: {status}.", user=user)
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
                self._log(f"Action '{action}' from '{user}' allowed and executed.", user=user)
            else:
                self._log(f"Action '{action}' from '{user}' denied (insufficient permissions).", user=user)

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

    def _is_dark_theme(self):
        """Detect if the current theme is dark based on the background color luminance."""
        return self.theme_manager.is_dark_theme()

    def _get_user_colors(self):
        """Return a list of 8 distinct pastel colors for users, responsive to theme."""
        # Pastel colors for light theme
        pastel_light = [
            "#ffd6e0", # pink
            "#ffe7c2", # peach
            "#fffac2", # yellow
            "#d6ffd6", # mint
            "#c2f0ff", # blue
            "#e0d6ff", # lavender
            "#ffd6fa", # magenta
            "#d6fff6"  # aqua
        ]
        # Darker versions for dark theme
        pastel_dark = [
            "#b85c6e", # dark pink
            "#b88a4a", # dark peach
            "#b8b04a", # dark yellow
            "#4ab85c", # dark mint
            "#4a8ab8", # dark blue
            "#6e4ab8", # dark lavender
            "#b84ab0", # dark magenta
            "#4ab8b0"  # dark aqua
        ]
        return pastel_dark if self._is_dark_theme() else pastel_light

    def _get_user_color(self, user):
        """Get a distinct color for a user from the color list."""
        colors = self._get_user_colors()
        idx = abs(hash(user)) % len(colors)
        return colors[idx]

    def _update_user(self, user: str, nav: bool = False, control: bool = False) -> None:
        """
        Add or update a user in the treeview with permission toggles and distinct background color.
        Args:
            user: Username string.
            nav: Navigation permission.
            control: Control permission.
        """
        nav_disp = '✔' if nav else '✖'
        control_disp = '✔' if control else '✖'
        user_color = self._get_user_color(user)
        tag_name = f"user_{user}"
        self.tree_users.tag_configure(tag_name, background=user_color)
        if user in self.user_rows:
            iid = self.user_rows[user]["iid"]
            self.tree_users.item(iid, values=(user, nav_disp, control_disp), tags=(tag_name,))
            self.user_rows[user]["nav"] = nav
            self.user_rows[user]["control"] = control
        else:
            iid = self.tree_users.insert('', 'end', values=(user, nav_disp, control_disp), tags=(tag_name,))
            self.user_rows[user] = {"iid": iid, "nav": nav, "control": control}

    def _log(self, msg: str, user: str = None) -> None:
        """
        Append a timestamped message to the log window, with optional user color.
        Args:
            msg: Message string.
            user: Username string (optional, for color).
        """
        self.logger.log(msg, user=user)

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
        return self.theme_manager.get_theme_icon()

    def _get_misc_icons(self):
        """Return a dict of icons using Segoe MDL2 Assets Unicode."""
        return get_misc_icons()

    def _switch_theme(self):
        new_theme = self.theme_manager.switch_theme()
        # Re-apply icon font style after theme change
        self.style.configure("Icon.TButton", font=self.font_icon)
        # Re-apply bold font for Treeview headers
        self.style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))
        # Re-apply monospace font for log (if needed)
        self.txt_log.configure(font=self.font_mono)
        self.btn_switch_theme.config(text=self.theme_manager.get_theme_icon())
        # Update user row colors for new theme
        for user in self.user_rows:
            tag_name = f"user_{user}"
            user_color = self._get_user_color(user)
            self.tree_users.tag_configure(tag_name, background=user_color)
        # Update log tag colors for new theme using the logger
        self.logger.update_theme_colors()

    def run(self) -> None:
        """
        Start the Tkinter main loop.
        """
        self.root.mainloop()

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'mqtt_config.yaml')
    
    # Create parser and validate arguments
    parser = create_common_parser("Presentation Clicker Server UI")
    args = parser.parse_args()
    
    if not validate_args(args):
        return
    
    # Load theme from config or use provided theme
    theme = args.theme or load_theme_from_config(config_path, "flatly")
    
    # Handle config operations
    config_changed, should_exit = handle_config_operations(args, config_path, theme)
    if should_exit:
        return
    
    # Launch the app
    app = ServerListenerApp(theme=theme, config_path=config_path)
    app.run()

if __name__ == "__main__":
    main()
