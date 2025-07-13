"""
mqtt_client.py
Presentation Clicker MQTT Client logic for secure, robust communication with server via MQTT.
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
    "keepalive": 15,
    "transport": "tcp"  # 'tcp' or 'websockets'
}

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'mqtt_config.json')

def load_mqtt_config(config_path: str = CONFIG_FILE) -> dict:
    """
    Load MQTT client configuration from a JSON file.
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

class PresentationMqttClient:
    """
    MQTT client for Presentation Clicker system.
    Handles encrypted communication, reconnect logic, and UI callbacks.
    """
    def __init__(self, config_path: str = CONFIG_FILE):
        """
        Initialize the MQTT client and set default callbacks.
        Args:
            config_path: Path to the MQTT config file.
        """
        self.config = load_mqtt_config(config_path)
        transport = self.config.get("transport", DEFAULT_CONFIG["transport"])
        # UI callbacks (to be set by UI layer)
        self.on_connect: Callable[[], None] = lambda: None
        self.on_disconnect: Callable[[], None] = lambda: None
        self.on_publish: Callable[[str, str], None] = lambda topic, payload: None
        self.on_message: Callable[[str, str], None] = lambda topic, payload: None

        self.client = mqtt.Client(transport=transport)
        self.client.on_connect    = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message    = self._on_message
        self.client.on_log        = self._on_log

        self._should_reconnect = True
        self._reconnect_thread: Optional[threading.Thread] = None
        self.connected = False
        self.room = None
        self.user = None
        self.pwd = None
        self.base_topic = None
        self.fernet = None

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

    def connect(self, user: str, room: str, pwd: str, timeout: int = 5):
        """
        Connect to the MQTT broker and subscribe to room topics.
        Args:
            user: Display name of the user.
            room: Room code.
            pwd: Room password.
            timeout: Connection timeout in seconds.
        Raises:
            TimeoutError: If connection is not established within timeout.
        """
        self.room = room
        self.user = user
        self.pwd = pwd
        self.base_topic = self._get_base_topic()
        self.fernet = self._get_fernet(pwd)
        # Set Last Will on status topic
        will_topic = f"{self.base_topic}/status"
        will_payload = self.fernet.encrypt(json.dumps({"user": user, "status": "offline"}).encode()).decode()
        self.client.will_set(will_topic, will_payload, qos=1, retain=True)
        # Connect to broker using config
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

    def disconnect(self):
        """
        Disconnect from the MQTT broker and stop the client loop.
        """
        self._should_reconnect = False
        self.client.loop_stop()
        self.client.disconnect()

    def publish_action(self, action: str):
        """
        Publish a presentation action to the server.
        Args:
            action: Action string (e.g., 'next', 'previous', 'start', etc.)
        """
        topic = f"{self.base_topic}/presentation"
        payload = json.dumps({"user": self.user, "action": action})
        encrypted = self.fernet.encrypt(payload.encode()).decode()
        self.client.publish(topic, encrypted, qos=1)
        self.on_publish(topic, payload)

    def publish_status(self, status: str):
        """
        Publish the user's status (online/offline) to the server.
        Args:
            status: Status string ('online' or 'offline').
        """
        topic = f"{self.base_topic}/status"
        payload = json.dumps({"user": self.user, "status": status})
        encrypted = self.fernet.encrypt(payload.encode()).decode()
        self.client.publish(topic, encrypted, qos=1, retain=True)
        self.on_publish(topic, payload)

    # ─── Internal Paho Callbacks ────────────────────────────────
    def _on_connect(self, client, userdata, flags, rc):
        """
        Internal callback for MQTT connect event.
        Subscribes to room topics and publishes online status.
        """
        self.connected = True
        client.subscribe(f"{self.base_topic}/#")
        self.publish_status("online")
        self.on_connect()

    def _on_disconnect(self, client, userdata, rc):
        """
        Internal callback for MQTT disconnect event.
        Handles reconnect logic if needed.
        """
        self.connected = False
        self.on_disconnect()
        if self._should_reconnect and rc != 0:
            # Start a background thread to reconnect
            if not self._reconnect_thread or not self._reconnect_thread.is_alive():
                self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
                self._reconnect_thread.start()

    def _reconnect_loop(self):
        """
        Background thread for reconnecting to the broker.
        """
        while self._should_reconnect and not self.connected:
            try:
                self.client.reconnect()
            except Exception:
                time.sleep(3)

    def _on_message(self, client, userdata, msg):
        """
        Internal callback for MQTT message event.
        Decrypts and passes message to UI callback.
        """
        try:
            decrypted = self.fernet.decrypt(msg.payload).decode()
            self.on_message(msg.topic, decrypted)
        except (InvalidToken, Exception) as e:
            self.on_message(msg.topic, f"[Decryption failed: {e}]")

    def _on_log(self, client, userdata, level, buf):
        """
        Internal callback for MQTT log events (optional, for debugging).
        """
        pass  # Optionally print MQTT logs for debugging