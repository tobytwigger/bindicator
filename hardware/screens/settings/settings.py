from typing import List

from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvents
import datetime

from hardware.screens.settings.internet import Internet
from hardware.utils.date_format import format_date
from hardware.screens.abstract_screen import Screen, QuitApp


class Settings(Screen):

    options: List[str] = [
        "Hardware Test",
        "Restart Device",
        "Internet",
        "Back",
    ]

    def __init__(self):
        self.selected_option: int = 0

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        self._update_screen(drivers)
        drivers.lights.set_lights(LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF)

    def _update_screen(self, drivers: Drivers):
        drivers.lcd.display('Settings', self.options[self.selected_option] or "Unknown Option", drivers.lcd.TEXT_STYLE_CENTER, prefix="<", suffix=">")

    def handle_inputs(self, events: List[InputEvents], drivers: Drivers = None):
        # If we press both left and right, show the 'today' screen

        if InputEvents.LEFT_BUTTON_PRESSED in events:
            if self.selected_option > 0:
                self.selected_option -= 1
            else:
                self.selected_option = len(self.options) - 1

            self._update_screen(drivers)

        if InputEvents.RIGHT_BUTTON_PRESSED in events:
            if self.selected_option < len(self.options) - 1:
                self.selected_option += 1
            else:
                self.selected_option = 0

            self._update_screen(drivers)

        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            return self._activate_option()

        return None

    def _activate_option(self) -> Screen | None | QuitApp:
        if self.options[self.selected_option] == "Hardware Test":
            from hardware.screens.settings.hardware_tester import HardwareTester

            return HardwareTester()

        elif self.options[self.selected_option] == "Restart Device":
            return QuitApp()

        elif self.options[self.selected_option] == "Internet":
            return Internet()

        elif self.options[self.selected_option] == "Back":
            from hardware.screens.bins.bin_collections import BinCollections

            return BinCollections()

        return None