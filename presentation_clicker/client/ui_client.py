"""
ui_client.py
Presentation Clicker Client UI using Tkinter and ttkbootstrap.
Provides a user interface for connecting to the server, sending navigation commands, and viewing logs.
"""
import datetime
import json
import os
import tkinter as tk
from tkinter import ttk
from typing import Optional

from ttkbootstrap import Style
from ttkbootstrap.constants import PRIMARY, SUCCESS, DANGER
from .mqtt_client import PresentationMqttClient
from ..common import (
    BaseApp, create_main_function, get_misc_icons, UILogger
)


class PresentationClickerApp(BaseApp):
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
        super().__init__("Presentation Clicker", theme, config_path)
        
        # --- MQTT setup & callbacks ---
        self.mqtt: PresentationMqttClient = mqtt_client or PresentationMqttClient()
        self._setup_mqtt_callbacks()

        # --- build UI ---
        self._create_widgets()
        
        # Initialize logger after widgets are created
        self.logger = UILogger(self.txt_log, self.theme_manager)
        self._setup_log_colors()
        
        self._layout_widgets()

    def _setup_mqtt_callbacks(self) -> None:
        """Setup MQTT callbacks."""
        self.mqtt.on_connect    = self._on_mqtt_connect
        self.mqtt.on_disconnect = self._on_mqtt_disconnect
        self.mqtt.on_publish    = self._on_mptt_publish
        self.mqtt.on_message    = self._on_mqtt_message

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
        misc_icons = get_misc_icons()
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
            height=12, state=tk.DISABLED)
        self._setup_text_widget_theme(self.txt_log)
        self.scr_log: ttk.Scrollbar = ttk.Scrollbar(self.frm_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=self.scr_log.set)
        # Theme switch button
        self.btn_switch_theme: ttk.Button = ttk.Button(
            self.frm_nav, text=self._get_theme_icon(), width=3, 
            style="Icon.TButton", command=self._switch_theme)

    def _setup_log_colors(self):
        """Setup log colors for sent/received messages."""
        from ..common import get_message_colors
        colors = get_message_colors(self.theme_manager.is_dark_theme())
        # Use background colors for message tags (consistent with UILogger)
        self.txt_log.tag_config("sent", background=colors["sent"])
        self.txt_log.tag_config("received", background=colors["received"])

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
        # Configure top frame to have two equal columns (connection & navigation)
        self.frm_top.columnconfigure(0, weight=1)
        self.frm_top.columnconfigure(1, weight=1)
        
        # Place connection and navigation frames side by side
        self.frm_connect.grid(row=0, column=0, sticky="nsew", **pad)
        self.frm_nav.grid(row=0, column=1, sticky="nsew", **pad)
        
        # ─── CONNECTION FRAME LAYOUT ───
        # Configure connection frame grid (expandable entry column)
        self.frm_connect.columnconfigure(1, weight=1)
        
        # Display name row (row 0) - spans 2 columns for wider entry
        self.lbl_name.grid(row=0, column=0, sticky="e", **pad)
        self.ent_name.grid(row=0, column=1, columnspan=2, sticky="w", **pad)
        
        # Room code row (row 1) - entry, paste button, connect button
        self.lbl_room.grid(row=1, column=0, sticky="e", **pad)
        self.ent_room.grid(row=1, column=1, sticky="w", **pad)
        self.btn_paste_room.grid(row=1, column=2, sticky="w", **pad)
        self.btn_connect.grid(row=1, column=3, **pad)
        
        # Password row (row 2) - entry, paste button, disconnect button
        self.lbl_pwd.grid(row=2, column=0, sticky="e", **pad)
        self.ent_pwd.grid(row=2, column=1, sticky="w", **pad)
        self.btn_paste_pwd.grid(row=2, column=2, sticky="w", **pad)
        self.btn_disconnect.grid(row=2, column=3, **pad)
        
        # Theme switch button (row 3) - positioned in bottom-right
        self.btn_switch_theme.grid(row=3, column=3, sticky="se", **pad)
        
        # ─── NAVIGATION FRAME LAYOUT ───
        # Navigation buttons arranged in 2x3 grid:
        # Row 0: [Start] [End] [Blackout]
        # Row 1: [Prev] [Next] 
        self.btn_start.grid(row=0, column=0, **pad)
        self.btn_end.grid(row=0, column=1, **pad)
        self.btn_blackout.grid(row=0, column=2, **pad)
        self.btn_prev.grid(row=1, column=0, **pad)
        self.btn_next.grid(row=1, column=1, **pad)
        
        # ═══ BOTTOM FRAME LAYOUT ═══
        # Configure bottom frame for log area
        self.frm_bottom.columnconfigure(0, weight=1)
        self.frm_bottom.rowconfigure(0, weight=1)
        
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
        name: str = self.ent_name.get().strip()
        room: str = self.ent_room.get().strip()
        pwd: str = self.ent_pwd.get().strip()
        if not (name and room and pwd):
            self._log("ERROR: All fields are required.")
            return
        self._log(f"Connecting as '{name}' to room '{room}'…")
        try:
            self.mqtt.connect(name, room, pwd)
        except TimeoutError as e:
            self._log(f"ERROR: {e}")

    def on_disconnect(self) -> None:
        """Handle disconnect button click. Disconnects from MQTT."""
        self._log("Disconnecting…")
        self.mqtt.disconnect()

    def on_prev(self) -> None:
        """Send 'previous' action to server."""
        self.mqtt.publish_action("previous")
    def on_next(self) -> None:
        """Send 'next' action to server."""
        self.mqtt.publish_action("next")
    def on_start(self) -> None:
        """Send 'start' action to server."""
        self.mqtt.publish_action("start")
    def on_end(self) -> None:
        """Send 'end' action to server."""
        self.mqtt.publish_action("end")
    def on_blackout(self) -> None:
        """Send 'blackout' action to server."""
        self.mqtt.publish_action("blackout")

    # MQTT client callbacks
    def _on_mqtt_connect(self) -> None:
        """MQTT callback: connected. Enables navigation and disables input fields."""
        def update_ui():
            self._set_connected(True)
            host = self.mqtt.config.get('host', 'unknown')
            port = self.mqtt.config.get('port', 'unknown')
            self._set_title_with_server(f"MQTT: {host}:{port}")
            self._log("Connected ✅")
        self.root.after(0, update_ui)

    def _on_mqtt_disconnect(self) -> None:
        """MQTT callback: disconnected. Disables navigation and enables input fields."""
        def update_ui():
            self._set_connected(False)
            self.root.title("Presentation Clicker")
            self._log("Disconnected ❌")
        self.root.after(0, update_ui)

    def _on_mptt_publish(self, topic: str, payload: str) -> None:
        """MQTT callback: message published. Logs outgoing messages."""
        def log_sent():
            try:
                data = json.loads(payload)
                user = data.get("user")
                action = data.get("action")
                if topic.endswith("/presentation") and user and action:
                    self._log(f"Sent action '{action}' from '{user}'.", tag="sent")
                elif topic.endswith("/status") and user:
                    self._log(f"Sent status update for user '{user}'.", tag="sent")
                else:
                    self._log(f"Sent: {topic}: {payload}", tag="sent")
            except Exception:
                self._log(f"Sent: {topic}: {payload}", tag="sent")
        self.root.after(0, log_sent)

    def _on_mqtt_message(self, topic: str, payload: str) -> None:
        """MQTT callback: message received. Parses JSON payload and logs user status/actions."""
        def log_message():
            try:
                data = json.loads(payload)
                if topic.endswith("/status"):
                    user = data.get("user")
                    status = data.get("status")
                    if user and status:
                        self._log(f"User '{user}' is now {status}.", tag="received")
                    else:
                        self._log(f"Malformed status message: {payload}", tag="received")
                elif topic.endswith("/presentation"):
                    user = data.get("user")
                    action = data.get("action")
                    if user and action:
                        self._log(f"Action '{action}' from '{user}' received.", tag="received")
                    else:
                        self._log(f"Malformed action message: {payload}", tag="received")
                else:
                    self._log(f"[RCV] {topic}: {payload}", tag="received")
            except Exception:
                self._log(f"Malformed message: {payload}", tag="received")
        self.root.after(0, log_message)

    # ─── Helpers ────────────────────────────────────────────────────────

    def _set_connected(self, is_connected: bool) -> None:
        """Enable/disable UI elements based on connection state."""
        # Input fields & connect button
        state_input = tk.DISABLED if is_connected else tk.NORMAL
        state_conn = tk.DISABLED if is_connected else tk.NORMAL
        state_disconn = tk.NORMAL if is_connected else tk.DISABLED
        state_nav = tk.NORMAL if is_connected else tk.DISABLED
        
        # Disable/enable input fields
        self.ent_name.config(state=state_input)
        self.ent_room.config(state=state_input)
        self.ent_pwd.config(state=state_input)
        
        # Disable/enable paste buttons
        self.btn_paste_room.config(state=state_input)
        self.btn_paste_pwd.config(state=state_input)
        
        # Disable/enable connection buttons
        self.btn_connect.config(state=state_conn)
        self.btn_disconnect.config(state=state_disconn)
        
        # Navigation buttons
        for btn in [self.btn_prev, self.btn_next, self.btn_start, self.btn_end, self.btn_blackout]:
            btn.config(state=state_nav)

    def _paste_to_entry(self, entry: ttk.Entry) -> None:
        """Paste clipboard content to specified entry widget."""
        try:
            clipboard = self.root.clipboard_get()
            entry.delete(0, tk.END)
            entry.insert(0, clipboard)
        except tk.TclError:
            pass  # Clipboard empty or unavailable


# Create main function using the factory
main = create_main_function("Presentation Clicker Client UI", PresentationClickerApp)

if __name__ == "__main__":
    main()
