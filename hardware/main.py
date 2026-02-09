#!/home/toby/bindicator/.venv/bin/python
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
root_dir = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=root_dir / ".env")

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
import time
import schedule
import threading
from hardware.drivers.drivers import Drivers
from hardware.drivers.inputs import Inputs, InputEvents
from hardware.screens.abstract_screen import Screen, QuitApp
from hardware.utils.logging_config import setup_logger

# Configure logger with APP RUNNER component
logger = setup_logger('APP RUNNER')


should_kill = False

def sigterm_handler(signal, frame):
    global should_kill
    should_kill = True

def log_error(e):
    print(e)

def run():
    logger.info("========== STARTING BINDICATOR HARDWARE APPLICATION ==========")
    logger.info("Registering SIGTERM signal handler")
    signal.signal(signal.SIGTERM, sigterm_handler)

    logger.info("Setting up GPIO pins")
    set_up_gpio()

    # Create MQTT client for publishing GPIO events
    logger.info("Initializing MQTT client")
    mqtt_client = MqttClient()

    logger.info("Initializing hardware drivers")
    drivers = Drivers(
        Lcd(),
        Lights(),
        Movement(),
        Buttons(),
        mqtt_client,
    )
    logger.info("Hardware drivers initialized successfully")

    logger.info("Initializing input handler")
    inputs = Inputs(
        drivers,
        mqtt_client=mqtt_client,
    )
    logger.info("Input handler initialized successfully")

    logger.info("Setting initial screen to WelcomeScreen")
    screen = WelcomeScreen()

    logger.info("Creating AppRunner instance")
    runner = AppRunner(drivers, inputs)
    runner.set_quitting_screen(GoodbyeScreen())

    try:
        logger.info("Starting main application loop")
        runner.run(screen)
    except Exception as e:
        logger.error(f"Fatal exception occurred in main loop: {e}", exc_info=True)
        runner.set_quitting_screen(ErrorScreen())
        runner.handle_exception(e)

def set_up_gpio():
    logger.info("Configuring GPIO mode to BCM")
    GPIO.setmode(GPIO.BCM)
    logger.info("Disabling GPIO warnings")
    GPIO.setwarnings(False)
    logger.info("GPIO setup complete")

class AppRunner:
    def __init__(self, drivers: Drivers, inputs: Inputs):
        logger.info("Initializing AppRunner")
        self._quitting_screen = None
        self._drivers = drivers
        self._stop_schedule = None
        self._schedule = None
        self._redirect_to_config = False
        self._inputs = inputs
        logger.info("AppRunner initialized")

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
        logger.debug("Starting background scheduler thread")
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                logger.debug("Schedule thread started")
                while not cease_continuous_run.is_set():
                    self._schedule.run_pending()
                    time.sleep(1)
                logger.debug("Schedule thread stopped")

        continuous_thread = ScheduleThread()
        continuous_thread.start()
        logger.debug("Background scheduler thread running")
        return cease_continuous_run

    def run(self, screen: Screen | None):
        logger.info("AppRunner.run() started")
        # Create a scheduler
        logger.info("Creating scheduler")
        self._schedule = schedule.Scheduler()

        # Add a regular job to check configuration
        logger.info("Scheduling configuration checks every 1 minute")
        self._schedule.every(1).minute.do(self._check_configuration)
        self._schedule.every(1).minute.do(self._check_settings)

        # Start the input polling thread
        logger.info("Starting input polling thread")
        self._inputs.start()

        while screen is not None:
            screen_name = type(screen).__name__
            logger.info(f"Entering screen {screen_name}")

            # Fire the on_enter event, so screens can set up schedules and show initial states
            logger.debug(f"Calling on_enter for {screen_name}")
            screen.on_enter(self._schedule, self._drivers)

            # Start the scheduler running in the background
            logger.debug(f"Starting background scheduler for {screen_name}")
            self._stop_schedule = self._run_schedule_in_background()

            # Start the screen running properly
            try:
                tick_count = 0
                while True:
                    tick_count += 1
                    if tick_count % 100 == 0:  # Log every 100 ticks to avoid spam
                        logger.debug(f"{screen_name}: Tick #{tick_count}")

                    result = screen.tick(self._drivers)

                    # Check if the app should quit
                    if should_kill:
                        logger.info("SIGTERM received, quitting application")
                        screen.on_exit(self._drivers)
                        screen = None
                        break

                    if isinstance(result, QuitApp):
                        logger.info("QuitApp received from screen, quitting application")
                        screen.on_exit(self._drivers)
                        screen = None
                        break

                    # Check if a redirect is needed
                    if isinstance(result, Screen):
                        new_screen_name = type(result).__name__
                        logger.info(f"Screen transition: {screen_name} -> {new_screen_name}")
                        screen.on_exit(self._drivers)
                        self._cleanup()
                        screen = result
                        break  # Break inner loop to transition to next_screen

                    # Listen for any inputs
                    events = self._inputs.listen()

                    # Handle driver sleep/wake events
                    if InputEvents.MOVEMENT_STOPPED in events:
                        logger.debug("Movement stopped, putting drivers to sleep")
                        self._drivers.sleep()
                    elif InputEvents.MOVEMENT_DETECTED in events:
                        logger.debug("Movement detected, waking drivers")
                        self._drivers.wake()

                    # Pass the events to the screen
                    if len(events) > 0:
                        event_names = [e.name for e in events]
                        logger.debug(f"{screen_name}: Handling input events: {event_names}")
                        result = screen.handle_inputs(events, self._drivers)

                        # Check if the app should quit
                        if should_kill:
                            logger.info("SIGTERM received after input handling, quitting application")
                            screen.on_exit(self._drivers)
                            screen = None
                            break

                        if isinstance(result, QuitApp):
                            logger.info("QuitApp received from input handler, quitting application")
                            screen.on_exit(self._drivers)
                            screen = None
                            break

                        # Check if a redirect is needed
                        if isinstance(result, Screen):
                            new_screen_name = type(result).__name__
                            logger.info(f"Screen transition from input: {screen_name} -> {new_screen_name}")
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
                logger.info("KeyboardInterrupt received")
                if screen is not None:
                    screen.on_exit(self._drivers)

                # Do nothing
                screen = None

            # To get to this point, either `run` has been called with no screen, or the screen has asked for the app to quit
            self._cleanup()

        logger.info("AppRunner.run() exiting, calling _quit()")
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
        logger.debug("Cleaning up resources")
        if self._stop_schedule is not None:
            logger.debug("Stopping background scheduler")
            self._stop_schedule.set()
            logger.debug("Cleaning up drivers")
            self._drivers.cleanup()
        logger.debug("Cleanup complete")

    def _quit(self):
        logger.info("Quitting application")
        # Stop the input polling thread
        logger.debug("Stopping input polling thread")
        self._inputs.stop()

        if self._quitting_screen is not None:
            logger.info(f"Displaying quitting screen: {type(self._quitting_screen).__name__}")
            quitting_screen = self._quitting_screen
            self._quitting_screen = None
            return self.run(quitting_screen)

        logger.info("Cleaning up GPIO")
        GPIO.cleanup()
        logger.info("========== APPLICATION SHUTDOWN COMPLETE ==========")

    def handle_exception(self, e):
        logger.error(f"Handling fatal exception: {e}", exc_info=True)
        self._quit()

    def set_quitting_screen(self, quitting_screen: Screen):
        self._quitting_screen = quitting_screen



if __name__ == "__main__":
    run()

