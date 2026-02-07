from RPi import GPIO

class Movement:
    MOTION_SENSOR_PIN = 9

    def __init__(self):
        GPIO.setup(self.MOTION_SENSOR_PIN, GPIO.IN)

    def movement_detected(self):
        return GPIO.input(self.MOTION_SENSOR_PIN) == GPIO.HIGH
