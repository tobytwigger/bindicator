from typing import List
from contextlib import contextmanager
import math
import threading
from core.database.database import SessionLocal
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen, QuitApp
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvents
import datetime
from core.scheduler.scheduler import BinCollectionExplorer
from core.database import models
from hardware.screens.bins.single_bin_collection import SingleBinCollection
from hardware.utils.date_format import format_date
from hardware.screens.abstract_screen import Screen
import logging

logger = logging.getLogger(__name__)


class BinCollections(Screen):

    def __init__(self):
        self._current_date = datetime.date.today()
        self._bin_collection_explorer = BinCollectionExplorer()
        self._cache_lock = threading.Lock()  # Thread-safe access to cache
        self._mqtt_subscribed = False  # Track subscription state

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        # Subscribe to database update notifications via MQTT
        if drivers.mqtt and not self._mqtt_subscribed:
            try:
                drivers.mqtt.subscribe("bindicator/database/updated",
                                       lambda payload: self._on_database_updated(payload, drivers))
                self._mqtt_subscribed = True
                logger.info("BinCollections: Subscribed to database updates")
            except Exception as e:
                logger.warning(f"BinCollections: Failed to subscribe to MQTT: {e}")

        self._display_correct_outputs(drivers)

    def on_exit(self, drivers):
        """Clean up MQTT subscription when leaving the screen."""
        if drivers.mqtt and self._mqtt_subscribed:
            try:
                drivers.mqtt.unsubscribe("bindicator/database/updated")
                self._mqtt_subscribed = False
                logger.info("BinCollections: Unsubscribed from database updates")
            except Exception as e:
                logger.warning(f"BinCollections: Failed to unsubscribe from MQTT: {e}")

    def _on_database_updated(self, payload, drivers: Drivers):
        """Thread-safe callback when database is updated via MQTT."""
        logger.info("BinCollections: Database update notification received")
        with self._cache_lock:
            try:
                self._bin_collection_explorer.clear_cache()
                # Check the current date is still valid. If it isn't, go to today
                is_current_date_still_collection_date = len(self._bin_collection_explorer.get_bins_due_out_on(self._current_date)) > 0
                if not is_current_date_still_collection_date:
                    self._current_date = datetime.date.today()

                self._display_correct_outputs(drivers)
                logger.debug("BinCollections: Cache refreshed after database update")
            except Exception as e:
                logger.error(f"BinCollections: Error refreshing cache: {e}")


    def handle_inputs(self, events: List[InputEvents], drivers: Drivers):
        # If we press both left and right, show the 'settings' screen
        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            from hardware.screens.settings.settings import Settings

            return Settings()

        if InputEvents.LEFT_BUTTON_PRESSED in events:
            previous_date = self._bin_collection_explorer.get_collection_date_before(self._current_date)
            if previous_date is not None and previous_date >= datetime.date.today():
                self._current_date = previous_date
            else:
                self._current_date = datetime.date.today()

            self._display_correct_outputs(drivers)
            return None

        if InputEvents.RIGHT_BUTTON_PRESSED in events:
            self._current_date = self._bin_collection_explorer.get_collection_date_after(self._current_date) or datetime.date.today()
            self._display_correct_outputs(drivers)
            return None

        if InputEvents.BIN_1_PRESSED in events or InputEvents.BIN_2_PRESSED in events or InputEvents.BIN_3_PRESSED in events or InputEvents.BIN_4_PRESSED in events:
            return SingleBinCollection.from_input_events(events)

        return None

    def _display_correct_outputs(self, drivers: Drivers):
        bins_due = self._bin_collection_explorer.get_bins_due_out_on(self._current_date)
        next_out = self._bin_collection_explorer.get_collection_date_after(self._current_date)

        if len(bins_due) > 0:
            self._display_bins_due(drivers, bins_due, next_out)
        else:
            self._display_no_bins_due(drivers, next_out)

    def _display_bins_due(self, drivers: Drivers, bins_due: List[models.Bin], next_out: datetime.date | None = None):
        bins_as_text = ''
        for b in bins_due:
            bins_as_text += b.name + ', '

        drivers.lcd.display(
            format_date(self._current_date),
            bins_as_text,
            drivers.lcd.TEXT_STYLE_CENTER,
            prefix='<' if self._current_date != datetime.date.today() else None,
            suffix='>' if next_out is not None else None,
        )

        bin_state: list[LightState] = [LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF]

        # # If the date is today, then the bin is always due
        # # If the date is tomorrow, then the bin is only due if the home value is set to put out the bin the day before
        # bins_are_due = False
        # if date == datetime.date.today():
        #     bins_are_due = True
        # elif date == datetime.date.today() + datetime.timedelta(days=1) and getattr(self._state.home.value,
        #                                                                             "put_out_day_before", True):
        #     bins_are_due = True
        #
        # currently_due_bins = {}

        for b in bins_due:
            # TODO Check if bin has been taken out already
            # is_due_out = bins_are_due and getattr(b, "is_taken_out", False) is False
            # if is_due_out:
            #     currently_due_bins[b.position] = b
            bin_state[b.position - 1] = LightState.ON

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
