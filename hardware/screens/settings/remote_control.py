from typing import List
import paho.mqtt.client as mqtt
import json
import logging
import time
import threading

from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvents
from hardware.screens.abstract_screen import Screen

logger = logging.getLogger(__name__)


class RemoteControl(Screen):
    """
    Screen that allows remote control of hardware via MQTT commands.
    Listens to bindicator/commands topic for LCD and light control.
    """

    BROKER_HOST = "localhost"
    BROKER_PORT = 1883
    COMMAND_TOPIC = "bindicator/commands"
    STATUS_TOPIC = "bindicator/remote_control/status"
    TIMEOUT_SECONDS = 300  # 5 minutes

    def __init__(self):
        self._mqtt_client = None
        self._connected = False
        self._should_disconnect = False
        self._last_command_time = time.time()
        self._command_lock = threading.Lock()
        self._drivers = None

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        """Initialize MQTT subscription and clear the hardware."""
        # Store drivers reference for use in callbacks
        self._drivers = drivers

        # Clear all hardware on entry
        drivers.lcd.display('', '', drivers.lcd.TEXT_STYLE_LEFT)
        drivers.lights.set_lights(LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF)

        # Schedule timeout check
        schedule.every(10).seconds.do(self._check_timeout)

        # Connect to MQTT broker
        self._connect_mqtt()

        # Publish ready signal so frontend knows hardware is in remote control mode
        self._publish_ready_signal()

    def _connect_mqtt(self):
        """Connect to MQTT broker and subscribe to commands."""
        try:
            self._mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self._mqtt_client.on_connect = self._on_connect
            self._mqtt_client.on_message = self._on_message
            self._mqtt_client.on_disconnect = self._on_disconnect

            self._mqtt_client.connect(self.BROKER_HOST, self.BROKER_PORT, keepalive=60)
            self._mqtt_client.loop_start()

            logger.info("RemoteControl: Connected to MQTT broker")
        except Exception as e:
            logger.error(f"RemoteControl: Failed to connect to MQTT: {e}")

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback when connected to MQTT broker."""
        if reason_code == 0:
            self._connected = True
            client.subscribe(self.COMMAND_TOPIC)
            logger.info(f"RemoteControl: Subscribed to {self.COMMAND_TOPIC}")
            # Publish ready signal after MQTT connection is established
            self._publish_ready_signal()
        else:
            logger.error(f"RemoteControl: MQTT connection failed with code {reason_code}")

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """Callback when disconnected from MQTT broker."""
        self._connected = False
        logger.info("RemoteControl: Disconnected from MQTT broker")

    def _publish_ready_signal(self):
        """Publish a ready signal so frontend knows hardware is in remote control mode."""
        if self._mqtt_client and self._connected:
            try:
                message = {
                    "status": "ready",
                    "timestamp": int(time.time())
                }
                self._mqtt_client.publish(self.STATUS_TOPIC, json.dumps(message), qos=0, retain=True)
                logger.info("RemoteControl: Published ready signal")
            except Exception as e:
                logger.error(f"RemoteControl: Failed to publish ready signal: {e}")

    def _on_message(self, client, userdata, msg):
        """Process incoming MQTT commands and control hardware directly."""
        try:
            payload = json.loads(msg.payload.decode())
            command_type = payload.get('type')

            with self._command_lock:
                self._last_command_time = time.time()

                if command_type == 'lcd_display' and self._drivers:
                    line1 = payload.get('line1', '')
                    line2 = payload.get('line2', '')
                    self._drivers.lcd.display(line1, line2, self._drivers.lcd.TEXT_STYLE_LEFT)
                    logger.debug(f"RemoteControl: Updated LCD: '{line1}' / '{line2}'")

                elif command_type == 'light_control' and self._drivers:
                    lights = payload.get('lights', {})
                    bin1 = self._parse_light_state(lights.get('bin1', 'off'))
                    bin2 = self._parse_light_state(lights.get('bin2', 'off'))
                    bin3 = self._parse_light_state(lights.get('bin3', 'off'))
                    bin4 = self._parse_light_state(lights.get('bin4', 'off'))
                    self._drivers.lights.set_lights(bin1, bin2, bin3, bin4)
                    logger.debug(f"RemoteControl: Updated lights: {lights}")

                elif command_type == 'disconnect':
                    self._should_disconnect = True
                    logger.info("RemoteControl: Disconnect command received")

        except Exception as e:
            logger.error(f"RemoteControl: Error processing MQTT message: {e}")

    def _check_timeout(self):
        """Check if timeout has been exceeded."""
        with self._command_lock:
            elapsed = time.time() - self._last_command_time
            if elapsed > self.TIMEOUT_SECONDS:
                logger.info(f"RemoteControl: Timeout exceeded ({elapsed:.0f}s), disconnecting")
                self._should_disconnect = True
        return CancelJob

    def tick(self, drivers: Drivers):
        """Check for disconnect signal."""
        with self._command_lock:
            if self._should_disconnect:
                self._cleanup()
                from hardware.screens.settings.settings import Settings
                return Settings()

        return None

    def _parse_light_state(self, state_str: str) -> LightState:
        """Parse light state string to LightState enum."""
        state_map = {
            'off': LightState.OFF,
            'on': LightState.ON,
            'phase': LightState.PHASE,
        }
        return state_map.get(state_str.lower(), LightState.OFF)

    def handle_inputs(self, events: List[InputEvents], drivers: Drivers = None):
        """Allow physical buttons to exit remote control mode."""
        # Press both buttons to exit remote control
        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            logger.info("RemoteControl: Manual exit via physical buttons")
            self._cleanup()
            from hardware.screens.settings.settings import Settings
            return Settings()
        return None

    def _cleanup(self):
        """Clean up MQTT connection."""
        if self._mqtt_client:
            try:
                # Clear the ready status
                self._mqtt_client.publish(self.STATUS_TOPIC, "", qos=0, retain=True)
                self._mqtt_client.loop_stop()
                self._mqtt_client.disconnect()
                logger.info("RemoteControl: MQTT client disconnected")
            except Exception as e:
                logger.error(f"RemoteControl: Error during cleanup: {e}")
