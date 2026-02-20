from typing import List
import math
import threading

from core.database.database import SessionLocal
from core.database.repositories import BinRepository, BinPutOutRepository
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen, QuitApp, HandlesDataCache
from schedule import Scheduler
from hardware.drivers.inputs import InputEvent, InputEvents
import datetime
from core.scheduler.scheduler import BinCollectionExplorer
from core.scheduler.schemas import BinCollection, BinCollectionStatus
from hardware.utils.bin_collection_caching import BinCollectionDataCaching
from hardware.utils.logging_config import setup_logger
from core.database import schemas

logger = setup_logger('TODAY SCREEN')


class Today(Screen):
    """
    Show information about upcoming collections relative to today
    Show any actions the user needs to be taking
    """

    def __init__(self):
        logger.info("Today screen created")
        self._bin_collections = BinCollectionDataCaching()
        self._actively_confirming_bin_id: int | None = None  # Track if we're actively confirming a bin action

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering Today screen")
        self._bin_collections.subscribe(logger, schedule, drivers)
        self._update_outputs(drivers)

    def on_exit(self, drivers):
        """Clean up MQTT subscription when leaving the screen."""
        logger.info("Exiting Today screen")
        self._bin_collections.unsubscribe(logger, drivers)

    def handle_inputs(self, events: InputEvents, drivers: Drivers):
        # If we press both left and right, show the 'settings' screen
        if InputEvent.LEFT_BUTTON_PRESSED in events and InputEvent.RIGHT_BUTTON_PRESSED in events:
            logger.info("Left + Right buttons pressed, navigating to Settings")
            from hardware.screens.settings.settings import Settings

            return Settings()

        if InputEvent.RIGHT_BUTTON_PRESSED in events:
            logger.info("Right button pressed, navigating to BinCollections")
            from hardware.screens.bins.bin_collections import BinCollections

            return BinCollections()

        if events.contains_bin_press():
            logger.info("A bin button has been pressed")
            # If any bins are pressed, we need to see what the status of that bin is.
            # If it's actionable, 'prime' the bin!

            bin = events.get_first_bin_press().get_bin()

            if bin is None:
                logger.info("No bin found for button presses: " + str(events))
                return None

            logger.info(f"Found bin '{bin.name}' (id={bin.id}) related to the button press")

            # Get the next collection for the bin that was pressed

            # Check if the bin is 'actionable'
            next_collection = self._bin_collections.data.get_next_collection_for_bin(bin.id)

            if next_collection is None or next_collection.status != BinCollectionStatus.DUE_OUT:
                logger.info(f"No upcoming collections found for bin '{bin.name}' (id={bin.id})")

                if self._actively_confirming_bin_id is not None:
                    logger.info(f"Clearing active confirmation for bin id {self._actively_confirming_bin_id} since no actionable collection found")
                    self._actively_confirming_bin_id = None  # Clear any active confirmation since there's no
                else:
                    from hardware.screens.bins.single_bin_collection import SingleBinCollection
                    # The user wants to go to the 'single view' for this bin!
                    return SingleBinCollection(bin.id)
            else:
                if self._actively_confirming_bin_id == bin.id:
                    self._actively_confirming_bin_id = None
                    logger.info(f"Bin '{bin.name}' (id={bin.id}) active confirmation accepted, continuing with action")
                    with SessionLocal() as db:
                        repo = BinPutOutRepository(db)
                        repo.create(schemas.BinPutOutCreate(
                            bin_id=bin.id,
                            date_put_out_at=datetime.datetime.now()
                        ))
                    self._bin_collections.data.load_data()
                elif self._actively_confirming_bin_id is not None:
                    logger.info(f"Clearing active confirmation for bin id {self._actively_confirming_bin_id} since no actionable collection found")
                    self._actively_confirming_bin_id = None
                else:
                    logger.info(f"Bin '{bin.name}' (id={bin.id}) actionable, priming for confirmation")
                    self._actively_confirming_bin_id = bin.id
                # Prime the bin for confirmation

            self._update_outputs(drivers)

            return None

        return None

    def tick(self, drivers) -> Screen | None | QuitApp:
        if self._bin_collections.recently_updated:
            logger.debug("Bin collection data recently updated, refreshing outputs")
            self._update_outputs(drivers)

        return None

    def _update_outputs(self, drivers: Drivers):
        """
        Update the display with bin collection data

        We consider the LCD and the bins separately. The bins tell us about actions, the LCD tells us about current status.
        """

        logger.debug("Updating display with current bin collection data")

        # Get the next collections for each of the bins
        next_collections = self._bin_collections.data.get_next_collections_for_all_bins()

        # Handle no collections found in the future
        if self._actively_confirming_bin_id is not None:
            # Get the collection with the bin ID
            collection = next((c for c in next_collections if c.bin_id == self._actively_confirming_bin_id), None)
            if collection is None:
                return
            self._show_confirmation_lcd_and_lights(collection, drivers)
        elif len(next_collections) == 0:
            self._show_no_collections_found(drivers)
        else:
            self._show_upcoming_collections_lcd(next_collections, drivers)
            self._show_upcoming_collections_lights(next_collections, drivers)

        self._bin_collections.mark_update_handled()


    def _show_no_collections_found(self, drivers: Drivers):
        logger.debug("No upcoming collections found")
        drivers.lcd.display("No upcoming", "collections", drivers.lcd.TEXT_STYLE_CENTER)
        drivers.lights.all_off()

    def _show_upcoming_collections_lcd(self, next_collections: List[BinCollection], drivers: Drivers):
        # Handle displaying collections
        next_collection_at = min([c.collection_due_at for c in next_collections])
        if next_collection_at is None:
            return

        bin_names_due_next = [c for c in next_collections if c.collection_due_at.date() == next_collection_at.date()]
        days_until_next_due = math.ceil((next_collection_at.date() - datetime.date.today()).days)
        # Show the next upcoming collection on the LCD

        out_in_text = 'Out '
        if days_until_next_due == 0:
            out_in_text += 'today'
        elif days_until_next_due == 1:
            out_in_text += 'tomorrow'
        else:
            out_in_text += 'in ' + str(days_until_next_due) + ' days'

        drivers.lcd.display(
            out_in_text,
            "|".join([c.bin_name for c in bin_names_due_next]),
            drivers.lcd.TEXT_STYLE_CENTER,
            suffix='>' if self._bin_collections.data.has_collection_after(next_collection_at) is not None else None,
            )


    def _show_upcoming_collections_lights(self, next_collections: List[BinCollection], drivers: Drivers):
        def convert_collection_to_light_state(collection: BinCollection) -> LightState:
            """
                Map bin status to light state.
                    - Missed: Nothing
                    - Taken Out: Just light up
                    - Put out early: Nothing
                    - Collected: Nothing
                    - Due out: Phasing. If this bin ID is also saved in self._actively_confirming_with_bin, instead it should be flashing fast.
                    - Not yet due: Nothing
                    """

            if collection.status == BinCollectionStatus.TAKEN_OUT:
                return LightState.ON

            if collection.status == BinCollectionStatus.DUE_OUT:
                return LightState.PHASE

            return LightState.OFF

        # Determine light states
        drivers.lights.set_lights(
            *[convert_collection_to_light_state(c) for c in next_collections]
        )

    def _show_confirmation_lcd_and_lights(self, collection: BinCollection, drivers: Drivers):
        drivers.lcd.display(
            f"Confirm {collection.bin_name}",
            "is taken out?",
            drivers.lcd.TEXT_STYLE_CENTER,
        )
        drivers.lights.set_lights(
            *[LightState.FLASH_FAST if c == (collection.bin_position - 1) else LightState.OFF for c in range(4)]
        )


