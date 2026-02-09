from threading import Thread

import RPi.GPIO as GPIO
import time
from enum import Enum
from hardware.utils.logging_config import setup_logger

logger = setup_logger('LIGHTS DRIVER')

class LightState(Enum):
    OFF = 0
    ON = 1
    PHASE = 2
    FLASH_FAST = 3  # 500ms toggle for "primed" state
    FLASH_SLOW = 4  # 1000ms toggle for success indicator

class LightController:
    def __init__(self, pin):
        self.pin = pin
        self.pwm = GPIO.PWM(pin, 100)
        self.pwm.start(0)
        self._duty_cycle = 0
        self._duty_cycle_direction = 1
        self.should_phase = False
        self.should_flash = False
        self.flash_interval = 0.5  # seconds between toggles
        self._flash_state = False  # current on/off state for flashing
        self._last_toggle_time = 0

    def do_phase(self):
        self.pwm.ChangeDutyCycle(self._duty_cycle)
        if self._duty_cycle == 100:
            self._duty_cycle_direction = -1
        elif self._duty_cycle == 0:
            self._duty_cycle_direction = 1
        self._duty_cycle += self._duty_cycle_direction

    def do_flash(self, current_time):
        """Toggle flash state if enough time has passed."""
        if current_time - self._last_toggle_time >= self.flash_interval:
            self._flash_state = not self._flash_state
            self._last_toggle_time = current_time
            if self._flash_state:
                self.pwm.ChangeDutyCycle(100)
            else:
                self.pwm.ChangeDutyCycle(0)

    def stop(self):
        self.pwm.ChangeDutyCycle(0)
        # self.pwm.stop()
        time.sleep(1)

    def flash_fast(self):
        self.should_phase = False
        self.should_flash = True
        self.flash_interval = 0.5
        self._last_toggle_time = time.time()

    def flash_slow(self):
        self.should_phase = False
        self.should_flash = True
        self.flash_interval = 1
        self._last_toggle_time = time.time()

    def phase(self):
        self.should_phase = True
        self.should_flash = False

    def on(self):
        self.should_phase = False
        self.should_flash = False
        self.pwm.ChangeDutyCycle(100)

    def off(self):
        self.should_phase = False
        self.should_flash = False
        self.pwm.ChangeDutyCycle(0)

