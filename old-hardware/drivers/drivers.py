class Drivers:
    def __init__(self, lcd, lights, movement, buttons):
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