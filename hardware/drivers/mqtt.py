import paho.mqtt.client as mqtt
import json
from typing import Optional, Callable
from typing import TYPE_CHECKING
from hardware.utils.logging_config import setup_logger

if TYPE_CHECKING:
    from hardware.drivers.inputs import InputEvents

logger = setup_logger('MQTT')


class MqttClient:
    """MQTT client for publishing GPIO events to external services."""

    BROKER_HOST = "localhost"
    BROKER_PORT = 1883
    PUBLISH_TOPIC = "bindicator/events/gpio"
    QOS = 0

    def __init__(self):
        """Initialize MQTT client."""
        logger.info("Initializing MQTT client")
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._connected = False
        self._connection_error: Optional[Exception] = None
        self._subscriptions: dict[str, Callable] = {}  # topic -> callback function

        # Set up callbacks
        logger.debug("Setting up MQTT callbacks")
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        logger.info("MQTT client initialized")

    def connect(self):
        """Connect to MQTT broker. Raises exception on failure."""
        logger.info(f"Connecting to MQTT broker at {self.BROKER_HOST}:{self.BROKER_PORT}")
        try:
            self._client.connect(self.BROKER_HOST, self.BROKER_PORT, keepalive=60)
            logger.debug("Starting MQTT client loop")
            self._client.loop_start()

            # Wait briefly for connection to establish
            import time
            timeout = 5
            start = time.time()
            logger.debug(f"Waiting up to {timeout}s for connection to establish")
            while not self._connected and time.time() - start < timeout:
                if self._connection_error:
                    logger.error(f"Connection error detected: {self._connection_error}")
                    raise self._connection_error
                time.sleep(0.1)

            if not self._connected:
                error_msg = f"Failed to connect to MQTT broker at {self.BROKER_HOST}:{self.BROKER_PORT} within {timeout}s"
                logger.error(error_msg)
                raise ConnectionError(error_msg)

            logger.info(f"Successfully connected to MQTT broker at {self.BROKER_HOST}:{self.BROKER_PORT}")
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}", exc_info=True)
            raise

    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("Disconnected from MQTT broker")

    def publish_event(self, event: 'InputEvents'):
        """
        Publish an input event to MQTT.
        Used to broadcast GPIO button presses to external tools.

        Args:
            event: The input event to publish
        """
        if not self._connected:
            logger.debug(f"Not publishing event {event.name} - MQTT not connected")
            return

        try:
            import time
            message = {
                "event": event.name,
                "source": "gpio",
                "timestamp": int(time.time())
            }

            result = self._client.publish(self.PUBLISH_TOPIC, json.dumps(message), qos=self.QOS)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published GPIO event: {event.name} to {self.PUBLISH_TOPIC}")
            else:
                logger.warning(f"Failed to publish MQTT event: {event.name}")

        except Exception as e:
            logger.error(f"Error publishing MQTT event: {e}")

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback when connected to MQTT broker."""
        if reason_code == 0:
            self._connected = True
            logger.info(f"Connected to MQTT broker")
            # Resubscribe to all topics on reconnection
            for topic in self._subscriptions.keys():
                client.subscribe(topic, qos=self.QOS)
                logger.info(f"Resubscribed to topic: {topic}")
        else:
            error_msg = f"MQTT connection failed with code {reason_code}"
            logger.error(error_msg)
            self._connection_error = ConnectionError(error_msg)
            self._connected = False

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """Callback when disconnected from MQTT broker."""
        self._connected = False
        if reason_code != 0:
            error_msg = f"Unexpected MQTT disconnection with code {reason_code}"
            logger.error(error_msg)
            # This is a critical failure - raise it so the app can handle it
            raise ConnectionError(error_msg)

    def _on_message(self, client, userdata, msg):
        """Route incoming MQTT messages to registered callbacks."""
        topic = msg.topic
        if topic in self._subscriptions:
            callback = self._subscriptions[topic]
            try:
                payload = json.loads(msg.payload.decode())
                logger.debug(f"Received message on topic {topic}: {payload}")
                callback(payload)
            except Exception as e:
                logger.error(f"Error processing message on topic {topic}: {e}")
        else:
            logger.debug(f"Received message on unhandled topic: {topic}")

    def subscribe(self, topic: str, callback: Callable):
        """
        Subscribe to an MQTT topic with a callback function.

        Args:
            topic: The MQTT topic to subscribe to
            callback: Function to call when messages are received.
                     Receives the parsed JSON payload as a dict.
        """
        self._subscriptions[topic] = callback

        if self._connected:
            self._client.subscribe(topic, qos=self.QOS)
            logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.debug(f"Topic {topic} will be subscribed when connected")

    def unsubscribe(self, topic: str):
        """
        Unsubscribe from an MQTT topic.

        Args:
            topic: The MQTT topic to unsubscribe from
        """
        if topic in self._subscriptions:
            del self._subscriptions[topic]

            if self._connected:
                self._client.unsubscribe(topic)
                logger.info(f"Unsubscribed from topic: {topic}")


