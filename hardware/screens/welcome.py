from screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob
from screens.check_configuration import CheckConfiguration

# Shows a welcome message for 2 seconds
class WelcomeScreen(Screen):
    def __init__(self):
        self._finish_booting = False

    def schedule(self, schedule: Scheduler):
        schedule.every(2).seconds.do(self._finish_booting_app)

    def _finish_booting_app(self):
        self._finish_booting = True
        return CancelJob



    def show_initial_state(self, drivers):
        drivers.lcd.display('The Bindicator', 'When is bins?', drivers.lcd.TEXT_STYLE_CENTER)

    def redirect(self):
        if self._finish_booting:
            return CheckConfiguration()

        return None
