from threading import Thread

import RPi.GPIO as GPIO
import time
from enum import Enum

class LightState(Enum):
    OFF = 0
    ON = 1
    PHASE = 2

class LightController:
    def __init__(self, pin):
        self.pin = pin
        self.pwm = GPIO.PWM(pin, 100)
        self.pwm.start(0)
        self._duty_cycle = 0
        self._duty_cycle_direction = 1
        self.should_phase = False

    def do_phase(self):
        self.pwm.ChangeDutyCycle(self._duty_cycle)
        if self._duty_cycle == 100:
            self._duty_cycle_direction = -1
        elif self._duty_cycle == 0:
            self._duty_cycle_direction = 1
        self._duty_cycle += self._duty_cycle_direction

    def stop(self):
        self.pwm.ChangeDutyCycle(0)
        # self.pwm.stop()
        time.sleep(1)
    def phase(self):
        self.should_phase = True

    def on(self):
        self.should_phase = False
        self.pwm.ChangeDutyCycle(100)

    def off(self):
        self.should_phase = False
        self.pwm.ChangeDutyCycle(0)

class Lights:
    POSITION_ONE_LED_PIN = 18
    POSITION_TWO_LED_PIN = 23
    POSITION_THREE_LED_PIN = 24
    POSITION_FOUR_LED_PIN = 25

    def __init__(self):
        GPIO.setup(self.POSITION_FOUR_LED_PIN, GPIO.OUT)
        GPIO.setup(self.POSITION_THREE_LED_PIN, GPIO.OUT)
        GPIO.setup(self.POSITION_ONE_LED_PIN, GPIO.OUT)
        GPIO.setup(self.POSITION_TWO_LED_PIN, GPIO.OUT)

        self._sleeping = False
        self._current_display = None
        self._phasing_thread = None

        self._bin_1_led = LightController(self.POSITION_ONE_LED_PIN)
        self._bin_2_led = LightController(self.POSITION_TWO_LED_PIN)
        self._bin_3_led = LightController(self.POSITION_THREE_LED_PIN)
        self._bin_4_led = LightController(self.POSITION_FOUR_LED_PIN)

        # State saved before sleeping
        self._saved_light_state = None

        self.all_off()


    def set_light_to_state(self, controller: LightController, state: LightState):
        if state == LightState.ON:
            controller.on()
        elif state == LightState.OFF:
            controller.off()
        elif state == LightState.PHASE:
            controller.phase()

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

        # If any are phasing and the thread is none, start
        if one == LightState.PHASE or two == LightState.PHASE or three == LightState.PHASE or four == LightState.PHASE:
            if self._phasing_thread is None or not self._phasing_thread.is_alive():
                self._start_phasing()

        # If none are phasing, stop the thread
        if one != LightState.PHASE and two != LightState.PHASE and three != LightState.PHASE and four != LightState.PHASE:
            self._stop_phasing()

    def cached(self, one, two, three, four):
        cache = [one, two, three, four]

        if(self._current_display is not None and self._current_display == cache):
            return True

        self._current_display = cache

        return False

    def sleep(self):
        if self._sleeping:
            return
        self.all_off(save_state = False)
        self._sleeping = True

    def wake(self):
        if not self._sleeping:
            return

        self._sleeping = False

        # Restore the saved state if it exists
        if self._saved_light_state is not None:
            # Clear the current display cache so set_lights will actually update
            self._current_display = None
            # Restore the saved light state
            self.set_lights(
                self._saved_light_state[0],
                self._saved_light_state[1],
                self._saved_light_state[2],
                self._saved_light_state[3]
            )

    def cleanup(self):
        self._stop_phasing()
        self.all_off()

    def all_off(self, save_state: bool = True):
        self.set_lights(LightState.OFF, LightState.OFF, LightState.OFF, LightState.OFF, save_state)

    def _start_phasing(self):
        if self._phasing_thread is not None:
            self._stop_phasing()
        self._phasing_thread = Thread(target=self._phase)
        self._phasing_thread.start()

    def _phase(self):
        # Set up the PWM for the pins
        pwms = []
        # for pin in self._pins_phasing:
        #     pwms.append(LightController(pin))

        pause_time = 0.01

        while True:
            if self._bin_1_led.should_phase is False and self._bin_2_led.should_phase is False and self._bin_3_led.should_phase is False and self._bin_4_led.should_phase is False:
                break

            if self._bin_1_led.should_phase:
                self._bin_1_led.do_phase()

            if self._bin_2_led.should_phase:
                self._bin_2_led.do_phase()

            if self._bin_3_led.should_phase:
                self._bin_3_led.do_phase()

            if self._bin_4_led.should_phase:
                self._bin_4_led.do_phase()

            time.sleep(pause_time)

    def _stop_phasing(self):
        self._bin_1_led.should_phase = False
        self._bin_2_led.should_phase = False
        self._bin_3_led.should_phase = False
        self._bin_4_led.should_phase = False

        if self._phasing_thread is not None:
            self._phasing_thread.join()
            self._phasing_thread = None
