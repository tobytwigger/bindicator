from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob
from hardware.utils.logging_config import setup_logger

logger = setup_logger('WELCOME SCREEN')


# Shows a welcome message for 2 seconds
class WelcomeScreen(Screen):
    def __init__(self):
        logger.info("WelcomeScreen created")
        self._finish_booting = False

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering WelcomeScreen - displaying welcome message")
        schedule.every(2).seconds.do(self._finish_booting_app)
        drivers.lcd.display('The Bindicator', 'When is bins?', drivers.lcd.TEXT_STYLE_CENTER)

    def _finish_booting_app(self):
        logger.info("Welcome screen timer complete, transitioning to main screen")
        self._finish_booting = True
        return CancelJob

    def tick(self, drivers):
        if self._finish_booting:
            from hardware.screens.bins.today import Today

            logger.info("Transitioning to Today screen")
            return Today()

        return None
