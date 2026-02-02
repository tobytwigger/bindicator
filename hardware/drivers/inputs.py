from drivers.buttons import Buttons
from drivers.movement import Movement
import time
from drivers.drivers import Drivers
from enum import Enum
import time

# class syntax

class InputEvents(Enum):
    LEFT_BUTTON_PRESSED = 1
    RIGHT_BUTTON_PRESSED = 2
    MOVEMENT_DETECTED = 3
    MOVEMENT_STOPPED = 4
    BIN_1_PRESSED = 5
    BIN_2_PRESSED = 6
    BIN_3_PRESSED = 7
    BIN_4_PRESSED = 8

class Inputs:
    def __init__(self, drivers: Drivers, timeout):
        self._drivers = drivers
        self._throttle = {}
        self._movement_timeout = timeout
        self._movement_detected_at = time.time()

    def listen(self):
        events = []

        if self._drivers.movement.movement_detected():
            if self._movement_detected_at is None:
                events.append(InputEvents.MOVEMENT_DETECTED)
            self._movement_detected_at = time.time()

        if self._movement_detected_at and time.time() - self._movement_detected_at > self._movement_timeout:
            events.append(InputEvents.MOVEMENT_STOPPED)
            self._movement_detected_at = None

        if self._drivers.buttons.is_left_pressed():
            if self.throttle(InputEvents.LEFT_BUTTON_PRESSED, 0.3):
                events.append(InputEvents.LEFT_BUTTON_PRESSED)

        if self._drivers.buttons.is_right_pressed():
            if self.throttle(InputEvents.RIGHT_BUTTON_PRESSED, 0.3):
                events.append(InputEvents.RIGHT_BUTTON_PRESSED)

        if self._drivers.buttons.is_bin_1_pressed():
            if self.throttle(InputEvents.BIN_1_PRESSED, 0.3):
                events.append(InputEvents.BIN_1_PRESSED)

        if self._drivers.buttons.is_bin_2_pressed():
            if self.throttle(InputEvents.BIN_2_PRESSED, 0.3):
                events.append(InputEvents.BIN_2_PRESSED)

        if self._drivers.buttons.is_bin_3_pressed():
            if self.throttle(InputEvents.BIN_3_PRESSED, 0.3):
                events.append(InputEvents.BIN_3_PRESSED)

        if self._drivers.buttons.is_bin_4_pressed():
            if self.throttle(InputEvents.BIN_4_PRESSED, 0.3):
                events.append(InputEvents.BIN_4_PRESSED)

        return events

    def throttle(self, key, timeout):
        if key in self._throttle and time.time() - self._throttle[key] < timeout:
            return False

        self._throttle[key] = time.time()
        return True
