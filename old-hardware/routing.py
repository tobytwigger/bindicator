import datetime

class Routing:

    def __init__(self, state):
        self._state = state

        # self.bin_data = ValueChangeNotifier(None)
        # self.bin_configuration = BinConfigValue()
        # self.selected_bin = ValueChangeNotifier(None)
        # self.visible_date = ValueChangeNotifier(None)
        # self.sleeping = ValueChangeNotifier(False)
        # self.home = HomeValue()

    def get_screen(self):
        # If the bin data is loading, show Loading.
        if self._state.bin_data.loading is True:
            from screens.loading_bin_day import LoadingBinDay

            return LoadingBinDay(self._state)


        # If there are no bins, show NoBins
        if self._state.bin_data.value.bin_days is None or len(self._state.bin_data.value.bin_days) == 0:
            from screens.loading_bin_day import NoBins

            return NoBins(self._state)

        # We now know there are bins

        visible_date = self._state.visible_date.value

        # If we have selected a bin, show the selected bin
        if self._state.selected_bin.value is not None:
            from screens.selected_bin import SelectedBin

            return SelectedBin(self._state)

        # If a visible date is now, show the today
        if visible_date is None or visible_date == datetime.date.today():
            from screens.today import Today

            return Today(self._state)

        from screens.next_bin_day import NextBinDay
        return NextBinDay(self._state)


        # # If there are bin days, show today
        # if self._state.bin_data.value.bin_days is not None and len(self._state.bin_data.value.bin_days) > 0:
        #     from screens.today import Today
        #
        #     return Today(self._state)
        # from screens.loading_bin_day import NoBins
        #
        #     return NoBins(self._state)
        #
        #
        #
        #
        #
        # # We now know we must have bin data
        #
        # # If a single bin has been selected, then show the selected bin
        # if self._state.selected_bin.value is not None:
        #     from screens.selected_bin import SelectedBin
        #
        #     return SelectedBin(self._state)
        #
        #
        # # If there's a visible date, show the next bin day
        # if self._state.visible_date.value is not None:
        #     from screens.next_bin_day import NextBinDay
        #
        #     return NextBinDay(self._state)
        #
        # return None