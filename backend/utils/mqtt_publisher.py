import paho.mqtt.client as mqtt
import json
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseUpdatePublisher:
    """
    Singleton MQTT publisher for broadcasting database update events.
    Silently fails if MQTT broker is unavailable.
    """

    _instance: Optional['DatabaseUpdatePublisher'] = None

    BROKER_HOST = "localhost"
    BROKER_PORT = 1883
    UPDATE_TOPIC = "bindicator/database/updated"
    SETTINGS_TOPIC = "bindicator/settings/updated"
    QOS = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._client: Optional[mqtt.Client] = None
        self._connected = False

        try:
            self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect

            # Try to connect - don't block if it fails
            self._client.connect(self.BROKER_HOST, self.BROKER_PORT, keepalive=60)
            self._client.loop_start()

            logger.info("DatabaseUpdatePublisher initialized")
        except Exception as e:
            logger.warning(f"DatabaseUpdatePublisher: Failed to connect to MQTT broker: {e}")
            self._client = None

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback when connected to MQTT broker."""
        if reason_code == 0:
            self._connected = True
            logger.info("DatabaseUpdatePublisher: Connected to MQTT broker")
        else:
            self._connected = False
            logger.warning(f"DatabaseUpdatePublisher: Connection failed with code {reason_code}")

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """Callback when disconnected from MQTT broker."""
        self._connected = False
        if reason_code != 0:
            logger.warning(f"DatabaseUpdatePublisher: Disconnected with code {reason_code}")

    def publish_database_update(self):
        """
        Publish a generic database update notification.
        Silently fails if MQTT is not available.
        """
        if not self._client or not self._connected:
            logger.debug("DatabaseUpdatePublisher: Not publishing - MQTT not connected")
            return

        try:
            message = {
                "message": "database_updated",
                "timestamp": int(time.time())
            }

            result = self._client.publish(self.UPDATE_TOPIC, json.dumps(message), qos=self.QOS)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"DatabaseUpdatePublisher: Published update to {self.UPDATE_TOPIC}")
            else:
                logger.warning(f"DatabaseUpdatePublisher: Failed to publish update")

        except Exception as e:
            logger.warning(f"DatabaseUpdatePublisher: Error publishing update: {e}")

    def publish_settings_update(self):
        """
        Publish a settings update notification.
        Silently fails if MQTT is not available.
        """
        if not self._client or not self._connected:
            logger.debug("DatabaseUpdatePublisher: Not publishing settings update - MQTT not connected")
            return

        try:
            message = {
                "message": "settings_updated",
                "timestamp": int(time.time())
            }

            result = self._client.publish(self.SETTINGS_TOPIC, json.dumps(message), qos=self.QOS)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"DatabaseUpdatePublisher: Published settings update to {self.SETTINGS_TOPIC}")
            else:
                logger.warning(f"DatabaseUpdatePublisher: Failed to publish settings update")

        except Exception as e:
            logger.warning(f"DatabaseUpdatePublisher: Error publishing settings update: {e}")

    def cleanup(self):
        """Disconnect from MQTT broker."""
        if self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
                logger.info("DatabaseUpdatePublisher: Disconnected")
            except Exception as e:
                logger.warning(f"DatabaseUpdatePublisher: Error during cleanup: {e}")


# Create singleton instance
_publisher = DatabaseUpdatePublisher()


def publish_database_update():
    """Convenience function to publish database updates."""
    _publisher.publish_database_update()


def publish_settings_update():
    """Convenience function to publish settings updates."""
    _publisher.publish_settings_update()

