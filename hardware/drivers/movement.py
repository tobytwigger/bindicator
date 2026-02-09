from RPi import GPIO
from hardware.utils.logging_config import setup_logger

logger = setup_logger('MOVEMENT SENSOR')

class Movement:
    MOTION_SENSOR_PIN = 9

    def __init__(self):
        logger.info("Initializing Movement sensor")
        logger.debug(f"Setting up motion sensor on GPIO pin {self.MOTION_SENSOR_PIN}")
        GPIO.setup(self.MOTION_SENSOR_PIN, GPIO.IN)
        logger.info("Movement sensor initialized successfully")

    def movement_detected(self):
        return GPIO.input(self.MOTION_SENSOR_PIN) == GPIO.HIGH
