from abc import ABC, abstractmethod
from schedule import Scheduler
from __future__ import annotations
from hardware.drivers.drivers import Drivers
from hardware.drivers.inputs import InputEvents
from hardware.main import QuitApp


class Screen(ABC):
    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        pass

    def tick(self, drivers) -> Screen | None | QuitApp:
        pass

    def handle_input(self, event: InputEvents):
        pass