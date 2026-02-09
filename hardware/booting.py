#!/home/toby/bindicator/.venv/bin/python
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
root_dir = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=root_dir / ".env")

sys.path.append(str(root_dir))

import RPi.GPIO as GPIO
from hardware.drivers.lcd import Lcd
import time
from hardware.utils.logging_config import setup_logger

logger = setup_logger('BOOT SCREEN')

def run():
    logger.info("========== BINDICATOR BOOT SCREEN ==========")
    logger.info("Initializing GPIO")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()

    logger.info("Creating LCD driver for boot screen")
    lcd = Lcd()

    logger.info("Displaying boot message")
    lcd.display('Booting...', '', lcd.TEXT_STYLE_CENTER)

    time.sleep(0.5)
    logger.info("Boot screen complete")



if __name__ == "__main__":
    run()