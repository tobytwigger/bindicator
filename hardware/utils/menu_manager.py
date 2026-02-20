from typing import Callable, List

from hardware.drivers.inputs import InputEvent
from hardware.screens.abstract_screen import Screen, QuitApp
from hardware.utils.logging_config import setup_logger

logger = setup_logger('MENU MANAGER')

class MenuItem:
    def __init__(self,
                 name: str,
                 on_ok: Callable[[],  Screen | QuitApp] | None = None,
                 text: Callable[[], str] | None = None
                 ):
        self.name = name
        self.on_ok = on_ok
        self._text = text

    @property
    def text(self) -> str:
        if self._text is not None:
            return self._text()
        else:
            return ""


class MenuManager:
    def __init__(self, menu_items: List[MenuItem], on_back: Callable[[], Screen] | None = None):
        self.menu_items = menu_items
        self._selected_option: int = 0
        self.on_back = on_back
        if self.on_back is not None:
            # Add 'Back' to the end
            self.menu_items.append(MenuItem(name="Back", on_ok=self.on_back))

    @property
    def selected_menu_item(self) -> MenuItem:
        return self.menu_items[self._selected_option]

    def handle_inputs(self, events) -> tuple[bool, Screen | None]:
        # Navigation
        if InputEvent.LEFT_BUTTON_PRESSED in events:
            if self._selected_option > 0:
                self._selected_option -= 1
            else:
                self._selected_option = len(self.menu_items) - 1

            logger.debug(f"Left button pressed, selected option: {self.menu_items[self._selected_option]}")
            return True, None

        if InputEvent.RIGHT_BUTTON_PRESSED in events:
            if self._selected_option < len(self.menu_items) - 1:
                self._selected_option += 1
            else:
                self._selected_option = 0

            logger.debug(f"Right button pressed, selected option: {self.menu_items[self._selected_option]}")
            return True, None

        # if InputEvent.LEFT_BUTTON_PRESSED in events and InputEvent.RIGHT_BUTTON_PRESSED in events:
        #     logger.info(f"Both buttons pressed, going back")
        #     return self._activate_option()

        if self.selected_menu_item.on_ok is not None:
            # Activate the 'OK' option of pressing a bin
            if events.contains_bin_press():
                logger.info(f"A bin button has been pressed, activating option: {self.menu_items[self._selected_option]}")
                return True, self.selected_menu_item.on_ok()


        return False, None



