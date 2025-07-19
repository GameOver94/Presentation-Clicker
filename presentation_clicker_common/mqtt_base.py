"""
mqtt_base.py
Base MQTT handler with common functionality for Presentation Clicker.
Handles encryption, reconnect logic, and common callbacks.
"""
import json
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Callable, Optional

import paho.mqtt.client as mqtt
from cryptography.fernet import InvalidToken

from .mqtt_config import load_mqtt_config, DEFAULT_CONFIG
from .encryption import get_fernet
from .topics import get_base_topic


class BaseMqttHandler(ABC):
    """
    Base MQTT handler with common functionality for client and server.
    Handles encryption, reconnect logic, and common callbacks.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the MQTT handler with common state and callbacks.
        Args:
            config_path: Path to the MQTT config file.
        """
        self.config = load_mqtt_config(config_path)
        transport = self.config.get("transport", DEFAULT_CONFIG["transport"])
        
        # UI callbacks (to be set by UI layer)
        self.on_connect: Callable[[], None] = lambda: None
        self.on_disconnect: Callable[[], None] = lambda: None
        self.on_message: Callable[[str, str], None] = lambda topic, payload: None
        
        # MQTT client setup
        self.client: mqtt.Client = mqtt.Client(transport=transport)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_log = self._on_log
        
        # Connection state
        self._should_reconnect: bool = True
        self._reconnect_thread: Optional[threading.Thread] = None
        self.connected: bool = False
        self.room: Optional[str] = None
        self.pwd: Optional[str] = None
        self.base_topic: Optional[str] = None
        self.fernet = None

    def _get_base_topic(self) -> str:
        """
        Returns the base MQTT topic for the current room.
        """
        return get_base_topic(self.room)

    def _setup_encryption(self, pwd: str) -> None:
        """
        Setup encryption using the room password.
        Args:
            pwd: Room password for encryption key derivation.
        """
        self.pwd = pwd
        self.fernet = get_fernet(pwd)

    def _connect_to_broker(self, timeout: int = 5) -> None:
        """
        Connect to the MQTT broker with timeout handling.
        Args:
            timeout: Connection timeout in seconds.
        Raises:
            TimeoutError: If connection times out.
        """
        # Get connection parameters from config
        host = self.config.get("host", DEFAULT_CONFIG["host"])
        port = self.config.get("port", DEFAULT_CONFIG["port"])
        keepalive = self.config.get("keepalive", DEFAULT_CONFIG["keepalive"])
        
        # Connect asynchronously
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
        if self.client:
            self.connected = False
            # Note: loop_stop() can cause freezing issues with paho-mqtt
            # self.client.loop_stop()
            self.client.disconnect()

    def publish_encrypted(self, topic: str, payload: dict, qos: int = 1, retain: bool = False) -> None:
        """
        Publish an encrypted message to the specified topic.
        Args:
            topic: MQTT topic to publish to.
            payload: Dictionary payload to encrypt and publish.
            qos: MQTT QoS level.
            retain: Whether to retain the message.
        """
        if not self.fernet:
            raise RuntimeError("Encryption not set up. Call _setup_encryption first.")
        
        json_payload = json.dumps(payload)
        encrypted = self.fernet.encrypt(json_payload.encode()).decode()
        self.client.publish(topic, encrypted, qos=qos, retain=retain)

    # ─── Internal MQTT Callbacks ────────────────────────────────────
    
    @abstractmethod
    def _on_connect_handler(self, client: mqtt.Client, userdata, flags, rc) -> None:
        """
        Abstract method for handling connection-specific logic.
        Must be implemented by subclasses.
        """
        pass

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc) -> None:
        """
        Internal callback for MQTT connect event.
        Calls the abstract handler and then the UI callback.
        """
        self.connected = True
        self._on_connect_handler(client, userdata, flags, rc)
        self.on_connect()

    def _on_disconnect(self, client: mqtt.Client, userdata, rc) -> None:
        """
        Internal callback for MQTT disconnect event.
        Handles reconnect logic if needed.
        """
        self.connected = False
        self.on_disconnect()
        
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
