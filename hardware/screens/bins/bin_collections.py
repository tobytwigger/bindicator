from typing import List
import math
import threading
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen
from schedule import Scheduler
from hardware.drivers.inputs import InputEvents
import datetime
from core.scheduler.scheduler import BinCollectionExplorer
from hardware.screens.bins.single_bin_collection import SingleBinCollection
from hardware.utils.date_format import format_date
from hardware.utils.logging_config import setup_logger

logger = setup_logger('BIN COLLECTIONS SCREEN')


class BinCollections(Screen):

    def __init__(self):
        logger.info("BinCollections screen created")
        self._bin_collection_explorer = BinCollectionExplorer()
        self._minimum_date = self._bin_collection_explorer.get_collection_date_after(
            datetime.date.today()
        )
        self._current_date = self._minimum_date
        logger.debug(f"Initial date set to: {self._current_date}")

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

        self._display_correct_outputs(drivers)

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
                self._bin_collection_explorer.clear_cache()
                # Check the current date is still valid. If it isn't, go to today
                is_current_date_still_collection_date = len(self._bin_collection_explorer.get_bins_due_out_on(self._current_date)) > 0
                if not is_current_date_still_collection_date:
                    logger.info(f"Current date {self._current_date} no longer has collections, resetting to today")
                    self._current_date = datetime.date.today()

                self._display_correct_outputs(drivers)
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
            logger.debug(f"Left button pressed, navigating to previous collection date from {self._current_date}")
            # Navigate to previous collection date (minimum: today)
            previous_date = self._bin_collection_explorer.get_collection_date_before(self._current_date)
            if previous_date is not None and previous_date >= self._minimum_date:
                self._current_date = previous_date
                logger.info(f"Navigated to previous date: {self._current_date}")
            else:
                logger.info("At earliest date, navigating back to Today screen")
                from hardware.screens.bins.today import Today

                return Today()
            self._display_correct_outputs(drivers)
            return None

        if InputEvents.RIGHT_BUTTON_PRESSED in events:
            logger.debug(f"Right button pressed, navigating to next collection date from {self._current_date}")
            # Navigate to next collection date
            next_date = self._bin_collection_explorer.get_collection_date_after(self._current_date)
            if next_date is not None:
                self._current_date = next_date
                logger.info(f"Navigated to next date: {self._current_date}")
                self._display_correct_outputs(drivers)
            return None

        if InputEvents.BIN_1_PRESSED in events or InputEvents.BIN_2_PRESSED in events or InputEvents.BIN_3_PRESSED in events or InputEvents.BIN_4_PRESSED in events:
            logger.info(f"Bin button pressed: {[e.name for e in events]}, navigating to SingleBinCollection")
            return SingleBinCollection.from_input_events(events)

        return None

    def _display_correct_outputs(self, drivers: Drivers):
        """Display bins based on their status and what requires action."""
        logger.debug(f"Displaying outputs for date: {self._current_date}")

        # User has navigated to a specific date - show that date
        bins_on_date = self._bin_collection_explorer.get_bins_due_out_on(self._current_date)
        logger.debug(f"Found {len(bins_on_date)} bins due on {self._current_date}: {[b.name for b in bins_on_date]}")

        if bins_on_date:
            # Build bin data with status for this specific date
            bins_data = []
            for bin_obj in bins_on_date:
                status, put_out_datetime, put_out_id = self._bin_collection_explorer.get_bin_status_for_date(
                    bin_obj.id,
                    self._current_date
                )
                logger.debug(f"Bin '{bin_obj.name}' (id={bin_obj.id}): status={status}, put_out_id={put_out_id}")
                bins_data.append({
                    'bin': bin_obj,
                    'status': status,
                    'put_out_datetime': put_out_datetime,
                    'put_out_id': put_out_id
                })

            next_collection_date = self._bin_collection_explorer.get_collection_date_after(self._current_date)
            logger.debug(f"Next collection date after {self._current_date}: {next_collection_date}")
            self._display_bins_due(drivers, bins_data, self._current_date, next_collection_date)
        else:
            # No bins on this date
            logger.info(f"No bins due on {self._current_date}")
            next_collection_date = self._bin_collection_explorer.get_collection_date_after(self._current_date)
            logger.debug(f"Next collection date: {next_collection_date}")
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
        light_state = status_map.get(status, LightState.OFF)

        if status not in status_map:
            logger.warning(f"Unknown bin status '{status}', defaulting to OFF")

        return light_state

    def _display_bins_due(self, drivers: Drivers, bins_data: List[dict], current_date: datetime.date, next_out: datetime.date | None = None):
        """Display bins due with status-based lighting.

        Args:
            drivers: Hardware drivers
            bins_data: List of dicts with 'bin', 'status', 'put_out_datetime', 'put_out_id'
            current_date: The date being displayed
            next_out: Next collection date (for arrow navigation)
        """
        bins_as_text = ", ".join(bin_data['bin'].name for bin_data in bins_data)
        logger.info(f"Displaying bins due: {bins_as_text} on {format_date(current_date)}")

        show_left_arrow = current_date not in [datetime.date.today(), datetime.date.today() + datetime.timedelta(days=1)]
        show_right_arrow = next_out is not None
        logger.debug(f"Navigation arrows: left={show_left_arrow}, right={show_right_arrow}")

        drivers.lcd.display(
            format_date(current_date),
            bins_as_text,
            drivers.lcd.TEXT_STYLE_CENTER,
            prefix='<' if show_left_arrow else None,
            suffix='>' if show_right_arrow else None,
        )

        bin_state: list[LightState] = [LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF]

        for bin_data in bins_data:
            bin_obj = bin_data['bin']
            status = bin_data['status']
            light_state = self._status_to_light_state(status)
            bin_state[bin_obj.position - 1] = light_state
            logger.debug(f"Position {bin_obj.position} ({bin_obj.name}): status={status} -> light={light_state.name}")

        logger.info(f"Setting lights: pos1={bin_state[0].name}, pos2={bin_state[1].name}, pos3={bin_state[2].name}, pos4={bin_state[3].name}")
        drivers.lights.set_lights(
            bin_state[0],
            bin_state[1],
            bin_state[2],
            bin_state[3]
        )

        return


    def _display_no_bins_due(self, drivers, next_out: datetime.date | None):
        logger.info("Displaying 'No bins due' message")

        days_until_next_due = math.ceil((next_out - datetime.date.today()).days) if next_out is not None else None

        if days_until_next_due is not None:
            logger.info(f"Next bin collection in {days_until_next_due} day(s) on {next_out}")
            day_text = 'day' if days_until_next_due == 1 else 'days'
            message = f'Out in {days_until_next_due} {day_text}'
        else:
            logger.warning("No future collection dates found")
            message = 'No future dates'

        drivers.lcd.display(
            'No bins due',
            message,
            drivers.lcd.TEXT_STYLE_CENTER,
            suffix='>' if next_out is not None else None,
        )

        logger.debug("Turning off all lights for 'no bins due' state")
        drivers.lights.all_off()
