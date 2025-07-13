"""
mqtt_server.py
Presentation Clicker MQTT Server logic for secure, robust communication with clients via MQTT.
Handles encryption, reconnect, connection timeout, and UI callbacks.
"""

import json
import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import threading
import time
from typing import Callable, Optional
import os

DEFAULT_CONFIG = {
    "host": "test.mosquitto.org",
    "port": 1883,
    "keepalive": 60,
    "transport": "tcp"  # 'tcp' or 'websockets'
}

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'mqtt_config.json')

def load_mqtt_config(config_path: str = CONFIG_FILE) -> dict:
    """
    Load MQTT server configuration from a JSON file.
    Returns default config if file is missing or invalid.
    """
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**DEFAULT_CONFIG, **config}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

class PresentationMqttServer:
    """
    MQTT server for Presentation Clicker system.
    Handles encrypted communication, reconnect logic, and UI callbacks.
    """
    def __init__(self, config_path: str = CONFIG_FILE) -> None:
        """
        Initialize the MQTT server and set default callbacks.
        Args:
            config_path: Path to the MQTT config file.
        """
        self.config = load_mqtt_config(config_path)
        transport = self.config.get("transport", DEFAULT_CONFIG["transport"])
        self.on_connect: Callable[[], None] = lambda: None
        self.on_disconnect: Callable[[], None] = lambda: None
        self.on_message: Callable[[str, str], None] = lambda topic, payload: None
        # self.on_log: Callable[[str], None] = lambda msg: None

        self.client: mqtt.Client = mqtt.Client(transport=transport)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_log = self._on_log
        self._should_reconnect: bool = True
        self._reconnect_thread: Optional[threading.Thread] = None
        self.connected: bool = False
        self.room: Optional[str] = None
        self.pwd: Optional[str] = None
        self.base_topic: Optional[str] = None
        self.fernet: Optional[Fernet] = None

    def _get_base_topic(self) -> str:
        """
        Returns the base MQTT topic for the current room.
        """
        return f"presentationclicker/{self.room}"

    def _get_fernet(self, pwd: str) -> Fernet:
        """
        Derives a Fernet encryption key from the password using PBKDF2HMAC.
        Args:
            pwd: Password string.
        Returns:
            Fernet: Fernet encryption object.
        """
        salt = b"presentationclicker_salt"  # Use a constant salt or store per-room for more security
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(pwd.encode("utf-8")))
        return Fernet(key)

    def connect(self, room: str, pwd: str, timeout: int = 5) -> None:
        """
        Connect to the MQTT broker and subscribe to room topics.
        Args:
            room: Room code.
            pwd: Room password.
            timeout: Connection timeout in seconds.
        Raises:
            TimeoutError: If connection is not established within timeout.
        """
        self.room = room
        self.pwd = pwd
        self.base_topic = self._get_base_topic()
        self.fernet = self._get_fernet(pwd)
        host = self.config.get("host", DEFAULT_CONFIG["host"])
        port = self.config.get("port", DEFAULT_CONFIG["port"])
        keepalive = self.config.get("keepalive", DEFAULT_CONFIG["keepalive"])
        self.client.connect_async(host, port, keepalive=keepalive)
        self._should_reconnect = True
        self.client.loop_start()
        # Wait for connection or timeout
        start = time.time()
        while not self.connected and (time.time() - start) < timeout:
            time.sleep(0.1)
        if not self.connected:
            self.client.loop_stop()
            raise TimeoutError(f"MQTT connection timed out after {timeout} seconds.")

    def disconnect(self) -> None:
        """
        Disconnect from the MQTT broker and stop the client loop.
        """
        self._should_reconnect = False
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc) -> None:
        """
        Internal callback for MQTT connect event.
        Subscribes to room topics and triggers UI callback.
        """
        self.connected = True
        client.subscribe(f"{self.base_topic}/#")
        self.on_connect()
        # self.on_log("MQTT server connected and subscribed.")

    def _on_disconnect(self, client: mqtt.Client, userdata, rc) -> None:
        """
        Internal callback for MQTT disconnect event.
        Handles reconnect logic if needed.
        """
        self.connected = False
        self.on_disconnect()
        # self.on_log("MQTT server disconnected.")
        if self._should_reconnect and rc != 0:
            if not self._reconnect_thread or not self._reconnect_thread.is_alive():
                self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
                self._reconnect_thread.start()

    def _reconnect_loop(self) -> None:
        """
        Background thread for reconnecting to the broker.
        """
        while self._should_reconnect and not self.connected:
            try:
                self.client.reconnect()
            except Exception:
                time.sleep(3)

    def _on_message(self, client: mqtt.Client, userdata, msg) -> None:
        """
        Internal callback for MQTT message event.
        Decrypts and passes message to UI callback.
        """
        try:
            decrypted = self.fernet.decrypt(msg.payload).decode()
            self.on_message(msg.topic, decrypted)
        except (InvalidToken, Exception) as e:
            self.on_message(msg.topic, f"[Decryption failed: {e}]")

    def _on_log(self, client: mqtt.Client, userdata, level, buf) -> None:
        """
        Internal callback for MQTT log events (optional, for debugging).
        """
        pass  # Optionally log MQTT debug info
