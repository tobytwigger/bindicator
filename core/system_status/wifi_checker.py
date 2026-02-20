from core.system_status.checker import SystemCheckerInterface
import requests

from hardware.utils.logging_config import setup_logger

logging = setup_logger('WIFI CHECKER')

class WifiChecker(SystemCheckerInterface):
    def check(self) -> bool:
        if self._is_wifi_connected(timeout=2):
            return True
        if self._is_wifi_connected(timeout=5):
            return True

        return False

    @classmethod
    def _is_wifi_connected(cls, timeout: int) -> bool:
        try:
            # Attempts to fetch a small amount of data from a known website
            requests.get('http://www.google.com', timeout=timeout)
            logging.debug("Connected to the Internet")
            return True
        except (requests.ConnectionError, requests.Timeout):
            logging.debug("No internet connection")

        return False

