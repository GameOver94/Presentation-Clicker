"""
mqtt_client.py
Presentation Clicker MQTT Client logic for secure, robust communication with server via MQTT.
Handles encryption, reconnect, connection timeout, and UI callbacks.
"""
import json
import os
import time
from typing import Callable

import paho.mqtt.client as mqtt

from ..common import BaseMqttHandler

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'mqtt_config.yaml')


class PresentationMqttClient(BaseMqttHandler):
    """
    MQTT client for Presentation Clicker system.
    Handles encrypted communication, reconnect logic, and UI callbacks.
    """
    def __init__(self, config_path: str = CONFIG_FILE):
        """
        Initialize the MQTT client state and set default callbacks.
        Args:
            config_path: Path to the MQTT config file.
        """
        super().__init__(config_path)
        # Additional client-specific callback
        self.on_publish: Callable[[str, str], None] = lambda topic, payload: None
        # Client-specific state
        self.user = None

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
        # Store connection parameters
        self.room = room
        self.user = user
        self.base_topic = self._get_base_topic()
        self._setup_encryption(pwd)
        
        # Set Last Will on status topic (connection lost)
        will_topic = f"{self.base_topic}/status"
        will_payload = {"user": user, "status": "connection_lost"}
        encrypted_will = self.fernet.encrypt(json.dumps(will_payload).encode()).decode()
        self.client.will_set(will_topic, encrypted_will, qos=1, retain=True)
        
        # Connect to broker
        self._connect_to_broker(timeout)

    def disconnect(self):
        """
        Disconnect from the MQTT broker and stop the client loop.
        """
        # Send offline status before disconnecting (graceful disconnect)
        if self.connected:
            self.publish_status("offline")
            time.sleep(0.5)
        super().disconnect()

    def publish_action(self, action: str):
        """
        Publish a presentation action to the server.
        Args:
            action: Action string (e.g., 'next', 'previous', 'start', etc.)
        """
        topic = f"{self.base_topic}/presentation"
        payload = {"user": self.user, "action": action}
        self.publish_encrypted(topic, payload, qos=1)
        # Call publish callback for UI
        self.on_publish(topic, json.dumps(payload))

    def publish_status(self, status: str):
        """
        Publish the user's status (online/offline) to the server.
        Args:
            status: Status string ('online' or 'offline').
        """
        topic = f"{self.base_topic}/status"
        payload = {"user": self.user, "status": status}
        self.publish_encrypted(topic, payload, qos=1, retain=True)
        # Call publish callback for UI
        self.on_publish(topic, json.dumps(payload))

    # ─── Internal MQTT Callbacks ────────────────────────────────
    
    def _on_connect_handler(self, client: mqtt.Client, userdata, flags, rc) -> None:
        """
        Client-specific connection handler.
        Subscribes to room topics and publishes online status.
        """
        client.subscribe(f"{self.base_topic}/#")
        self.publish_status("online")
