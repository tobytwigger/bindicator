from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

from schedule import Scheduler
from hardware.drivers.drivers import Drivers
from hardware.drivers.inputs import InputEvents


class Screen(ABC):
    def on_enter(self, schedule: Scheduler, drivers: Drivers):
        pass

    def on_exit(self, drivers: Drivers):
        pass

    def tick(self, drivers) -> Screen | None | QuitApp:
        pass

    def handle_inputs(self, events: List[InputEvents], drivers: Drivers):
        pass

class QuitApp:
    pass
