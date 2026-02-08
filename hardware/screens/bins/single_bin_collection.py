from typing import List
from contextlib import contextmanager

from core.database.database import SessionLocal
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


class SingleBinCollection(Screen):

    def __init__(self, bin_id: int):
        self._bin_id = bin_id
        self._bin_collection_explorer = BinCollectionExplorer()
        self._current_date = self._bin_collection_explorer.get_collection_date_after(
            datetime.date.today(), self._bin_id
        )

    @classmethod
    def from_input_events(cls, events: List[InputEvents]):
        if InputEvents.BIN_1_PRESSED in events:
            return cls(1)
        elif InputEvents.BIN_2_PRESSED in events:
            return cls(2)
        elif InputEvents.BIN_3_PRESSED in events:
            return cls(3)
        elif InputEvents.BIN_4_PRESSED in events:
            return cls(4)
        return None

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        self._display_correct_outputs(drivers)

    def handle_inputs(self, events: List[InputEvents], drivers: Drivers):
        # If we press both left and right, show the 'settings' screen
        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            from hardware.screens.settings.settings import Settings

            return Settings()

        if InputEvents.LEFT_BUTTON_PRESSED in events:
            previous_date = self._bin_collection_explorer.get_collection_date_before(self._current_date,
                                                                                     bin_id=self._bin_id)
            if previous_date is not None and previous_date >= datetime.date.today():
                self._current_date = previous_date
                self._display_correct_outputs(drivers)
                return None

        if InputEvents.RIGHT_BUTTON_PRESSED in events:
            next_date = self._bin_collection_explorer.get_collection_date_after(self._current_date, bin_id=self._bin_id)
            if next_date is not None and next_date >= datetime.date.today():
                self._current_date = next_date
                self._display_correct_outputs(drivers)
                return None

        if InputEvents.BIN_1_PRESSED in events or InputEvents.BIN_2_PRESSED in events or InputEvents.BIN_3_PRESSED in events or InputEvents.BIN_4_PRESSED in events:
            new_screen = SingleBinCollection.from_input_events(events)
            if new_screen._bin_id == self._bin_id:
                from hardware.screens.bins.bin_collections import BinCollections
                return BinCollections()
            else:
                return new_screen

        return None

    def tick(self, drivers) -> Screen | None | QuitApp:
        self._display_correct_outputs(drivers)

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

