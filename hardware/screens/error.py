from screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob
import time

class ErrorScreen(Screen):
    def __init__(self):
        self._finish_saying_bye = False

    def schedule(self, schedule: Scheduler):
        schedule.every(3).seconds.do(self._finish_closing_app)

    def _finish_closing_app(self):
        self._finish_saying_bye = True
        return CancelJob

    def show_initial_state(self, drivers):
        drivers.lcd.display('Error!', 'System rebooting', drivers.lcd.TEXT_STYLE_CENTER)

    def should_quit(self):
        return self._finish_saying_bye