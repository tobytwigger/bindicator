import RPi.GPIO as GPIO
from drivers.lcd import Lcd
import time

def run():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()

    lcd = Lcd()


    lcd.display('Booting...', '', lcd.TEXT_STYLE_CENTER)

    time.sleep(0.5)



if __name__ == "__main__":
    run()