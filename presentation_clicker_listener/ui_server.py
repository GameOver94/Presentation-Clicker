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
from mqtt_server import PresentationMqttServer
from ttkbootstrap import Style
from ttkbootstrap.constants import PRIMARY, SUCCESS, DANGER
from presentation_clicker_common import (
    BaseApp, create_main_function, get_misc_icons, UILogger
)


class ServerListenerApp(BaseApp):
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
            config_path: Path to config file for saving theme.
        """
        super().__init__("Presentation Clicker Server", theme, config_path)
        
        self.connected_users: dict[str, Any] = {}
        self.mqtt: PresentationMqttServer = mqtt_server or PresentationMqttServer()
        self._setup_mqtt_callbacks()
        
        self._create_widgets()
        
        # Initialize logger after widgets are created
        self.logger = UILogger(self.txt_log, self.theme_manager)
        self.logger.set_user_color_function(self._get_user_color)
        
        self._layout_widgets()
        self._generate_room()
        self._generate_pwd()

    def _setup_mqtt_callbacks(self) -> None:
        """Setup MQTT callbacks."""
        self.mqtt.on_connect    = self._on_mqtt_connect
        self.mqtt.on_disconnect = self._on_mqtt_disconnect
        self.mqtt.on_message    = self._on_mqtt_message

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
            state=tk.DISABLED, relief=tk.SOLID, height=10)
        self._setup_text_widget_theme(self.txt_log)
        self.scr_log: ttk.Scrollbar = ttk.Scrollbar(
            self.frm_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log['yscrollcommand'] = self.scr_log.set
        # Add Switch Theme button
        self.btn_switch_theme: ttk.Button = ttk.Button(
            self.frm_connect, text=self._get_theme_icon(), width=3, 
            style="Icon.TButton", command=self._switch_theme)

    def _layout_widgets(self) -> None:
        """Lay out all widgets in the UI."""
        pad = {"padx": 5, "pady": 5}
        
        # ═══ ROOT WINDOW CONFIGURATION ═══
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # ═══ MAIN LAYOUT: TOP & BOTTOM FRAMES ═══
        self.frm_top.grid(row=0, column=0, sticky="ew", **pad)
        self.frm_bottom.grid(row=1, column=0, sticky="nsew", **pad)
        
        # ═══ TOP FRAME CONFIGURATION ═══
        # Configure top frame to have two equal columns (connection & users)
        self.frm_top.columnconfigure(0, weight=1)
        self.frm_top.columnconfigure(1, weight=1)
        
        # Place connection and users frames side by side
        self.frm_connect.grid(row=0, column=0, sticky="nsew", **pad)
        self.frm_users.grid(row=0, column=1, sticky="nsew", **pad)
        
        # ─── CONNECTION FRAME LAYOUT ───
        # Configure connection frame grid (3 rows, 4 columns)
        self.frm_connect.rowconfigure(0, weight=0)     # Room row
        self.frm_connect.rowconfigure(1, weight=0)     # Password row
        self.frm_connect.rowconfigure(2, weight=1)     # Buttons row (expandable)
        self.frm_connect.columnconfigure(0, weight=0)  # Labels column
        self.frm_connect.columnconfigure(1, weight=1)  # Entry fields column (expandable)
        self.frm_connect.columnconfigure(2, weight=0)  # Generate buttons column
        self.frm_connect.columnconfigure(3, weight=0)  # Copy buttons column
        
        # Room code row (row 0)
        self.lbl_room.grid( row=0, column=0, sticky="se", **pad)
        self.ent_room.grid( row=0, column=1, sticky="sw", **pad)
        self.btn_gen_room.grid(row=0, column=2, sticky="sw", **pad)
        self.btn_copy_room.grid(row=0, column=3, sticky="sw", **pad)
        
        # Password row (row 1)
        self.lbl_pwd.grid(  row=1, column=0, sticky="ne", **pad)
        self.ent_pwd.grid(  row=1, column=1, sticky="nw", **pad)
        self.btn_gen_pwd.grid(row=1, column=2, sticky="nw", **pad)
        self.btn_copy_pwd.grid(row=1, column=3, sticky="nw", **pad)
        
        # Connection buttons frame (row 2)
        self.frm_connect_btns.grid(row=2, column=0, columnspan=4, sticky="se")
        
        # Buttons within connection buttons frame
        self.btn_connect.grid(row=0, column=0, padx=5, pady=5)
        self.btn_disconnect.grid(row=0, column=1, padx=5, pady=5)
        
        # Theme switch button (also in connection frame)
        self.btn_switch_theme.grid(row=2, column=0, sticky="sw", **pad)
        
        # ─── USERS FRAME LAYOUT ───
        # Configure users frame for treeview and scrollbar
        self.frm_users.rowconfigure(0, weight=1)
        self.frm_users.columnconfigure(0, weight=1)
        
        # Place treeview and scrollbar
        self.tree_users.grid(row=0, column=0, sticky="nsew")
        self.scr_users.grid(row=0, column=1, sticky="ns")
        
        # ═══ BOTTOM FRAME LAYOUT ═══
        # Configure bottom frame for log area
        self.frm_bottom.rowconfigure(0, weight=1)
        self.frm_bottom.columnconfigure(0, weight=1)
        
        # ─── LOG FRAME LAYOUT ───
        # Place log frame in bottom area
        self.frm_log.grid(row=0, column=0, sticky="nsew")
        
        # Configure log frame for text widget and scrollbar
        self.frm_log.rowconfigure(0, weight=1)
        self.frm_log.columnconfigure(0, weight=1)
        
        # Place log text widget and scrollbar
        self.txt_log.grid(row=0, column=0, sticky="nsew")
        self.scr_log.grid(row=0, column=1, sticky="ns")

    # ─── UI ↔ MQTT Glue ─────────────────────────────────────────────────

    def on_connect(self) -> None:
        """Handle connect button click. Validates input and connects via MQTT."""
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
        """Handle disconnect button click. Disconnects from MQTT."""
        self._log("Disconnecting server…")
        self.mqtt.disconnect()

    def on_treeview_click(self, event: Any) -> None:
        """Handle clicks on the Treeview. Toggle permissions for users."""
        # Check if click is in a cell region
        region = self.tree_users.identify('region', event.x, event.y)
        if region != 'cell':
            return
            
        # Get the row and column
        rowid = self.tree_users.identify_row(event.y)
        col = self.tree_users.identify_column(event.x)
        if not rowid or col not in ('#2', '#3'):
            return
            
        # Get the username
        user = self.tree_users.item(rowid, 'values')[0]
        if user not in self.user_rows:
            return
            
        # Toggle the appropriate permission
        if col == '#2':  # Navigation column
            self.user_rows[user]["nav"] = not self.user_rows[user]["nav"]
        elif col == '#3':  # Control column
            self.user_rows[user]["control"] = not self.user_rows[user]["control"]
            
        # Update the display and log the change
        self._update_user_display(user)
        self._log(f"Permission changed for {user}: nav={self.user_rows[user]['nav']}, control={self.user_rows[user]['control']}")

    # MQTT callbacks
    def _on_mqtt_connect(self) -> None:
        """MQTT callback: connected. Enables/disables UI elements."""
        def update_ui():
            self._set_connected(True)
            host = self.mqtt.config.get('host', 'unknown')
            port = self.mqtt.config.get('port', 'unknown')
            self._set_title_with_server(f"MQTT: {host}:{port}")
            self._log("Connected ✅")
        self.root.after(0, update_ui)

    def _on_mqtt_disconnect(self) -> None:
        """MQTT callback: disconnected. Enables/disables UI elements."""
        def update_ui():
            self._set_connected(False)
            self.root.title("Presentation Clicker Server")
            self._log("Disconnected ❌")
        self.root.after(0, update_ui)

    def _on_mqtt_message(self, topic: str, payload: str) -> None:
        """MQTT callback: message received. Handles user status and actions."""
        self.root.after(0, lambda: self._handle_message(topic, payload))

    def _handle_message(self, topic: str, payload: str) -> None:
        """Handle incoming MQTT messages for user status and presentation actions."""
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
                self._log(f"User '{user}' connection lost.", user=user)
        elif topic.endswith("/presentation"):
            user = data.get("user")
            action = data.get("action")
            if user and action:
                # Check user permissions before executing action
                perms = self.user_rows.get(user, {})
                allowed = False
                
                # Check navigation permissions (next, previous)
                if action in ("next", "previous") and perms.get("nav"):
                    allowed = True
                    if action == "next":
                        keyboard.send("right")
                    elif action == "previous":
                        keyboard.send("left")
                        
                # Check control permissions (start, end, blackout)
                elif action in ("start", "end", "blackout") and perms.get("control"):
                    allowed = True
                    if action == "start":
                        keyboard.send("shift+f5")
                    elif action == "end":
                        keyboard.send("end")
                    elif action == "blackout":
                        keyboard.send("b")
                
                # Log the result
                if allowed:
                    self._log(f"Action '{action}' from '{user}' allowed and executed.", user=user)
                else:
                    self._log(f"Action '{action}' from '{user}' denied (insufficient permissions).", user=user)
            else:
                self._log(f"Malformed action message: {payload}")

    def _set_connected(self, is_connected: bool) -> None:
        """Enable/disable UI elements based on connection state."""
        state_input = tk.DISABLED if is_connected else tk.NORMAL
        state_conn = tk.DISABLED if is_connected else tk.NORMAL
        state_disconn = tk.NORMAL if is_connected else tk.DISABLED
        
        # Disable/enable input fields
        self.ent_room.config(state=state_input)
        self.ent_pwd.config(state=state_input)
        
        # Disable/enable generation and copy buttons
        self.btn_gen_room.config(state=state_input)
        self.btn_gen_pwd.config(state=state_input)
        
        # Disable/enable connection buttons
        self.btn_connect.config(state=state_conn)
        self.btn_disconnect.config(state=state_disconn)

    def _get_user_colors(self):
        """Return a list of distinct colors for users, responsive to theme."""
        # Light pastel colors for light theme
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

    def _get_user_color(self, user: str) -> str:
        """Get a consistent color for a user based on their name hash."""
        if not user:
            return "#888888"
        colors = self._get_user_colors()
        return colors[hash(user) % len(colors)]

    def _update_user(self, user: str, nav: bool = True, control: bool = False) -> None:
        """Add or update a user in the connected users list with background color."""
        if user in self.user_rows:
            return  # User already exists
        
        # Create colored row with tag
        nav_text = "✔" if nav else "✖"
        control_text = "✔" if control else "✖"
        user_color = self._get_user_color(user)
        tag_name = f"user_{user}"
        
        # Configure tag with user color
        self.tree_users.tag_configure(tag_name, background=user_color)
        
        # Insert row with tag
        iid = self.tree_users.insert("", tk.END, values=(user, nav_text, control_text), tags=(tag_name,))
        self.user_rows[user] = {"iid": iid, "nav": nav, "control": control}

    def _update_user_display(self, user: str) -> None:
        """Update the display for a specific user with color preservation."""
        if user not in self.user_rows:
            return
        user_data = self.user_rows[user]
        nav_text = "✔" if user_data["nav"] else "✖"
        control_text = "✔" if user_data["control"] else "✖"
        
        # Preserve the tag for background color
        tag_name = f"user_{user}"
        self.tree_users.item(user_data["iid"], values=(user, nav_text, control_text), tags=(tag_name,))

    def _generate_room(self) -> None:
        """Generate a random room code."""
        room = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.ent_room.delete(0, tk.END)
        self.ent_room.insert(0, room)

    def _generate_pwd(self) -> None:
        """Generate a random password."""
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        self.ent_pwd.delete(0, tk.END)
        self.ent_pwd.insert(0, pwd)

    def _copy_from_entry(self, entry: ttk.Entry) -> None:
        """Copy text from an entry widget to clipboard."""
        text = entry.get()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _update_theme_specific(self) -> None:
        """Update theme-specific elements when theme changes."""
        # Update user row colors for new theme
        for user in self.user_rows:
            tag_name = f"user_{user}"
            user_color = self._get_user_color(user)
            self.tree_users.tag_configure(tag_name, background=user_color)
        
        # Re-apply bold font for Treeview headers (may be needed after theme change)
        self.style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))


# Create main function using the factory
main = create_main_function("Presentation Clicker Server UI", ServerListenerApp)

if __name__ == "__main__":
    main()
