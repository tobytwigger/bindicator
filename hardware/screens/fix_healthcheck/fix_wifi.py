from core.system_status.checker import SystemStatusChecker
from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from hardware.screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob
from hardware.utils.logging_config import setup_logger

logger = setup_logger('WELCOME SCREEN')


# Shows a welcome message for 2 seconds
class FixWifiScreen(Screen):
    def __init__(self):
        logger.info("FixWifiScreen created")

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering FixWifiScreen - displaying message")
        drivers.lcd.display('No Internet', 'Connect to the bindicator wifi', drivers.lcd.TEXT_STYLE_CENTER)
