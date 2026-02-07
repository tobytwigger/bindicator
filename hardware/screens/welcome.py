from hardware.drivers.drivers import Drivers
from hardware.screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob


# Shows a welcome message for 2 seconds
class WelcomeScreen(Screen):
    def __init__(self):
        self._finish_booting = False

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        schedule.every(2).seconds.do(self._finish_booting_app)
        drivers.lcd.display('The Bindicator', 'When is bins?', drivers.lcd.TEXT_STYLE_CENTER)

    def _finish_booting_app(self):
        self._finish_booting = True
        return CancelJob

    def tick(self, drivers):
        if self._finish_booting:
            from hardware.screens.today import Today

            return Today()

        return None
