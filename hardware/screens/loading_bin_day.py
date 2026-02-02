from screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob
from database.db import Home, Bin
from data.bins import BinDayRepository
from drivers.inputs import InputEvents
import datetime
from screens.today import Today
from utils.state import ValueChangeNotifier, ScreenUsingState, State


class LoadingBinDay(ScreenUsingState):

    def show_initial_state(self, drivers):
        self._state.load_bin_data()
        drivers.lcd.display('Loading bin day', '', drivers.lcd.TEXT_STYLE_CENTER)

class NoBins(ScreenUsingState):

    def show_initial_state(self, drivers):
        drivers.lcd.display('No bins set up', '', drivers.lcd.TEXT_STYLE_CENTER)

    def tick(self, drivers):
        drivers.lights.all_off()