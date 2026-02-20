from typing import List

from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvent, InputEvents
import datetime

from hardware.screens.abstract_screen import Screen, QuitApp
from hardware.utils.logging_config import setup_logger
from hardware.utils.menu_manager import MenuManager, MenuItem

logger = setup_logger('SETTINGS SCREEN')


class Settings(Screen):

    def __init__(self):
        logger.info("Settings screen created")
        self.menu = MenuManager(
            menu_items=[
                MenuItem(
                    name="Remote Control",
                    on_ok=lambda: self._create_remote_control()
                ),
                MenuItem(
                    name="Internet",
                    on_ok=lambda: self._create_internet()
                ),
                MenuItem(
                    name="Updates",
                    on_ok=lambda: self._create_updates()
                ),
                MenuItem(
                    name="Restart Device",
                    on_ok=lambda: QuitApp()
                ),
                MenuItem(
                    name="Back",
                )
            ],
            on_back = lambda: self._create_bin_collections()
        )

    def _create_remote_control(self):
        from hardware.screens.settings.remote_control import RemoteControl
        return RemoteControl()

    def _create_internet(self):
        from hardware.screens.settings.internet import Internet
        return Internet()

    def _create_updates(self):
        from hardware.screens.settings.updates import Updates
        return Updates()

    def _create_bin_collections(self):
        from hardware.screens.bins.bin_collections import BinCollections

        return BinCollections()

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering Settings screen")
        self._update_screen(drivers)
        drivers.lights.set_lights(LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF)

    def _update_screen(self, drivers: Drivers):
        drivers.lcd.display('Settings', self.menu.selected_menu_item.name, drivers.lcd.TEXT_STYLE_CENTER, prefix="<", suffix=">")

    def handle_inputs(self, events: InputEvents, drivers: Drivers = None):
        # If we press both left and right, show the 'today' screen

        was_updated, screen_to_update = self.menu.handle_inputs(events)

        if screen_to_update is not None:
            return screen_to_update

        if was_updated:
            logger.debug(f"Menu selection updated to {self.menu.selected_menu_item.name}")
            self._update_screen(drivers)
            return None

        return None