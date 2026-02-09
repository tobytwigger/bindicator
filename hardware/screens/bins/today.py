from typing import List
import math
import threading

from core.database.database import SessionLocal
from core.database.repositories import BinRepository
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen
from schedule import Scheduler
from hardware.drivers.inputs import InputEvents
import datetime
from core.scheduler.scheduler import BinCollectionExplorer
from hardware.screens.bins.bin_collections import BinCollections
from hardware.screens.bins.single_bin_collection import SingleBinCollection
from hardware.utils.date_format import format_date
from hardware.utils.logging_config import setup_logger

logger = setup_logger('TODAY SCREEN')


class Today(Screen):

    def __init__(self):
        logger.info("Today screen created")
        self._cache_lock = threading.Lock()  # Thread-safe access to cache
        self._mqtt_subscribed = False  # Track subscription state

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering Today screen")
        # Subscribe to database update notifications via MQTT
        if drivers.mqtt and not self._mqtt_subscribed:
            try:
                drivers.mqtt.subscribe("bindicator/database/updated",
                                       lambda payload: self._on_database_updated(payload, drivers))
                self._mqtt_subscribed = True
                logger.info("Subscribed to database updates via MQTT")
            except Exception as e:
                logger.warning(f"Failed to subscribe to MQTT: {e}")

        self._display_correct_outputs(drivers)

    def on_exit(self, drivers):
        """Clean up MQTT subscription when leaving the screen."""
        logger.info("Exiting Today screen")
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
                self._display_correct_outputs(drivers)
                logger.debug("Cache refreshed after database update")
            except Exception as e:
                logger.error(f"Error refreshing cache: {e}", exc_info=True)


    def handle_inputs(self, events: List[InputEvents], drivers: Drivers):
        # If we press both left and right, show the 'settings' screen
        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            logger.info("Left + Right buttons pressed, navigating to Settings")
            from hardware.screens.settings.settings import Settings

            return Settings()

        if InputEvents.RIGHT_BUTTON_PRESSED in events:
            logger.info("Right button pressed, navigating to BinCollections")
            return BinCollections()

        if InputEvents.BIN_1_PRESSED in events or InputEvents.BIN_2_PRESSED in events or InputEvents.BIN_3_PRESSED in events or InputEvents.BIN_4_PRESSED in events:
            logger.info("A bin button has been pressed")
            # If any bins are pressed, we need to see what the status of that bin is. If it's actionable, 'prime' the bin!

            # Load the bin that was pressed
            db = SessionLocal()
            bin_repo = BinRepository(db)
            bin = bin_repo.get_by_button_press(events)
            db.close()
            if bin is None:
                logger.info("No bin found for button presses: " + str(events))
                return None

            logger.info(f"Found bin '{bin.name}' (id={bin.id}) related to the button press")

            # Check if the bin is 'actionable'
            bin_status = BinCollectionExplorer().get_bin_status_for_date(bin.id, datetime.date.today())

            print(bin_status)


            return None

        return None

    def _display_correct_outputs(self, drivers: Drivers):
        logger.debug("Updating display with current bin collection data")
        # Use the smart action-based logic
        result = BinCollectionExplorer().get_bins_requiring_action()

        bins_to_display = result['bins_to_display']
        display_date = result['display_date']
        next_collection_date = result['next_collection_date']

        if bins_to_display:
            logger.debug(f"Displaying {len(bins_to_display)} bins for {display_date}")
            self._display_bins_due(drivers, bins_to_display, display_date, next_collection_date)
        else:
            logger.debug(f"No actionable bins, next collection: {next_collection_date}")
            self._display_no_bins_due(drivers, next_collection_date)

    def _status_to_light_state(self, status: str) -> LightState:
        """Map bin status to light state."""
        status_map = {
            'due_out': LightState.FLASH_FAST,
            'taken_out': LightState.OFF,
            'put_out_early': LightState.OFF,
            'not_yet_due': LightState.ON,
            'collected': LightState.OFF,
            'missed': LightState.OFF
        }
        return status_map.get(status, LightState.OFF)

    def _display_bins_due(self, drivers: Drivers, bins_data: List[dict], current_date: datetime.date, next_out: datetime.date | None = None):
        """Display bins due with status-based lighting.

        Args:
            drivers: Hardware drivers
            bins_data: List of dicts with 'bin', 'status', 'put_out_datetime', 'put_out_id'
            current_date: The date being displayed
            next_out: Next collection date (for arrow navigation)
        """
        bins_as_text = ", ".join(bin_data['bin'].name for bin_data in bins_data)

        drivers.lcd.display(
            format_date(current_date),
            bins_as_text,
            drivers.lcd.TEXT_STYLE_CENTER,
            prefix='<' if current_date not in [datetime.date.today(), datetime.date.today() + datetime.timedelta(days=1)] else None,
            suffix='>' if next_out is not None else None,
        )

        bin_state: list[LightState] = [LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF]

        for bin_data in bins_data:
            bin_obj = bin_data['bin']
            status = bin_data['status']
            bin_state[bin_obj.position - 1] = self._status_to_light_state(status)

        drivers.lights.set_lights(
            bin_state[0],
            bin_state[1],
            bin_state[2],
            bin_state[3]
        )

        return


    def _display_no_bins_due(self, drivers, next_out: datetime.date | None):

        days_until_next_due = math.ceil((next_out - datetime.date.today()).days) if next_out is not None else None

        drivers.lcd.display(
            'No bins due',
            'Out in ' + str(days_until_next_due) + ' ' + ('day' if days_until_next_due == 1 else 'days'),
            drivers.lcd.TEXT_STYLE_CENTER,
            suffix='>' if next_out is not None else None,
        )

        drivers.lights.all_off()
