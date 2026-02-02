from drivers.lights import LightState
from screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob
from database.db import Home, Bin
from data.bins import BinDayRepository
from drivers.inputs import InputEvents
import datetime

from utils.date_format import format_date
from utils.state import ValueChangeNotifier, State, ScreenUsingState, HomeValue, BinConfigValue


class SelectedBin(ScreenUsingState):

    def handle_input(self, event: InputEvents):
        if event == InputEvents.LEFT_BUTTON_PRESSED:
            self._state.visible_date.value = self._state.bin_data.value.date_before(self._state.visible_date.value, self._state.selected_bin.value) or self._state.visible_date.value
        elif event == InputEvents.RIGHT_BUTTON_PRESSED:
            next_date = self._state.bin_data.value.next_date_after(self._state.visible_date.value, self._state.selected_bin.value)
            self._state.visible_date.value = next_date or self._state.visible_date.value

        super().handle_input(event)

    def show_initial_state(self, drivers):
        # Set the visible date to the first bin date
        self._state.visible_date.value = self._state.bin_data.value.first_date(self._state.selected_bin.value)

    def _get_bin(self):
        """

        :return: Bin or None
        """
        for bin in self._state.bin_configuration.value:
            if bin.position == self._state.selected_bin.value:
                return bin

        return None

    def tick(self, drivers):
        super().tick(drivers)

        # Get the name of the selected bin
        bin = self._get_bin()

        if bin is None:
            drivers.lcd.display('No bin found', '', drivers.lcd.TEXT_STYLE_CENTER)
            drivers.lights.all_off()
            return

        dates = self._state.bin_data.value.get_dates_for_bin(bin.position)

        # If the visible date is not valid, make it valid
        if len(dates) > 0 and (self._state.visible_date.value is None or self._state.visible_date.value not in dates):
            self._state.visible_date.value = dates[0]


        if self._state.visible_date.value is None:
            drivers.lcd.display('No dates found', '', drivers.lcd.TEXT_STYLE_CENTER)
            drivers.lights.all_off()
        else:
            # Check the dates array to see if we have a date that occurs after the visible date
            has_next_date = dates.index(self._state.visible_date.value) < len(dates) - 1
            has_previous_date = dates.index(self._state.visible_date.value) > 0

            drivers.lcd.display(
                format_date(self._state.visible_date.value),
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
