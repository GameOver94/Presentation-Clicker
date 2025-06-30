"""
ui_client.py
Presentation Clicker Client UI using Tkinter and ttkbootstrap.
Provides a user interface for connecting to the server, sending navigation commands, and viewing logs.
"""
import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from mqtt_client import PresentationMqttClient
from typing import Optional

class PresentationClickerApp:
    """
    Presentation Clicker Client UI application.
    Handles user input, MQTT communication, and log display.
    """
    def __init__(self, mqtt_client: Optional[PresentationMqttClient] = None, theme: str = "flatly") -> None:
        """
        Initialize the UI, MQTT client, and callbacks.
        Args:
            mqtt_client: Optional custom MQTT client instance.
            theme: ttkbootstrap theme name.
        """
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
        """Set UI and monospace fonts."""
        self.font_ui: tuple[str, int]   = ("Segoe UI",     10)
        self.font_mono: tuple[str, int] = ("Cascadia Code",  9)

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
        # Connection inputs
        L = ttk.Label; E = ttk.Entry; B = ttk.Button
        self.lbl_name: ttk.Label = L(self.frm_connect, text="Display Name:", font=self.font_ui)
        self.ent_name: ttk.Entry = E(self.frm_connect, font=self.font_ui, width=25)
        self.lbl_room: ttk.Label = L(self.frm_connect, text="Room Code:",    font=self.font_ui)
        self.ent_room: ttk.Entry = E(self.frm_connect, font=self.font_ui, width=15)
        self.btn_paste_room: ttk.Button = B(self.frm_connect, text="Paste", width=6, command=lambda: self._paste_to_entry(self.ent_room))
        self.lbl_pwd: ttk.Label  = L(self.frm_connect, text="Password:",     font=self.font_ui)
        self.ent_pwd: ttk.Entry  = E(self.frm_connect, font=self.font_ui, width=15, show="*")
        self.btn_paste_pwd: ttk.Button = B(self.frm_connect, text="Paste", width=6, command=lambda: self._paste_to_entry(self.ent_pwd))
        # Connect / Disconnect
        self.btn_connect: ttk.Button = ttk.Button(
            self.frm_connect, text="Connect", bootstyle="success-outline",
            width=12, command=self.on_connect)
        self.btn_disconnect: ttk.Button = ttk.Button(
            self.frm_connect, text="Disconnect", bootstyle="danger-outline",
            width=12, state=tk.DISABLED, command=self.on_disconnect)
        # Navigation
        nav_bs = dict(bootstyle="info", width=10, state=tk.DISABLED)
        self.btn_prev: ttk.Button     = ttk.Button(self.frm_nav, text="◀ Prev",   command=self.on_prev,     **nav_bs)
        self.btn_next: ttk.Button     = ttk.Button(self.frm_nav, text="Next ▶",   command=self.on_next,     **nav_bs)
        self.btn_start: ttk.Button    = ttk.Button(self.frm_nav, text="⏺ Start",  command=self.on_start,    **nav_bs)
        self.btn_end: ttk.Button      = ttk.Button(self.frm_nav, text="⏹ End",    command=self.on_end,      **nav_bs)
        self.btn_blackout: ttk.Button = ttk.Button(self.frm_nav, text="🕶 Blackout", command=self.on_blackout, **nav_bs)
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
        # navigation buttons in frm_nav
        self.btn_prev.    grid(row=0, column=0, **pad)
        self.btn_next.    grid(row=0, column=1, **pad)
        self.btn_start.   grid(row=0, column=2, **pad)
        self.btn_end.     grid(row=0, column=3, **pad)
        self.btn_blackout.grid(row=1, column=0, columnspan=4, **pad)
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
    def _on_mqtt_connect(self) -> None:
        """
        MQTT callback: connected. Enables navigation and disables input fields.
        """
        self.root.after(0, lambda: self._set_connected(True))

    def _on_mqtt_disconnect(self) -> None:
        """
        MQTT callback: disconnected. Disables navigation and enables input fields.
        """
        self.root.after(0, lambda: self._set_connected(False))
        
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
        import datetime
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

    def run(self) -> None:
        """
        Start the Tkinter main loop.
        """
        self.root.mainloop()

if __name__ == "__main__":
    app = PresentationClickerApp()
    app.run()