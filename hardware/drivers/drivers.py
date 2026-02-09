from hardware.drivers.buttons import Buttons
from hardware.drivers.lcd import Lcd
from hardware.drivers.lights import Lights
from hardware.drivers.movement import Movement
from hardware.drivers.mqtt import MqttClient
from typing import Optional
from hardware.utils.logging_config import setup_logger

logger = setup_logger('DRIVERS MANAGER')


class Drivers:
    def __init__(self, lcd: Lcd, lights: Lights, movement: Movement, buttons: Buttons, mqtt: Optional[MqttClient] = None):
        logger.info("Initializing Drivers manager")
        self.lcd = lcd
        self.lights = lights
        self.buttons = buttons
        self.movement = movement
        self.mqtt = mqtt
        logger.info("Drivers manager initialized")

    def cleanup(self):
        logger.info("Cleaning up all drivers")
        self.lcd.cleanup()
        self.lights.cleanup()
        logger.info("All drivers cleaned up")

    def sleep(self):
        logger.info("Putting all drivers to sleep")
        self.lcd.sleep()
        self.lights.sleep()
        logger.info("All drivers are now sleeping")

    def wake(self):
        logger.info("Waking all drivers")
        self.lcd.wake()
        self.lights.wake()
        logger.info("All drivers are now awake")
