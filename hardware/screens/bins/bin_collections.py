from typing import List, Iterator, Tuple
import math
import threading
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen
from schedule import Scheduler
from hardware.drivers.inputs import InputEvents
import datetime
from core.scheduler.scheduler import BinCollectionExplorer
from core.scheduler.schemas import BinCollection
from hardware.screens.bins.single_bin_collection import SingleBinCollection
from hardware.utils.date_format import format_date
from hardware.utils.logging_config import setup_logger
import polars as pl

logger = setup_logger('BIN COLLECTIONS SCREEN')


class BinCollections(Screen):

    def __init__(self):
        logger.info("BinCollections screen created")
        self._bin_collection_explorer = BinCollectionExplorer()
        self._selected_index = 0
        self._cache_lock = threading.Lock()  # Thread-safe access to cache
        self._mqtt_subscribed = False  # Track subscription state

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering BinCollections screen")
        # Subscribe to database update notifications via MQTT
        if drivers.mqtt and not self._mqtt_subscribed:
            try:
                drivers.mqtt.subscribe("bindicator/database/updated",
                                       lambda payload: self._on_database_updated(payload, drivers))
                self._mqtt_subscribed = True
                logger.info("Subscribed to database updates via MQTT")
            except Exception as e:
                logger.warning(f"Failed to subscribe to MQTT: {e}")
        schedule.every(15).minutes.do(self._bin_collection_explorer.load_data)

        self._update_outputs(drivers)

    def on_exit(self, drivers):
        """Clean up MQTT subscription when leaving the screen."""
        logger.info("Exiting BinCollections screen")
        if drivers.mqtt and self._mqtt_subscribed:
            try:
                drivers.mqtt.unsubscribe("bindicator/database/updated")
                self._mqtt_subscribed = False
                logger.info("Unsubscribed from database updates")
            except Exception as e:
                logger.warning(f"Failed to unsubscribe from MQTT: {e}")

    def _on_database_updated(self, payload, drivers: Drivers):
        """Thread-safe callback when database is updated via MQTT."""
        logger.info("Database update notification received")
        with self._cache_lock:
            try:
                self._bin_collection_explorer.load_data()
                if self._selected_index >= len(self._bin_collection_explorer.data):
                    logger.info(f"Selected index {self._selected_index} out of range after refresh, resetting to 0")
                    self._selected_index = 0

                self._update_outputs(drivers)
                logger.debug("Cache refreshed after database update")
            except Exception as e:
                logger.error(f"Error refreshing cache: {e}", exc_info=True)

    def handle_inputs(self, events: List[InputEvents], drivers: Drivers):
        # If we press both left and right, show the 'settings' screen
        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            logger.info("Both buttons pressed, navigating to Settings")
            from hardware.screens.settings.settings import Settings

            return Settings()

        if InputEvents.LEFT_BUTTON_PRESSED in events:
            logger.debug(f"Left button pressed, navigating to previous collection date from index {self._selected_index}")
            if self._selected_index > 0:
                self._selected_index -= 1
            else:
                logger.info("At earliest date, navigating back to Today screen")
                from hardware.screens.bins.today import Today

                return Today()
            self._update_outputs(drivers)
            return None

        if InputEvents.RIGHT_BUTTON_PRESSED in events:
            logger.debug(f"Right button pressed, navigating to next collection date from index {self._selected_index}")
            if self._selected_index < len(self._bin_collection_explorer.data) - 1:
                self._selected_index += 1
                self._update_outputs(drivers)
            return None

        if InputEvents.BIN_1_PRESSED in events or InputEvents.BIN_2_PRESSED in events or InputEvents.BIN_3_PRESSED in events or InputEvents.BIN_4_PRESSED in events:

            first_button_event = next((e for e in events if e.is_bin_press()), None)

            if first_button_event is None:
                logger.warning("No bin press events found in events: " + str(events))
                return None

            logger.debug(f"Bin button {first_button_event} pressed, filtered from {len(events)}")

            bin = first_button_event.get_bin()

            if bin is None:
                logger.info("No bin found for button presses: " + str(events))
                return None

            logger.info(f"Found bin '{bin.name}' (id={bin.id}) related to the button press")


            return SingleBinCollection(bin.id)

        return None

    def _update_outputs(self, drivers: Drivers):
        """Display bins based on their status and what requires action."""
        data: Tuple[int, datetime.date, List[BinCollection]] = self._bin_collection_explorer.get_not_yet_due_collection_days_by_index(self._selected_index)
        total_count, date, collection = data

        # Start easy with the bin lights. They should be on if in the collection, or off otherwise
        positions_to_show = [bin_collection.bin_position for bin_collection in collection]
        drivers.lights.set_lights(
            *[LightState.ON if pos in positions_to_show else LightState.OFF for pos in range(1, 5)]
        )

        # Next the LCD. We show a date at the top, and the bins listed below
        # We should have a prefix < always (can go bcak to today screen), and a suffix > if the index is < the max index (so we know we can navigate in either direction)
        drivers.lcd.display(
            format_date(date),
            "|".join(bin_collection.bin_name for bin_collection in collection),
            drivers.lcd.TEXT_STYLE_CENTER,
            prefix='<',
            suffix='>' if self._selected_index < total_count else None,
        )



