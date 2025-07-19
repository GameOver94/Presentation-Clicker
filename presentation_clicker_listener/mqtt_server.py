"""
mqtt_server.py
Presentation Clicker MQTT Server logic for secure, robust communication with clients via MQTT.
Handles encryption, reconnect, connection timeout, and UI callbacks.
"""

import os
import paho.mqtt.client as mqtt

from presentation_clicker_common import BaseMqttHandler

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'mqtt_config.yaml')


class PresentationMqttServer(BaseMqttHandler):
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
        super().__init__(config_path)

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
        # Store connection parameters
        self.room = room
        self.base_topic = self._get_base_topic()
        self._setup_encryption(pwd)
        
        # Connect to broker
        self._connect_to_broker(timeout)

    # ─── Internal MQTT Callbacks ────────────────────────────────
    
    def _on_connect_handler(self, client: mqtt.Client, userdata, flags, rc) -> None:
        """
        Server-specific connection handler.
        Subscribes to all room topics.
        """
        client.subscribe(f"{self.base_topic}/#")
