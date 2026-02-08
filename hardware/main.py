#!/home/toby/when-is-bins/python/.venv/bin/python
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from hardware.screens.flash_messages.error import ErrorScreen
import RPi.GPIO as GPIO
import signal
from hardware.drivers.lcd import Lcd
from hardware.drivers.lights import Lights
from hardware.drivers.movement import Movement
from hardware.drivers.buttons import Buttons
from hardware.drivers.mqtt import MqttClient
from hardware.screens.flash_messages.goodbye import GoodbyeScreen
from hardware.screens.flash_messages.welcome import WelcomeScreen
import logging
import time
import schedule
import threading
from hardware.drivers.drivers import Drivers
from hardware.drivers.inputs import Inputs
from hardware.screens.abstract_screen import Screen, QuitApp

# Configure logger to output all levels to stdout
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


should_kill = False

def sigterm_handler(signal, frame):
    global should_kill
    should_kill = True

def log_error(e):
    print(e)

def run():
    signal.signal(signal.SIGTERM, sigterm_handler)

    set_up_gpio()

    # Create MQTT client for publishing GPIO events
    mqtt_client = MqttClient()
    drivers = Drivers(
        Lcd(),
        Lights(),
        Movement(),
        Buttons(),
        mqtt_client,
    )

    inputs = Inputs(
        drivers,
        mqtt_client=mqtt_client,
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

    def run(self, screen: Screen | None):
        # Create a scheduler
        self._schedule = schedule.Scheduler()

        # Add a regular job to check configuration
        self._schedule.every(1).minute.do(self._check_configuration)
        self._schedule.every(1).minute.do(self._check_settings)

        # Start the input polling thread
        self._inputs.start()

        while screen is not None:
            # Fire the on_enter event, so screens can set up schedules and show initial states
            screen.on_enter(self._schedule, self._drivers)

            # Start the scheduler running in the background
            self._stop_schedule = self._run_schedule_in_background()

            # Start the screen running properly
            try:
                while True:

                    result = screen.tick(self._drivers)

                    # Check if the app should quit
                    if should_kill or isinstance(result, QuitApp):
                        screen.on_exit(self._drivers)
                        screen = None
                        break

                    # Check if a redirect is needed
                    if isinstance(result, Screen):
                        screen.on_exit(self._drivers)
                        self._cleanup()
                        screen = result
                        break  # Break inner loop to transition to next_screen

                    # Listen for any inputs
                    events = self._inputs.listen()

                    # Pass the events to the screen
                    if len(events) > 0:
                        result = screen.handle_inputs(events, self._drivers)

                        # Check if the app should quit
                        if should_kill or isinstance(result, QuitApp):
                            screen.on_exit(self._drivers)
                            screen = None
                            break

                        # Check if a redirect is needed
                        if isinstance(result, Screen):
                            screen.on_exit(self._drivers)
                            self._cleanup()
                            screen = result
                            break  # Break inner loop to transition to next_screen

                    # Redirect to the config page if config is not valid
                    # if self._redirect_to_config and screen is not None and not isinstance(screen, CheckConfiguration):
                    #     self._redirect_to_config = False
                    #     self._cleanup()
                    #     screen = CheckConfiguration()
                    #     break

                    time.sleep(0.08)

            except KeyboardInterrupt:
                if screen is not None:
                    screen.on_exit(self._drivers)

                # Do nothing
                screen = None

            # To get to this point, either `run` has been called with no screen, or the screen has asked for the app to quit
            self._cleanup()

        self._quit()




    def _check_configuration(self):
        pass
        # checker = ConfigurationChecker()
        # result = checker.validate()
        # if not result.is_valid():
        #     self._redirect_to_config = True

    def _check_settings(self):
        pass
        # self._inputs._movement_timeout = ConfigRepository().get().timeout

    def _cleanup(self):
        if self._stop_schedule is not None:
            self._stop_schedule.set()
            self._drivers.cleanup()

    def _quit(self):
        # Stop the input polling thread
        self._inputs.stop()

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

