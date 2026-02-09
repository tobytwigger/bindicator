from threading import Thread
from RPLCD.gpio import CharLCD
import RPi.GPIO as GPIO
import time
from hardware.utils.logging_config import setup_logger

logger = setup_logger('LCD DRIVER')

class Lcd:
    LCD_E_PIN = 3
    LCD_RS_PIN = 2
    LCD_D4_PIN = 4
    LCD_D5_PIN = 17
    LCD_D6_PIN = 27
    LCD_D7_PIN = 22
    LCD_BACKLIGHT_TOGGLE_PIN = 10

    LCD_WIDTH = 16

    TEXT_STYLE_LEFT = 'left'
    TEXT_STYLE_CENTER = 'center'
    TEXT_STYLE_RIGHT = 'right'

    def __init__(self):
        logger.info("Initializing LCD driver")
        logger.debug("Initializing LCD GPIO pins")
        self._lcd_init_pins()
        logger.debug(f"Creating CharLCD instance with pins: RS={Lcd.LCD_RS_PIN}, E={Lcd.LCD_E_PIN}, DATA=[{Lcd.LCD_D4_PIN}, {Lcd.LCD_D5_PIN}, {Lcd.LCD_D6_PIN}, {Lcd.LCD_D7_PIN}]")
        self._lcd = CharLCD(pin_rs=Lcd.LCD_RS_PIN, pin_e=Lcd.LCD_E_PIN, pins_data=[Lcd.LCD_D4_PIN, Lcd.LCD_D5_PIN, Lcd.LCD_D6_PIN, Lcd.LCD_D7_PIN],
                            cols=16, rows=2, numbering_mode=GPIO.BCM)
        self._lcd.cursor_mode = 'hide'
        logger.debug("Clearing LCD display")
        self._lcd.clear()
        self._lcd.cursor_pos = (0, 0)
        self._current_line_1 = None
        self._current_line_2 = None
        self._sleeping = False
        self._scrolling_thread = None
        self._quit_scrolling_thread = False
        # State saved before sleeping
        self._saved_state = None
        logger.info("LCD driver initialized successfully")

    def _lcd_init_pins(self):
        logger.debug("Setting up LCD GPIO pins")
        GPIO.setup(self.LCD_E_PIN, GPIO.OUT)
        GPIO.setup(self.LCD_RS_PIN, GPIO.OUT)
        GPIO.setup(self.LCD_D4_PIN, GPIO.OUT)
        GPIO.setup(self.LCD_D5_PIN, GPIO.OUT)
        GPIO.setup(self.LCD_D6_PIN, GPIO.OUT)
        GPIO.setup(self.LCD_D7_PIN, GPIO.OUT)
        GPIO.setup(self.LCD_BACKLIGHT_TOGGLE_PIN, GPIO.OUT)  # Backlight enable
        GPIO.output(self.LCD_BACKLIGHT_TOGGLE_PIN, GPIO.HIGH)
        logger.debug("LCD GPIO pins configured, backlight enabled")

    def display(self, line1, line2, style, prefix=None, suffix=None):
        # Save the original (unpadded) state for wake restoration
        self._saved_state = {
            'line1': line1,
            'line2': line2,
            'style': style,
            'prefix': prefix,
            'suffix': suffix
        }

        if self._sleeping:
            logger.debug("Display called while sleeping, ignoring")
            return

        logger.debug(f"Displaying: '{line1}' / '{line2}' (style={style}, prefix={prefix}, suffix={suffix})")

        # Add padding
        if style == self.TEXT_STYLE_LEFT:
            line1 = line1.ljust(self.LCD_WIDTH, ' ')
            line2 = line2.ljust(self.LCD_WIDTH, ' ')
        elif style == self.TEXT_STYLE_CENTER:
            line1 = line1.center(self.LCD_WIDTH, ' ')
            line2 = line2.center(self.LCD_WIDTH, ' ')
        elif style == self.TEXT_STYLE_RIGHT:
            line1 = line1.rjust(self.LCD_WIDTH, ' ')
            line2 = line2.rjust(self.LCD_WIDTH, ' ')

        if self._current_line_1 == line1 and self._current_line_2 == line2:
            return

        if self._scrolling_thread is not None:
            self._quit_scrolling_thread = True
            self._scrolling_thread.join()

        self._current_line_1 = line1
        self._current_line_2 = line2
        self._lcd.clear()
        self._lcd.cursor_mode = 'hide'

        if len(line1) > self.LCD_WIDTH or len(line2) > self.LCD_WIDTH:
            self._scrolling_thread = Thread(target=self._display_scrolling, args=(line1, line2, prefix, suffix))
            self._scrolling_thread.start()
        else:
            if prefix:
                line1 = prefix + line1[len(prefix):]
            if suffix:
                line1 = line1[:self.LCD_WIDTH - len(suffix)] + suffix

            self._lcd.write_string(line1)
            self._lcd.cursor_pos = (1, 0)
            self._lcd.write_string(line2)

    def _display_scrolling(self, line1, line2, prefix, suffix):
        if len(line1) > self.LCD_WIDTH:
            line1 = line1 + '          '
        if len(line2) > self.LCD_WIDTH:
            line2 = line2 + '          '
        line1, line2 = self._scroll_text(line1, line2, prefix, suffix)
        self._quit_scrolling_thread = False

        while True:
            # Loop 10 times
            for _ in range(10):
                if self._quit_scrolling_thread:
                    self._quit_scrolling_thread = False
                    return
                time.sleep(0.05)
            line1, line2 = self._scroll_text(line1, line2, prefix, suffix)

    def _scroll_text(self, line1, line2, prefix, suffix):
        """
        If line1 or line2 is longer than the LCD_WIDTH, scroll the text by one character
        :param line1:
        :param line2:
        :return: (line1, line2)
        """
        self._lcd.clear()
        self._lcd.cursor_mode = 'hide'
        real_line_1 = line1[:self.LCD_WIDTH]
        real_line_2 = line2[:self.LCD_WIDTH]

        if prefix is not None:
            real_line_1 = prefix + real_line_1[len(prefix):]
        if suffix is not None:
            real_line_1 = real_line_1[:self.LCD_WIDTH - len(suffix)] + suffix

        self._lcd.write_string(real_line_1)
        self._lcd.cursor_pos = (1, 0)
        self._lcd.write_string(real_line_2)

        if len(line1) > self.LCD_WIDTH:
            line1 = line1[1:] + line1[0]
        if len(line2) > self.LCD_WIDTH:
            line2 = line2[1:] + line2[0]

        return line1, line2

    def sleep(self):
        if self._sleeping:
            logger.debug("Sleep called but already sleeping")
            return
        logger.info("Putting LCD to sleep")
        self._lcd.clear()
        self._lcd.cursor_mode = 'hide'
        self._current_line_1 = None
        self._current_line_2 = None

        if self._scrolling_thread is not None:
            logger.debug("Stopping scrolling thread")
            self._quit_scrolling_thread = True
            self._scrolling_thread.join()

        logger.debug("Turning off backlight")
        GPIO.output(self.LCD_BACKLIGHT_TOGGLE_PIN, GPIO.LOW)
        self._sleeping = True
        logger.info("LCD is now sleeping")

    def wake(self):
        if(not self._sleeping):
            logger.debug("Wake called but already awake")
            return
        logger.info("Waking LCD from sleep")
        self._sleeping = False
        logger.debug("Turning on backlight")
        GPIO.output(self.LCD_BACKLIGHT_TOGGLE_PIN, GPIO.HIGH)
        self._lcd.cursor_mode = 'hide'

        # Restore the saved state if it exists
        if self._saved_state is not None:
            logger.debug("Restoring saved display state")
            # Clear the current state so display() will actually update
            self._current_line_1 = None
            self._current_line_2 = None
            # Redisplay the saved content
            self.display(
                self._saved_state['line1'],
                self._saved_state['line2'],
                self._saved_state['style'],
                self._saved_state['prefix'],
                self._saved_state['suffix']
            )
        logger.info("LCD is now awake")

    def cleanup(self):
        logger.info("Cleaning up LCD")
        if self._scrolling_thread is not None:
            logger.debug("Stopping scrolling thread")
            self._quit_scrolling_thread = True
            self._scrolling_thread.join()
        logger.debug("Clearing display")
        self._lcd.clear()
        self._lcd.cursor_mode = 'hide'
        logger.info("LCD cleanup complete")
