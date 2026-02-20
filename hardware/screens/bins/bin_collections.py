from typing import List, Iterator, Tuple
import math
import threading
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen, QuitApp
from schedule import Scheduler
from hardware.drivers.inputs import InputEvent, InputEvents
import datetime
from core.scheduler.scheduler import BinCollectionExplorer
from core.scheduler.schemas import BinCollection
from hardware.screens.bins.single_bin_collection import SingleBinCollection
from hardware.utils.bin_collection_caching import BinCollectionDataCaching
from hardware.utils.date_format import format_date
from hardware.utils.logging_config import setup_logger
import polars as pl

logger = setup_logger('BIN COLLECTIONS SCREEN')


class BinCollections(Screen):

    def __init__(self):
        logger.info("BinCollections screen created")
        self._bin_collections = BinCollectionDataCaching()
        self._selected_index = 0

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering BinCollections screen")
        # Subscribe to database update notifications via MQTT
        self._bin_collections.subscribe(logger, schedule, drivers)
        self._update_outputs(drivers)


    def on_exit(self, drivers):
        """Clean up MQTT subscription when leaving the screen."""
        logger.info("Exiting BinCollections screen")
        self._bin_collections.unsubscribe(logger, drivers)

    def tick(self, drivers) -> Screen | None | QuitApp:
        if self._bin_collections.recently_updated:
            logger.debug("Bin collection data recently updated, refreshing outputs")
            self._update_outputs(drivers)

        return None

    def handle_inputs(self, events: InputEvents, drivers: Drivers):
        # If we press both left and right, show the 'settings' screen
        if InputEvent.LEFT_BUTTON_PRESSED in events and InputEvent.RIGHT_BUTTON_PRESSED in events:
            logger.info("Both buttons pressed, navigating to Settings")
            from hardware.screens.settings.settings import Settings

            return Settings()

        if InputEvent.LEFT_BUTTON_PRESSED in events:
            logger.debug(f"Left button pressed, navigating to previous collection date from index {self._selected_index}")
            if self._selected_index > 0:
                self._selected_index -= 1
            else:
                logger.info("At earliest date, navigating back to Today screen")
                from hardware.screens.bins.today import Today

                return Today()
            self._update_outputs(drivers)
            return None

        if InputEvent.RIGHT_BUTTON_PRESSED in events:
            logger.debug(f"Right button pressed, navigating to next collection date from index {self._selected_index}")
            if self._selected_index < len(self._bin_collections.data) - 1:
                self._selected_index += 1
                self._update_outputs(drivers)
            return None

        if events.contains_bin_press():
            logger.debug(f"Bin button pressed: {[e.name for e in events]}")

            bin = events.get_first_bin_press().get_bin()

            if bin is None:
                logger.info("No bin found for button presses: " + str(events))
                return None

            logger.info(f"Found bin '{bin.name}' (id={bin.id}) related to the button press")


            return SingleBinCollection(bin.id)

        return None

    def _update_outputs(self, drivers: Drivers):
        if self._selected_index >= len(self._bin_collections.data.data):
            logger.info(f"Selected index {self._selected_index} out of range after refresh, resetting to 0")
            self._selected_index = 0

        """Display bins based on their status and what requires action."""
        data: Tuple[int, datetime.date, List[BinCollection]] = self._bin_collections.data.get_not_yet_due_collection_days_by_index(self._selected_index)
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


        self._bin_collections.mark_update_handled()



