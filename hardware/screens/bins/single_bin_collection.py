from typing import List
from contextlib import contextmanager
import threading
from core.database.database import SessionLocal
from core.database.repositories import BinRepository
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen, QuitApp
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvents
import datetime
from core.scheduler.scheduler import BinCollectionExplorer
from core.database import models
from hardware.utils.date_format import format_date
from hardware.screens.abstract_screen import Screen
from hardware.utils.logging_config import setup_logger

logger = setup_logger('SINGLE BIN SCREEN')


class SingleBinCollection(Screen):

    def __init__(self, bin_id: int):
        logger.info(f"SingleBinCollection screen created for bin_id={bin_id}")
        self._bin_id = bin_id
        self._bin_collection_explorer = BinCollectionExplorer()
        self._current_date = self._bin_collection_explorer.get_collection_date_after(
            datetime.date.today(), self._bin_id
        )
        logger.debug(f"Initial date for bin {bin_id} set to: {self._current_date}")
        self._cache_lock = threading.Lock()  # Thread-safe access to cache
        self._mqtt_subscribed = False  # Track subscription state

    @classmethod
    def from_input_events(cls, events: List[InputEvents]):
        db = SessionLocal()

        bin_repo = BinRepository(db)
        bin = bin_repo.get_by_button_press(events)

        db.close()

        if bin is not None:
            logger.info(f"Found bin '{bin.name}' (id={bin.id})")
            return cls(bin.id)
        else:
            logger.warning(f"No bin found for button presses: {[e.name for e in events]}")

        return None

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info(f"Entering SingleBinCollection screen for bin_id={self._bin_id}")
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

    def on_exit(self, drivers: Drivers):
        """Clean up MQTT subscription when leaving the screen."""
        logger.info(f"Exiting SingleBinCollection screen for bin_id={self._bin_id}")
        if self._mqtt_subscribed:
            try:
                drivers.mqtt.unsubscribe("bindicator/database/updated")
                logger.info("Unsubscribed from database updates")
            except Exception as e:
                logger.warning(f"Failed to unsubscribe from MQTT: {e}")

    def _on_database_updated(self, payload, drivers: Drivers):
        """Thread-safe callback when database is updated via MQTT."""
        logger.info("Database update notification received")
        with self._cache_lock:
            try:
                self._bin_collection_explorer.clear_cache()
                # Check the current date is still valid. If it isn't, go to first collection date
                is_current_date_still_collection_date = len(
                    [b for b in self._bin_collection_explorer.get_bins_due_out_on(self._current_date) if b.id == self._bin_id]
                ) > 0
                if not is_current_date_still_collection_date:
                    logger.info(f"Current date {self._current_date} no longer valid, finding next collection date")
                    self._current_date = self._bin_collection_explorer.get_collection_date_after(
                        datetime.date.today(), self._bin_id
                    )

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
            logger.debug(f"Left button pressed, navigating to previous date from {self._current_date}")
            previous_date = self._bin_collection_explorer.get_collection_date_before(self._current_date,
                                                                                     bin_id=self._bin_id)
            if previous_date is not None and previous_date >= datetime.date.today():
                self._current_date = previous_date
                logger.info(f"Navigated to previous date: {self._current_date}")
                self._display_correct_outputs(drivers)
                return None

        if InputEvents.RIGHT_BUTTON_PRESSED in events:
            logger.debug(f"Right button pressed, navigating to next date from {self._current_date}")
            bin_is_due_today = len(self._bin_collection_explorer.get_bins_due_out_on(self._current_date)) > 0
            bin_is_due_tomorrow = len(self._bin_collection_explorer.get_bins_due_out_on(self._current_date + datetime.timedelta(days=1))) > 0

            next_date = None
            if bin_is_due_today:
                next_date = self._bin_collection_explorer.get_collection_date_after(self._current_date, bin_id=self._bin_id)
            elif bin_is_due_tomorrow:
                next_date = self._bin_collection_explorer.get_collection_date_after(self._current_date + datetime.timedelta(days=1), bin_id=self._bin_id)

            if next_date is not None and next_date >= datetime.date.today():
                self._current_date = next_date
                logger.info(f"Navigated to next date: {self._current_date}")
                self._display_correct_outputs(drivers)
                return None

        if InputEvents.BIN_1_PRESSED in events or InputEvents.BIN_2_PRESSED in events or InputEvents.BIN_3_PRESSED in events or InputEvents.BIN_4_PRESSED in events:
            logger.debug(f"Bin button pressed: {[e.name for e in events]}")
            new_screen = SingleBinCollection.from_input_events(events)
            if new_screen._bin_id == self._bin_id:
                logger.info("Same bin pressed, returning to Today screen")
                from hardware.screens.bins.today import Today
                return Today()
            else:
                logger.info(f"Different bin pressed, switching to bin_id={new_screen._bin_id}")
                return new_screen

        return None

    def _display_correct_outputs(self, drivers: Drivers):
        bin = self._bin_collection_explorer.get_bin_by_id(self._bin_id)

        has_next_date = self._bin_collection_explorer.get_collection_date_after(self._current_date, bin_id=self._bin_id)
        has_previous_date = self._bin_collection_explorer.get_collection_date_before(self._current_date, bin_id=self._bin_id)

        drivers.lcd.display(
            format_date(self._current_date),
            bin.name,
            drivers.lcd.TEXT_STYLE_CENTER,
            prefix='<' if has_previous_date else None,
            suffix='>' if has_next_date else None
        )

        bin_state: list[LightState] = [LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF]

        bin_state[bin.position - 1] = LightState.ON

        drivers.lights.set_lights(
            bin_state[0],
            bin_state[1],
            bin_state[2],
            bin_state[3]
        )
        return

