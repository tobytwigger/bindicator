from typing import List

from hardware.drivers.drivers import Drivers
from hardware.drivers.lights import LightState
from schedule import Scheduler, CancelJob
from hardware.drivers.inputs import InputEvents
import datetime

from hardware.utils.date_format import format_date
from hardware.screens.abstract_screen import Screen, QuitApp
from dataclasses import dataclass
import threading
import socket

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
        return True
    except socket.error as ex:
        return False

class Internet(Screen):

    options: List[str] = [
        "Status",
        "Network Name",
        "Back",
    ]

    def __init__(self):
        self.selected_option: int = 0
        self.is_loading: bool = False
        self.internet_status: InternetStatus | None = None
        self._status_thread: threading.Thread | None = None

    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        self._start_status_check()
        self._update_screen(drivers)
        drivers.lights.set_lights(LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF)


    def handle_inputs(self, events: List[InputEvents], drivers: Drivers = None):
        if InputEvents.LEFT_BUTTON_PRESSED in events:
            if self.selected_option > 0:
                self.selected_option -= 1
            else:
                self.selected_option = len(self.options) - 1

            self._update_screen(drivers)

        if InputEvents.RIGHT_BUTTON_PRESSED in events:
            if self.selected_option < len(self.options) - 1:
                self.selected_option += 1
            else:
                self.selected_option = 0

            self._update_screen(drivers)

        if InputEvents.LEFT_BUTTON_PRESSED in events and InputEvents.RIGHT_BUTTON_PRESSED in events:
            return self._activate_option()

        return None

    def tick(self, drivers) -> Screen | None | QuitApp:
        self._update_screen(drivers)

    def _start_status_check(self):
        self.is_loading = True
        self.internet_status = None

        def check_status():
            # Simulate status check (replace with real check)
            from subprocess import check_output
            ssid = None

            scan_output = check_output(["iwlist", "wlan0", "scan"])
            scan_output = scan_output.decode("utf-8", errors="ignore")

            for line in scan_output.splitlines():
                line = line.strip()
                if line.startswith("ESSID"):
                    # Example line: ESSID:"MyNetwork"
                    parts = line.split('"')
                    if len(parts) > 1:
                        ssid = parts[1]

            has_internet_access = ping_internet()

            if ssid is None:
                self.internet_status = InternetStatus(
                    status="Disconnected",
                )

            self.internet_status = InternetStatus(
                status="Connected" if has_internet_access else "No Internet",
                ssid=ssid
            )
            self.is_loading = False

        self._status_thread = threading.Thread(target=check_status, daemon=True)
        self._status_thread.start()

    def _update_screen(self, drivers: Drivers):
        drivers.lcd.display(self.options[self.selected_option] or "Unknown Option", self._get_active_option_text() or "", drivers.lcd.TEXT_STYLE_CENTER, prefix="<", suffix=">")

    def _get_active_option_text(self) -> str | None:
         if self.options[self.selected_option] == "Status":
             if self.is_loading:
                 return "Checking..."
             elif self.internet_status is not None:
                 return self.internet_status.status
             else:
                 return "Try again later"
         elif self.options[self.selected_option] == "Network Name":
             if self.is_loading:
                 return "Checking..."
             elif self.internet_status is not None:
                 return self.internet_status.ssid
             else:
                 return "Try again later"

         return None

    def _activate_option(self) -> Screen | None | QuitApp:
        if self.options[self.selected_option] == "Back":
            from hardware.screens.settings.settings import Settings

            return Settings()

