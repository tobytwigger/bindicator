from core.system_status.checker import SystemStatusChecker
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
        self._system_status = None
        self._is_checking_status = False

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering WelcomeScreen - displaying welcome message")
        drivers.lcd.display('The Bindicator', 'When is bins?', drivers.lcd.TEXT_STYLE_CENTER)

        # TODO Move to a thread
        self._check_system_status()


    def _check_system_status(self):
        self._is_checking_status = True
        logger.info("Performing system checks")
        self._system_status = SystemStatusChecker.run()
        print(self._system_status)
        if not self._system_status.wifi_connection_passed:
            logger.warning("WiFi connection check failed")
        if not self._system_status.user_has_bins_passed:
            logger.warning("Sensor check failed")

        self._is_checking_status = False

        return

    def tick(self, drivers):
        # TODO WIth thread, when thread is no longer running!
        # TODO: Handle if nothing there. Just go to Today?
        if self._is_checking_status is False and self._system_status is not None:
            return self._redirect_with_system_status()

    def _redirect_with_system_status(self):
        if not self._system_status.wifi_connection_passed:
            logger.info("Redirecting to FixWifiScreen due to failed WiFi check")
            from hardware.screens.fix_healthcheck.fix_wifi import FixWifiScreen
            return FixWifiScreen()

        if not self._system_status.user_has_bins_passed:
            logger.info("Redirecting to FixBinsScreen due to failed sensor check")
            from hardware.screens.fix_healthcheck.fix_bins import FixBinsScreen
            return FixBinsScreen()

        logger.info("All system checks passed, proceeding with normal boot flow")
        from hardware.screens.bins.today import Today

        return Today()