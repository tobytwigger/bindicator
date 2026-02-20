from hardware.drivers.drivers import Drivers
from hardware.screens.abstract_screen import Screen, QuitApp
from schedule import Scheduler, CancelJob
from hardware.utils.logging_config import setup_logger

logger = setup_logger('ERROR SCREEN')

class ErrorScreen(Screen):
    def __init__(self, error: Exception):
        self._error = error
        logger.error("ErrorScreen created - fatal error occurred")
        self._finish_saying_bye = False

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.error("Entering ErrorScreen - displaying error message")
        logger.error(f"Fatal error occurred: {self._error}", exc_info=self._error)
        logger.error(f"Stack trace: {self._error.__traceback__}")

        drivers.lcd.display('Error!', 'System rebooting', drivers.lcd.TEXT_STYLE_CENTER)
        schedule.every(3).seconds.do(self._finish_closing_app)

    def _finish_closing_app(self):
        logger.error("Error screen timer complete, application will quit")
        self._finish_saying_bye = True
        return CancelJob

    def tick(self, drivers) -> Screen | None | QuitApp:
        if self._finish_saying_bye:
            logger.error("Returning QuitApp signal after error")
            return QuitApp()

        return None