#!/home/toby/when-is-bins/python/.venv/bin/python
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

import RPi.GPIO as GPIO
from hardware.drivers.lcd import Lcd
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