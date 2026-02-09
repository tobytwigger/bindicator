from hardware.drivers.drivers import Drivers
from hardware.screens.abstract_screen import Screen, QuitApp
from schedule import Scheduler, CancelJob
from hardware.utils.logging_config import setup_logger

logger = setup_logger('GOODBYE SCREEN')


class GoodbyeScreen(Screen):
    def __init__(self):
        logger.info("GoodbyeScreen created")
        self._finish_saying_bye = False

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering GoodbyeScreen - displaying goodbye message")
        drivers.lcd.display('Goodbye', '', drivers.lcd.TEXT_STYLE_CENTER)
        schedule.every(2).seconds.do(self._finish_closing_app)

    def _finish_closing_app(self):
        logger.info("Goodbye screen timer complete, application will quit")
        self._finish_saying_bye = True
        return CancelJob

    def tick(self, drivers) -> Screen | None | QuitApp:
        if self._finish_saying_bye:
            logger.info("Returning QuitApp signal")
            return QuitApp()

        return None