from typing import List

from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvents
import datetime

from hardware.screens.settings.internet import Internet
from hardware.utils.date_format import format_date
from hardware.screens.abstract_screen import Screen, QuitApp
from hardware.utils.logging_config import setup_logger

logger = setup_logger('SETTINGS SCREEN')


class Settings(Screen):

    options: List[str] = [
        "Remote Control",
        "Restart Device",
        "Internet",
        "Back",
    ]

    def __init__(self):
        logger.info("Settings screen created")
        self.selected_option: int = 0

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering Settings screen")
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

            logger.debug(f"Left button pressed, selected option: {self.options[self.selected_option]}")
            self._update_screen(drivers)

        if InputEvents.RIGHT_BUTTON_PRESSED in events:
            if self.selected_option < len(self.options) - 1:
                self.selected_option += 1
            else:
                self.selected_option = 0

            logger.debug(f"Right button pressed, selected option: {self.options[self.selected_option]}")
            self._update_screen(drivers)

        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            logger.info(f"Both buttons pressed, activating option: {self.options[self.selected_option]}")
            return self._activate_option()

        return None

    def _activate_option(self) -> Screen | None | QuitApp:
        if self.options[self.selected_option] == "Remote Control":
            logger.info("Navigating to Remote Control screen")
            from hardware.screens.settings.remote_control import RemoteControl

            return RemoteControl()

        elif self.options[self.selected_option] == "Restart Device":
            logger.info("Restart Device selected, returning QuitApp")
            return QuitApp()

        elif self.options[self.selected_option] == "Internet":
            logger.info("Navigating to Internet screen")
            return Internet()

        elif self.options[self.selected_option] == "Back":
            logger.info("Navigating back to BinCollections screen")
            from hardware.screens.bins.bin_collections import BinCollections

            return BinCollections()

        return None