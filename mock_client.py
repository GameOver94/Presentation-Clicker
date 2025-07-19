# mock_client.py
import time
import threading

from mqtt_client import PresentationMqttClient

class MockClient:
    def __init__(self, user, room, pwd, sequence, delay=1.0, initial_delay=0.0):
        self.client = PresentationMqttClient()
        self.user = user
        self.room = room
        self.pwd = pwd
        self.sequence = sequence
        self.delay = delay
        self.initial_delay = initial_delay
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish

    def on_connect(self):
        print(f"[MockClient] Connected as '{self.user}' to room '{self.room}'")
        
        def send_sequence():
            if self.initial_delay > 0:
                print(f"[MockClient] Waiting initial delay: {self.initial_delay} seconds")
                time.sleep(self.initial_delay)
            for action in self.sequence:
                print(f"[MockClient] Sending action: {action}")
                self.client.publish_action(action)
                time.sleep(self.delay)
            print("[MockClient] Sequence complete. Disconnecting...")
            self.client.disconnect()
        threading.Thread(target=send_sequence, daemon=True).start()

    def on_disconnect(self):
        print(f"[MockClient] Disconnected.")
        self._running = False

    def on_message(self, topic, payload):
        print(f"[MockClient] Received: {topic}: {payload}")

    def on_publish(self, topic, payload):
        print(f"[MockClient] Published: {topic}: {payload}")

    def run(self):
        try:
            self._running = True
            self.client.connect(self.user, self.room, self.pwd)
            while self._running and getattr(self.client, 'connected', False):
                time.sleep(0.1)
        except Exception as e:
            print(f"[MockClient] Connection failed: {e}")

if __name__ == "__main__":
    # Example usage: change these as needed
    user = "MockUser"
    room = "ABC123"
    pwd = "password123"
    sequence = ["start", "next", "next", "previous", "blackout", "end"]
    delay = 1.5  # seconds between commands
    initial_delay = 2.0  # seconds before starting sequence
    mock = MockClient(user, room, pwd, sequence, delay, initial_delay)
    mock.run()
