from typing import List

from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvents
import datetime

from hardware.utils.date_format import format_date
from hardware.screens.abstract_screen import Screen, QuitApp


class HardwareTest(Screen):

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        drivers.lcd.display('Hardware Test', format_date(datetime.date.today()), drivers.lcd.TEXT_STYLE_CENTER)
        drivers.lights.set_lights(LightState.PHASE, LightState.PHASE, LightState.PHASE, LightState.PHASE)

    def handle_inputs(self, events: List[InputEvents], drivers: Drivers = None):
        print(events)

        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            from hardware.screens.settings.settings import Settings

            return Settings()

