from hardware.drivers.buttons import Buttons
from hardware.drivers.lcd import Lcd
from hardware.drivers.lights import Lights
from hardware.drivers.movement import Movement


class Drivers:
    def __init__(self, lcd: Lcd, lights: Lights, movement: Movement, buttons: Buttons):
        self.lcd = lcd
        self.lights = lights
        self.buttons = buttons
        self.movement = movement

    def cleanup(self):
        self.lcd.cleanup()
        self.lights.cleanup()

    def sleep(self):
        self.lcd.sleep()
        self.lights.sleep()

    def wake(self):
        self.lcd.wake()
        self.lights.wake()