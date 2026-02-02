#!/home/toby/when-is-bins/python/.venv/bin/python

import RPi.GPIO as GPIO
import time
import signal
import schedule
from drivers.lcd import Lcd
from drivers.lights import Lights, LightState
from drivers.movement import Movement
import threading
from drivers.buttons import Buttons
from drivers.drivers import Drivers
from drivers.inputs import Inputs
from config.config import ConfigRepository
from screens.check_configuration import ConfigurationChecker, CheckConfiguration
from screens.goodbye import GoodbyeScreen
from screens.error import ErrorScreen
from screens.welcome import WelcomeScreen
from screens.abstract_screen import Screen
import logging

should_kill = False

def sigterm_handler(signal, frame):
    global should_kill
    should_kill = True

def log_error(e):
    print(e)

def run():
    signal.signal(signal.SIGTERM, sigterm_handler)

    set_up_gpio()

    config = ConfigRepository().get()

    drivers = Drivers(
        Lcd(),
        Lights(),
        Movement(),
        Buttons(),
    )

    inputs = Inputs(
        drivers,
        config.timeout,
    )

    screen = WelcomeScreen()

    runner = AppRunner(drivers, inputs)
    runner.set_quitting_screen(GoodbyeScreen())
    try:
        runner.run(screen)
    except Exception as e:
        runner.set_quitting_screen(ErrorScreen())
        runner.handle_exception(e)

def set_up_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)


class AppRunner:
    def __init__(self, drivers: Drivers, inputs: Inputs):
        self._quitting_screen = None
        self._drivers = drivers
        self._stop_schedule = None
        self._schedule = None
        self._redirect_to_config = False
        self._inputs = inputs

    def _run_schedule_in_background(self):
        """Continuously run, while executing pending jobs at each
        elapsed time interval.
        @return cease_continuous_run: threading. Event which can
        be set to cease continuous run. Please note that it is
        *intended behavior that run_continuously() does not run
        missed jobs*. For example, if you've registered a job that
        should run every minute and you set a continuous run
        interval of one hour then your job won't be run 60 times
        at each interval but only once.
        """
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    self._schedule.run_pending()
                    time.sleep(1)

        continuous_thread = ScheduleThread()
        continuous_thread.start()
        return cease_continuous_run

    def run(self, screen: Screen or None):
        while screen is not None:
            # Create a scheduler
            self._schedule = schedule.Scheduler()

            # Add a regular job to check configuration
            self._schedule.every(1).minute.do(self._check_configuration)
            self._schedule.every(1).minute.do(self._check_settings)

            # Let the screen define its schedule
            screen.schedule(self._schedule)

            # Start the scheduler running in the background
            self._stop_schedule = self._run_schedule_in_background()

            # Show the initial state of the screen
            screen.show_initial_state(self._drivers)

            # Start the screen running properly
            try:
                while True:
                    ## Result of this loop is to populate the screen variable

                    # Check if a redirect is needed
                    next_screen = screen.redirect()
                    if next_screen is not None:
                        self._cleanup(screen)
                        screen = next_screen
                        break  # Break inner loop to transition to next_screen

                    # Check if the app should quit
                    if should_kill or screen.should_quit():
                        screen = None
                        break

                    # Listen for any inputs
                    events = self._inputs.listen()

                    # Pass the events to the screen
                    if len(events) > 0:
                        for event in events:
                            screen.handle_input(event)

                    # Redirect to the config page if config is not valid
                    if self._redirect_to_config and not screen is None and not isinstance(screen, CheckConfiguration):
                        self._redirect_to_config = False
                        self._cleanup(screen)
                        screen = CheckConfiguration()
                        break

                    # Tick the screen
                    screen.tick(self._drivers)
                    time.sleep(0.08)

            except KeyboardInterrupt:
                # Do nothing
                screen = None

            # To get to this point, either `run` has been called with no screen, or the screen has asked for the app to quit
            self._cleanup(screen)
        self._quit()




    def _check_configuration(self):
        checker = ConfigurationChecker()
        result = checker.validate()
        if not result.is_valid():
            self._redirect_to_config = True

    def _check_settings(self):
        self._inputs._movement_timeout = ConfigRepository().get().timeout

    def _cleanup(self, screen):
        if self._stop_schedule is not None:
            self._stop_schedule.set()
            self._drivers.cleanup()


    def _quit(self):
        if self._quitting_screen is not None:
            quitting_screen = self._quitting_screen
            self._quitting_screen = None
            return self.run(quitting_screen)

        GPIO.cleanup()

    def handle_exception(self, e):
        logging.exception('An error occurred')
        self._quit()

    def set_quitting_screen(self, quitting_screen: Screen):
        self._quitting_screen = quitting_screen


if __name__ == "__main__":
    run()

