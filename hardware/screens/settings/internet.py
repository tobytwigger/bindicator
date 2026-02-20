from typing import List

from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvent, InputEvents
import datetime

from hardware.utils.date_format import format_date
from hardware.screens.abstract_screen import Screen, QuitApp
from dataclasses import dataclass
import threading
import socket
from hardware.utils.logging_config import setup_logger
from hardware.utils.menu_manager import MenuItem, MenuManager

logger = setup_logger('INTERNET SCREEN')

@dataclass
class InternetStatus:
    status: str
    ssid: str | None = None

def ping_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        logger.debug(f"Internet ping successful to {host}:{port}")
        return True
    except socket.error as ex:
        logger.debug(f"Internet ping failed to {host}:{port}: {ex}")
        return False

class Internet(Screen):

    def __init__(self):
        logger.info("Internet screen created")
        self.menu = MenuManager(
            menu_items=[
                MenuItem(
                    name="Status",
                    text=lambda: "Checking..." if self.is_loading else (self.internet_status.status if self.internet_status else "Try again later")
                ),
                MenuItem(
                    name="Network Name",
                    text=lambda: "Checking..." if self.is_loading else (self.internet_status.ssid if self.internet_status and self.internet_status.ssid else "Try again later")
                ),
            ],
            on_back = lambda: self._create_settings()
        )
        self.is_loading: bool = False
        self.internet_status: InternetStatus | None = None
        self._status_thread: threading.Thread | None = None

    def _create_settings(self):
        from hardware.screens.settings.settings import Settings

        return Settings()

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        logger.info("Entering Internet screen")
        self._start_status_check()
        drivers.lights.set_lights(LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF)
        self._update_screen(drivers)


    def handle_inputs(self, events: InputEvents, drivers: Drivers = None):
        was_updated, screen_to_update = self.menu.handle_inputs(events)

        if screen_to_update is not None:
            return screen_to_update

        if was_updated:
            logger.debug(f"Menu selection updated to {self.menu.selected_menu_item.name}")
            self._update_screen(drivers)

        return None

    def tick(self, drivers) -> Screen | None | QuitApp:
        self._update_screen(drivers)

        return None

    def _start_status_check(self):
        logger.info("Starting internet status check in background thread")
        self.is_loading = True
        self.internet_status = None

        def check_status():
            logger.debug("Status check thread started")
            # Simulate status check (replace with real check)
            from subprocess import check_output
            ssid = None

            try:
                logger.debug("Scanning for WiFi networks")
                scan_output = check_output(["iwlist", "wlan0", "scan"])
                scan_output = scan_output.decode("utf-8", errors="ignore")

                for line in scan_output.splitlines():
                    line = line.strip()
                    if line.startswith("ESSID"):
                        # Example line: ESSID:"MyNetwork"
                        parts = line.split('"')
                        if len(parts) > 1:
                            ssid = parts[1]
                            logger.debug(f"Found SSID: {ssid}")
                            break
            except Exception as e:
                logger.error(f"Error scanning WiFi: {e}", exc_info=True)

            logger.debug("Checking internet connectivity")
            has_internet_access = ping_internet()

            if ssid is None:
                logger.info("No WiFi network detected, status: Disconnected")
                self.internet_status = InternetStatus(
                    status="Disconnected",
                )
            else:
                status_str = "Connected" if has_internet_access else "No Internet"
                logger.info(f"WiFi status: {status_str}, SSID: {ssid}")
                self.internet_status = InternetStatus(
                    status=status_str,
                    ssid=ssid
                )
            self.is_loading = False
            logger.debug("Status check complete")

        self._status_thread = threading.Thread(target=check_status, daemon=True)
        self._status_thread.start()

    def _update_screen(self, drivers: Drivers):
        drivers.lcd.display(
            self.menu.selected_menu_item.name,
            self.menu.selected_menu_item.text, drivers.lcd.TEXT_STYLE_CENTER, prefix="<", suffix=">")

