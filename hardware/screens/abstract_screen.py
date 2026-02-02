from abc import ABC, abstractmethod
from schedule import Scheduler

from drivers.inputs import InputEvents


class Screen(ABC):
    def schedule(self, schedule: Scheduler):
        pass

    def tick(self, drivers):
        pass

    def handle_input(self, event: InputEvents):
        pass

    def redirect(self):
        return None

    def show_initial_state(self, drivers):
        pass

    def should_quit(self):
        return False

    def on_left_button_pressed(self):
        pass