class Lights:
    POSITION_ONE_LED_PIN = 18
    POSITION_TWO_LED_PIN = 23
    POSITION_THREE_LED_PIN = 24
    POSITION_FOUR_LED_PIN = 25

    def __init__(self):
        logger.info("Initializing Lights driver")
        logger.debug("Setting up LED GPIO pins")
        GPIO.setup(self.POSITION_FOUR_LED_PIN, GPIO.OUT)
        GPIO.setup(self.POSITION_THREE_LED_PIN, GPIO.OUT)
        GPIO.setup(self.POSITION_ONE_LED_PIN, GPIO.OUT)
        GPIO.setup(self.POSITION_TWO_LED_PIN, GPIO.OUT)

        self._sleeping = False
        self._current_display = None
        self._phasing_thread = None

        logger.debug("Creating LED controllers for 4 positions")
        self._bin_1_led = LightController(self.POSITION_ONE_LED_PIN)
        self._bin_2_led = LightController(self.POSITION_TWO_LED_PIN)
        self._bin_3_led = LightController(self.POSITION_THREE_LED_PIN)
        self._bin_4_led = LightController(self.POSITION_FOUR_LED_PIN)

        # State saved before sleeping
        self._saved_light_state = None

        self.all_off()
        logger.info("Lights driver initialized successfully")


    def set_light_to_state(self, controller: LightController, state: LightState):
        if state == LightState.ON:
            controller.on()
        elif state == LightState.OFF:
            controller.off()
        elif state == LightState.PHASE:
            controller.phase()
        elif state == LightState.FLASH_FAST:
            controller.flash_fast()
        elif state == LightState.FLASH_SLOW:
            controller.flash_slow()

    def set_lights(self, one: LightState, two: LightState, three: LightState, four: LightState, save_state: bool = True):
        # Save the state for wake restoration (save before checking sleep/cache)
        if save_state:
            self._saved_light_state = [one, two, three, four]

        if self._sleeping:
            return

        if self.cached(one, two, three, four):
            return

        self.set_light_to_state(self._bin_1_led, one)
        self.set_light_to_state(self._bin_2_led, two)
        self.set_light_to_state(self._bin_3_led, three)
        self.set_light_to_state(self._bin_4_led, four)

        # If any are phasing or flashing and the thread is none, start
        needs_thread = (one in [LightState.PHASE, LightState.FLASH_FAST, LightState.FLASH_SLOW] or
                       two in [LightState.PHASE, LightState.FLASH_FAST, LightState.FLASH_SLOW] or
                       three in [LightState.PHASE, LightState.FLASH_FAST, LightState.FLASH_SLOW] or
                       four in [LightState.PHASE, LightState.FLASH_FAST, LightState.FLASH_SLOW])

        if needs_thread:
            if self._phasing_thread is None or not self._phasing_thread.is_alive():
                self._start_phasing()

        # If none are phasing or flashing, stop the thread
        if not needs_thread:
            self._stop_phasing()

    def cached(self, one, two, three, four):
        cache = [one, two, three, four]

        if(self._current_display is not None and self._current_display == cache):
            return True

        self._current_display = cache

        return False

    def sleep(self):
        if self._sleeping:
            logger.debug("Sleep called but already sleeping")
            return
        logger.info("Putting lights to sleep")
        self.all_off(save_state = False)
        self._sleeping = True
        logger.info("Lights are now sleeping")

    def wake(self):
        if not self._sleeping:
            logger.debug("Wake called but already awake")
            return

        logger.info("Waking lights from sleep")
        self._sleeping = False

        # Restore the saved state if it exists
        if self._saved_light_state is not None:
            logger.debug(f"Restoring saved light state: {self._saved_light_state}")
            # Clear the current display cache so set_lights will actually update
            self._current_display = None
            # Restore the saved light state
            self.set_lights(
                self._saved_light_state[0],
                self._saved_light_state[1],
                self._saved_light_state[2],
                self._saved_light_state[3]
            )
        logger.info("Lights are now awake")

    def cleanup(self):
        logger.info("Cleaning up lights")
        self._stop_phasing()
        self.all_off()
        logger.info("Lights cleanup complete")

    def all_off(self, save_state: bool = True):
        self.set_lights(LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF, save_state)

    def _start_phasing(self):
        if self._phasing_thread is not None:
            self._stop_phasing()
        self._phasing_thread = Thread(target=self._phase)
        self._phasing_thread.start()

    def _phase(self):
        # Set up the PWM for the pins
        pause_time = 0.01

        while True:
            if (not self._bin_1_led.should_phase and not self._bin_1_led.should_flash and
                not self._bin_2_led.should_phase and not self._bin_2_led.should_flash and
                not self._bin_3_led.should_phase and not self._bin_3_led.should_flash and
                not self._bin_4_led.should_phase and not self._bin_4_led.should_flash):
                break

            current_time = time.time()

            if self._bin_1_led.should_phase:
                self._bin_1_led.do_phase()
            elif self._bin_1_led.should_flash:
                self._bin_1_led.do_flash(current_time)

            if self._bin_2_led.should_phase:
                self._bin_2_led.do_phase()
            elif self._bin_2_led.should_flash:
                self._bin_2_led.do_flash(current_time)

            if self._bin_3_led.should_phase:
                self._bin_3_led.do_phase()
            elif self._bin_3_led.should_flash:
                self._bin_3_led.do_flash(current_time)

            if self._bin_4_led.should_phase:
                self._bin_4_led.do_phase()
            elif self._bin_4_led.should_flash:
                self._bin_4_led.do_flash(current_time)

            time.sleep(pause_time)

    def _stop_phasing(self):
        self._bin_1_led.should_phase = False
        self._bin_2_led.should_phase = False
        self._bin_3_led.should_phase = False
        self._bin_4_led.should_phase = False
        self._bin_1_led.should_flash = False
        self._bin_2_led.should_flash = False
        self._bin_3_led.should_flash = False
        self._bin_4_led.should_flash = False

        if self._phasing_thread is not None:
            self._phasing_thread.join()
            self._phasing_thread = None
