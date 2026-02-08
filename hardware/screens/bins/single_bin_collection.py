from typing import List
from contextlib import contextmanager

from core.database.database import SessionLocal
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen, QuitApp
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvents
import datetime
from core.scheduler.scheduler import Scheduler as BinScheduler
from core.scheduler.scheduler import BinCollectionExplorer
from core.database import models
from hardware.utils.date_format import format_date
from hardware.screens.abstract_screen import Screen


class SingleBinCollection(Screen):

    def __init__(self):
        self._current_date = datetime.date.today()
        self._bin_collection_explorer = BinCollectionExplorer()

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        self._display_correct_outputs(drivers)
        drivers.lcd.display('Today', format_date(datetime.date.today()), drivers.lcd.TEXT_STYLE_CENTER)
        drivers.lights.set_lights(LightState.ON, LightState.ON, LightState.ON, LightState.ON)

    def handle_inputs(self, events: List[InputEvents], drivers: Drivers):
        # If we press both left and right, show the 'settings' screen
        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            from hardware.screens.settings.settings import Settings

            return Settings()

        return None

    def tick(self, drivers) -> Screen | None | QuitApp:
        self._display_correct_outputs(drivers)

        return None

    def _display_correct_outputs(self, drivers: Drivers):
        bins_due = self._bin_collection_explorer.get_bins_due_out_on(self._current_date)
        next_out = self._bin_collection_explorer.get_next_collection_date_after(self._current_date)

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
            bin_state[b.position - 1] = LightState.PHASE

        drivers.lights.set_lights(
            bin_state[0],
            bin_state[1],
            bin_state[2],
            bin_state[3]
        )

        return


    def _display_no_bins_due(self, drivers, days_until_next_due: int | None):
        drivers.lcd.display(
            'No bins due',
            'Out in ' + str(days_until_next_due) + ' ' + ('day' if days_until_next_due == 1 else 'days'),
            drivers.lcd.TEXT_STYLE_CENTER,
            suffix='>' if days_until_next_due is not None else None,
        )

        drivers.lights.all_off()
