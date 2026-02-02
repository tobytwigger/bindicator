from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import Model
from schedule import Scheduler
from data.bins import BinDayRepository
from database.db import Home, Bin
from drivers.inputs import InputEvents
from routing import Routing
from screens.abstract_screen import Screen
import datetime

class ValueChangeNotifier:
    def __init__(self, value=None, refresh=None, loading=False):
        self._value = value
        self._refresh = refresh
        self._has_changed = False
        self._observers = []
        self.loading = loading

    @property            # first decorate the getter method
    def value(self): # This getter method name is *the* name
        return self._value

    @value.setter
    def value(self, v):
        if not self._is_equal(v):
            self._value = v
            self._has_changed = True
            self.notify()

    def _is_equal(self, v):
        if isinstance(self._value, list) and isinstance(v, list):
            if all(isinstance(x, Model) for x in self._value) and all(isinstance(y, Model) for y in v):
                return all(model_to_dict(x) == model_to_dict(y) for x, y in zip(self._value, v)) and len(self._value) == len(v)
            return all(x == y for x, y in zip(self._value, v)) and len(self._value) == len(v)
        return self._value == v

    def handle_change(self):
        if self._has_changed:
            self.mark_handled()
            return True

        return False

    def has_changed(self):
        return self._has_changed

    def on_change(self, observer):
        self._observers.append(observer)

    def mark_handled(self):
        self._has_changed = False

    def notify(self):
        for observer in self._observers:
            observer()

    def refresh(self):
        if self._refresh:
            self.value = self._refresh()

class HomeValue(ValueChangeNotifier):
    def __init__(self):
        super().__init__(self.load_home(), self.load_home)

    def load_home(self):
        return Home.get_active()

class BinConfigValue(ValueChangeNotifier):
    def __init__(self):
        super().__init__(self.load_config(), self.load_config)

    def load_config(self):
        bins = []
        for bin in Bin.select().where(Bin.home_id == Home.get_active().id):
            bins.append(bin)

        return bins

class State:
    def __init__(self):
        self.bin_data = ValueChangeNotifier(None)
        self.bin_configuration = BinConfigValue()
        self.selected_bin = ValueChangeNotifier(None)
        self.visible_date = ValueChangeNotifier(None)
        self.sleeping = ValueChangeNotifier(False)
        self.home = HomeValue()

    def bin_data(self):
        return self.bin_data

    def bin_configuration(self):
        return self.bin_configuration

    def selected_bin(self):
        return self.selected_bin

    def visible_date(self):
        return self.visible_date

    def sleeping(self):
        return self.sleeping

    def home(self):
        return self.home

    def refresh(self):
        self.bin_data.refresh()
        self.bin_configuration.refresh()
        self.selected_bin.refresh()
        self.visible_date.refresh()
        self.sleeping.refresh()
        self.home.refresh()

    def load_bin_data(self):
        self.bin_data.loading = True
        self.bin_data.value = BinDayRepository(self.home.value, self.bin_configuration.value).get_bin_data()
        self.bin_data.loading = False
        first_date = self.bin_data.value.first_date()
        current_date = datetime.date.today()
        self.visible_date.value = min(first_date, current_date) if first_date is not None else current_date

class ScreenUsingState(Screen):
    def __init__(self, state: State = None):
        self._state = state or State()

    def schedule(self, schedule: Scheduler):
        schedule.every(20).seconds.do(self._refresh_state)
        schedule.every(1).minutes.do(self._state.load_bin_data)

    def redirect(self):
        screen = Routing(self._state).get_screen()

        if screen is not None and screen.__class__.__name__ != self.__class__.__name__:
            return screen

        return None

    def handle_input(self, event: InputEvents):
        if event == InputEvents.MOVEMENT_DETECTED:
            self._state.sleeping.value = False
        elif event == InputEvents.MOVEMENT_STOPPED:
            self._state.sleeping.value = True
        elif event == InputEvents.BIN_1_PRESSED or event == InputEvents.BIN_2_PRESSED or event == InputEvents.BIN_3_PRESSED or event == InputEvents.BIN_4_PRESSED:
            bin_number = None
            if event == InputEvents.BIN_1_PRESSED:
                bin_number = 1
            elif event == InputEvents.BIN_2_PRESSED:
                bin_number = 2
            elif event == InputEvents.BIN_3_PRESSED:
                bin_number = 3
            elif event == InputEvents.BIN_4_PRESSED:
                bin_number = 4

            if self._state.selected_bin.value == bin_number:
                self._state.selected_bin.value = None
                self._state.visible_date.value = None
            else:
                self._state.selected_bin.value = bin_number


    def _refresh_state(self):
        if self._state is not None:
            self._state.refresh()


    def tick(self, drivers):
        if self._state.sleeping.handle_change():
            if self._state.sleeping.value:
                drivers.sleep()
            else:
                drivers.wake()

        should_reload_bin_data = False

        if self._state.home.handle_change():
            should_reload_bin_data = True

        if self._state.bin_configuration.handle_change():
            should_reload_bin_data = True

        if should_reload_bin_data:
            self._state.load_bin_data()