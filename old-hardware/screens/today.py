from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob
from hardware.database.db import Home, Bin, BinDay
from hardware.data.bins import BinDayRepository
from hardware.drivers.inputs import InputEvents
import datetime
from playhouse.shortcuts import model_to_dict, dict_to_model
from hardware.utils.date_format import format_date
from hardware.utils.state import ValueChangeNotifier, ScreenUsingState, State


class Today(ScreenUsingState):

    def __init__(self, state: State):
        super().__init__(state)
        self._currently_due_bins = {}

    def handle_input(self, event: InputEvents):
        if event == InputEvents.RIGHT_BUTTON_PRESSED:
            # Set to the first date after tomorrow
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            self._state.visible_date.value = self._state.bin_data.value.next_date_after(tomorrow)

        if event == InputEvents.BIN_1_PRESSED or event == InputEvents.BIN_2_PRESSED or event == InputEvents.BIN_3_PRESSED or event == InputEvents.BIN_4_PRESSED:
            # We have pressed one of the bins. We now need to mark the bin as taken out, if it's currently due.
            bin_number = None
            if event == InputEvents.BIN_1_PRESSED:
                bin_number = 1
            elif event == InputEvents.BIN_2_PRESSED:
                bin_number = 2
            elif event == InputEvents.BIN_3_PRESSED:
                bin_number = 3
            elif event == InputEvents.BIN_4_PRESSED:
                bin_number = 4

            if bin_number is not None:
                # Check if the given bin position is present as .position in self._currently_due_bins
                if self._currently_due_bins.get(bin_number) is not None:
                    bin = self._currently_due_bins[bin_number]
                    bin.mark_as_taken_out()
                    self._currently_due_bins[bin_number] = None
                    return


        super().handle_input(event)

    def tick(self, drivers):
        super().tick(drivers)

        current_date = datetime.date.today()
        bins_today = self._state.bin_data.value.get_for_date(current_date)

        if bins_today is not None:
            self.show_bins_due(drivers, current_date, bins_today)
            return

        tomorrow = current_date + datetime.timedelta(days=1)
        bins_tomorrow = self._state.bin_data.value.get_for_date(tomorrow)

        if bins_tomorrow is not None:
            self.show_bins_due(drivers, tomorrow, bins_tomorrow)
            return

        next_bins = self._state.bin_data.value.next_date_after(current_date)
        num_of_days_until_next_bins = (next_bins - current_date).days

        self.show_no_bins_due(drivers, num_of_days_until_next_bins)


    def show_bins_due(self, drivers, date, bins):

        next_bins = self._state.bin_data.value.next_date_after(date)

        bins_as_text = ''
        for b in bins.bins:
            bins_as_text += b.name + ', '

        drivers.lcd.display(
            format_date(date),
            bins_as_text,
            drivers.lcd.TEXT_STYLE_CENTER,
            suffix='>' if next_bins is not None else None,
        )

        bin_state: list[LightState] = [LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF]

        # If the date is today, then the bin is always due
        # If the date is tomorrow, then the bin is only due if the home value is set to put out the bin the day before
        bins_are_due = False
        if date == datetime.date.today():
            bins_are_due = True
        elif date == datetime.date.today() + datetime.timedelta(days=1) and getattr(self._state.home.value, "put_out_day_before", True):
            bins_are_due = True

        currently_due_bins = {}

        for b in bins.bins:
            # TODO Check if bin has been taken out already
            is_due_out = bins_are_due and getattr(b, "is_taken_out", False) is False
            if is_due_out:
                currently_due_bins[b.position] = b
            bin_state[b.position - 1] = LightState.PHASE if is_due_out else LightState.ON

        self._currently_due_bins = currently_due_bins
        drivers.lights.set_lights(
            bin_state[0],
            bin_state[1],
            bin_state[2],
            bin_state[3]
        )

        return

    def show_no_bins_due(self, drivers, days_until_next_due: int or None):
        drivers.lcd.display(
            'No bins due',
            'Out in ' + str(days_until_next_due) + ' ' + ('day' if days_until_next_due == 1 else 'days'),
            drivers.lcd.TEXT_STYLE_CENTER,
            suffix='>' if days_until_next_due is not None else None,
        )

        drivers.lights.all_off()
