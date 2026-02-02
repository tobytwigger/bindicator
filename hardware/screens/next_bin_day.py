from drivers.lights import LightState
from screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob
from database.db import Home, Bin
from data.bins import BinDayRepository
from drivers.inputs import InputEvents
import datetime

from utils.date_format import format_date
from utils.state import ScreenUsingState


class NextBinDay(ScreenUsingState):

    def handle_input(self, event: InputEvents):
        if event == InputEvents.LEFT_BUTTON_PRESSED:
            # If the visible date is equal to the first date, set to none
            if self._state.visible_date.value == self._state.bin_data.value.first_date() and self._state.selected_bin.value is None:
                self._state.visible_date.value = None
            # Otherwise, set to the date before
            else:
                previous_date = self._state.bin_data.value.date_before(self._state.visible_date.value)
                # If the previous date is either today or tomorrow, set the visible date to None
                if previous_date in [datetime.date.today(), datetime.date.today() + datetime.timedelta(days=1)]:
                    self._state.visible_date.value = None
                else:
                    self._state.visible_date.value = previous_date

        elif event == InputEvents.RIGHT_BUTTON_PRESSED:
            next_date = self._state.bin_data.value.next_date_after(self._state.visible_date.value, self._state.selected_bin.value)
            # If we do not have a selected bin, OR next_date is not None, set the visible date to the next date
            if next_date is not None:
                self._state.visible_date.value = next_date

        super().handle_input(event)

    def tick(self, drivers):
        super().tick(drivers)

        # Get the relevant bins
        bins = self._state.bin_data.value.get_for_date(self._state.visible_date.value)

        # Get whether we can go back and/or forward
        has_next_date = self._state.bin_data.value.next_date_after(self._state.visible_date.value) is not None
        has_previous_date = self._state.visible_date.value is not None

        if bins is None:
            drivers.lcd.display('No bins due', '', drivers.lcd.TEXT_STYLE_CENTER)
            drivers.lights.all_off()
        else:
            num_of_days_until_bins_date = (bins.date - datetime.date.today()).days

            drivers.lcd.display(
                format_date(bins.date),
                'In ' + str(num_of_days_until_bins_date) + ' ' + (
                    'day' if num_of_days_until_bins_date == 1 else 'days'),
                drivers.lcd.TEXT_STYLE_CENTER,
                prefix='<' if has_previous_date else None,
                suffix='>' if has_next_date else None
            )

            bin_state: list[LightState] = [LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF]

            for b in bins.bins:
                bin_state[b.position - 1] = LightState.ON

            drivers.lights.set_lights(
                bin_state[0],
                bin_state[1],
                bin_state[2],
                bin_state[3]
            )

