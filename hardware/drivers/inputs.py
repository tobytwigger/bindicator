import time
from hardware.drivers.drivers import Drivers
from enum import Enum
import queue
import threading
from typing import Optional
from hardware.utils.logging_config import setup_logger

logger = setup_logger('INPUT HANDLER')

# class syntax

class InputEvents(Enum):
    LEFT_BUTTON_PRESSED = 1
    RIGHT_BUTTON_PRESSED = 2
    MOVEMENT_DETECTED = 3
    MOVEMENT_STOPPED = 4
    BIN_1_PRESSED = 5
    BIN_2_PRESSED = 6
    BIN_3_PRESSED = 7
    BIN_4_PRESSED = 8

    def get_button_position(self) -> int | None:

        if self == InputEvents.BIN_1_PRESSED:
            return 1
        elif self == InputEvents.BIN_2_PRESSED:
            return 2
        elif self == InputEvents.BIN_3_PRESSED:
            return 3
        elif self == InputEvents.BIN_4_PRESSED:
            return 4

        return None

    def is_bin_press(self) -> bool:
        return self in [InputEvents.BIN_1_PRESSED, InputEvents.BIN_2_PRESSED, InputEvents.BIN_3_PRESSED, InputEvents.BIN_4_PRESSED]

class Inputs:
    # Debounce interval for button presses (seconds)
    DEBOUNCE_INTERVAL = 0.3

    # Maximum queue size before dropping events
    MAX_QUEUE_SIZE = 500

    # Polling interval for GPIO checks (seconds)
    POLL_INTERVAL = 0.01

    def __init__(self, drivers: Drivers, mqtt_client=None):
        self._drivers = drivers

        # Load timeout from database with fallback to 120
        self._movement_timeout = self._load_timeout_from_db()
        self._timeout_lock = threading.Lock()  # Thread-safe access to timeout

        self._mqtt_client = mqtt_client

        # Event queue shared between background thread and main thread
        self._event_queue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)

        # Thread control
        self._stop_event = threading.Event()
        self._polling_thread: Optional[threading.Thread] = None

        # Debouncing state (used by background thread)
        self._last_event_time = {}

        # Movement state (shared between threads, accessed with lock)
        self._movement_lock = threading.Lock()
        self._movement_detected_at: Optional[float] = None

    def _load_timeout_from_db(self) -> int:
        """Load timeout value from database, fallback to 120 if unavailable."""
        try:
            from core.database.repositories import SettingsRepository

            settings_repo = SettingsRepository()
            timeout = settings_repo.get_by_key("timeout")
            logger.info(f"Loaded timeout from database: {timeout}s")
            return timeout
        except Exception as e:
            logger.warning(f"Failed to load timeout from database, using default 120s: {e}")
            return 120

    def update_timeout(self):
        """Update timeout value from database. Called when settings are updated via MQTT."""
        new_timeout = self._load_timeout_from_db()
        with self._timeout_lock:
            old_timeout = self._movement_timeout
            self._movement_timeout = new_timeout
            logger.info(f"Timeout updated: {old_timeout}s -> {new_timeout}s")

    def _on_settings_updated(self, payload):
        """Callback when settings are updated via MQTT."""
        logger.info("Settings update notification received, refreshing timeout...")
        self.update_timeout()



    def start(self):
        """Start the background polling thread and connect MQTT if configured."""
        if self._polling_thread is not None and self._polling_thread.is_alive():
            logger.warning("Input polling thread already running")
            return

        # Connect MQTT if configured
        if self._mqtt_client:
            try:
                logger.info("Connecting to MQTT...")
                self._mqtt_client.connect()
                logger.info("MQTT connected successfully")

                # Subscribe to settings updates
                self._mqtt_client.subscribe("bindicator/settings/updated", self._on_settings_updated)
                logger.info("Subscribed to settings updates")
            except Exception as e:
                logger.warning(f"Failed to connect to MQTT broker: {e}")
                logger.info("Continuing without MQTT support")
                self._mqtt_client = None  # Disable MQTT if connection fails

        # Start the background polling thread
        self._stop_event.clear()
        self._polling_thread = threading.Thread(target=self._poll_inputs_loop, daemon=True)
        self._polling_thread.start()
        logger.info("Started input polling thread")

    def stop(self):
        """Stop the background polling thread and disconnect MQTT."""
        if self._polling_thread is None:
            logger.debug("No polling thread to stop")
            return

        logger.info("Stopping input polling thread...")
        self._stop_event.set()

        # Wait for thread to finish
        if self._polling_thread.is_alive():
            logger.debug("Waiting for polling thread to finish...")
            self._polling_thread.join(timeout=2.0)

        # Disconnect MQTT if configured
        if self._mqtt_client:
            logger.info("Disconnecting MQTT...")
            self._mqtt_client.disconnect()
            logger.info("MQTT disconnected")

        logger.info("Input polling thread stopped")

    def listen(self):
        """
        Retrieve all available events from the queue.
        This is called by the main application loop.
        """
        events = []

        # Drain all available events from the queue
        while True:
            try:
                event = self._event_queue.get_nowait()
                events.append(event)
                logger.debug(f"Retrieved {event.name} from queue")
            except queue.Empty:
                break

        # Check movement timeout in main thread
        # This needs to be done here to maintain timing accuracy
        with self._movement_lock:
            if self._movement_detected_at is not None:
                with self._timeout_lock:
                    timeout = self._movement_timeout
                time_elapsed = time.time() - self._movement_detected_at

                if time_elapsed > timeout:
                    logger.info(f"Movement timeout reached ({time_elapsed:.1f}s > {timeout}s)")
                    logger.debug("Movement stopped, enqueueing MOVEMENT_STOPPED")
                    events.append(InputEvents.MOVEMENT_STOPPED)
                    self._movement_detected_at = None

                    # Publish GPIO event to MQTT so external tools can see it
                    if self._mqtt_client:
                        self._mqtt_client.publish_event(InputEvents.MOVEMENT_STOPPED)

        if events:
            logger.debug(f"Returning {len(events)} event(s): {[e.name for e in events]}")

        return events

    def _poll_inputs_loop(self):
        """Background thread that continuously polls GPIO inputs."""
        while not self._stop_event.is_set():
            try:
                self._poll_gpio_inputs()
                time.sleep(self.POLL_INTERVAL)
            except Exception as e:
                logger.error(f"Error in input polling loop: {e}")

    def _poll_gpio_inputs(self):
        """Poll all GPIO inputs and queue events with debouncing."""
        current_time = time.time()

        # Check movement sensor
        if self._drivers.movement.movement_detected():
            with self._movement_lock:
                if self._movement_detected_at is None:
                    # First detection
                    logger.info(f"Movement detected at {current_time}")
                    logger.debug("First movement detection, enqueueing MOVEMENT_DETECTED")
                    self._enqueue_event(InputEvents.MOVEMENT_DETECTED)

                    # Publish GPIO event to MQTT so external tools can see it
                    if self._mqtt_client:
                        self._mqtt_client.publish_event(InputEvents.MOVEMENT_DETECTED)

                self._movement_detected_at = current_time

        # Check all button inputs with debouncing
        if self._drivers.buttons.is_left_pressed():
            self._enqueue_event_with_debounce(InputEvents.LEFT_BUTTON_PRESSED, current_time)

        if self._drivers.buttons.is_right_pressed():
            self._enqueue_event_with_debounce(InputEvents.RIGHT_BUTTON_PRESSED, current_time)

        if self._drivers.buttons.is_bin_1_pressed():
            self._enqueue_event_with_debounce(InputEvents.BIN_1_PRESSED, current_time)

        if self._drivers.buttons.is_bin_2_pressed():
            self._enqueue_event_with_debounce(InputEvents.BIN_2_PRESSED, current_time)

        if self._drivers.buttons.is_bin_3_pressed():
            self._enqueue_event_with_debounce(InputEvents.BIN_3_PRESSED, current_time)

        if self._drivers.buttons.is_bin_4_pressed():
            self._enqueue_event_with_debounce(InputEvents.BIN_4_PRESSED, current_time)

    def _enqueue_event_with_debounce(self, event: InputEvents, current_time: float):
        """Enqueue an event only if debounce interval has passed."""
        last_time = self._last_event_time.get(event, 0)
        time_since_last = current_time - last_time

        if time_since_last >= self.DEBOUNCE_INTERVAL:
            logger.debug(f"Enqueueing {event.name} (time since last: {time_since_last:.3f}s)")
            self._last_event_time[event] = current_time
            self._enqueue_event(event)

            # Publish GPIO event to MQTT so external tools can see it
            if self._mqtt_client:
                self._mqtt_client.publish_event(event)
        else:
            logger.debug(f"Skipping {event.name} (time since last: {time_since_last:.3f}s < {self.DEBOUNCE_INTERVAL}s)")

    def _enqueue_event(self, event: InputEvents):
        """Add event to queue, dropping if full."""
        try:
            self._event_queue.put_nowait(event)
            logger.debug(f"Added {event.name} to queue (size: {self._event_queue.qsize()})")
        except queue.Full:
            logger.warning(f"Event queue full, dropping event: {event}")

