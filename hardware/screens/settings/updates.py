from typing import List

from core.versions.current_version import get_current_version
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvent, InputEvents
import datetime

from hardware.screens.settings.settings import Settings
from hardware.screens.abstract_screen import Screen, QuitApp
from hardware.utils.logging_config import setup_logger
from hardware.utils.menu_manager import MenuManager, MenuItem

logger = setup_logger('UPDATES SCREEN')

class Updates(Screen):

    options: List[str] = [
        "Status",
        "Network Name",
        "Back",
    ]

    def __init__(self):
        logger.info("Internet screen created")
        self.menu = MenuManager(
            menu_items=[
                MenuItem(
                    name="Version",
                    text=lambda: f"{get_current_version()}",
                ),
            ],
            on_back = lambda: self._create_settings()
        )

    def _create_settings(self):
        from hardware.screens.settings.settings import Settings

        return Settings()

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering Internet screen")
        self._update_screen(drivers)
        drivers.lights.set_lights(LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF)

    def handle_inputs(self, events: InputEvents, drivers: Drivers = None):
        was_updated, screen_to_update = self.menu.handle_inputs(events)

        if screen_to_update is not None:
            return screen_to_update

        if was_updated:
            logger.debug(f"Menu selection updated to {self.menu.selected_menu_item.name}")
            self._update_screen(drivers)

        return None

    def _update_screen(self, drivers: Drivers):
        drivers.lcd.display(
            self.menu.selected_menu_item.name,
            self.menu.selected_menu_item.text, drivers.lcd.TEXT_STYLE_CENTER, prefix="<", suffix=">"
        )



