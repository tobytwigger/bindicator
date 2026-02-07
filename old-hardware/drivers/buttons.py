import RPi.GPIO as GPIO

class Buttons:

    LEFT_BUTTON_PIN = 7
    RIGHT_BUTTON_PIN = 8

    BIN_1_PIN = 12
    BIN_2_PIN = 16
    BIN_3_PIN = 20
    BIN_4_PIN = 21

    def __init__(self):
        GPIO.setup(self.LEFT_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.RIGHT_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.BIN_1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.BIN_2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.BIN_3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.BIN_4_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def is_left_pressed(self):
        return GPIO.input(self.LEFT_BUTTON_PIN) == GPIO.HIGH

    def is_right_pressed(self):
        return GPIO.input(self.RIGHT_BUTTON_PIN) == GPIO.HIGH

    def is_bin_1_pressed(self):
        return GPIO.input(self.BIN_1_PIN) == GPIO.HIGH

    def is_bin_2_pressed(self):
        return GPIO.input(self.BIN_2_PIN) == GPIO.HIGH

    def is_bin_3_pressed(self):
        return GPIO.input(self.BIN_3_PIN) == GPIO.HIGH

    def is_bin_4_pressed(self):
        return GPIO.input(self.BIN_4_PIN) == GPIO.HIGH