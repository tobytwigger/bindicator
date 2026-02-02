from screens.abstract_screen import Screen
from schedule import Scheduler, CancelJob
from database.db import Home
from screens.loading_bin_day import LoadingBinDay
from drivers.drivers import Drivers


class CheckConfiguration(Screen):

    def __init__(self):
        self._configuration_result = None
        self._checker = ConfigurationChecker()

    def schedule(self, schedule: Scheduler):
        schedule.every(10).seconds.do(self._check_configuration)

    def _check_configuration(self):
        self._configuration_result = self._checker.validate()

    def show_initial_state(self, drivers):
        drivers.lcd.display('Checking', 'Settings', drivers.lcd.TEXT_STYLE_CENTER)

    def tick(self, drivers: Drivers):
        if self._configuration_result is not None:
            if self._configuration_result.is_missing_active_home:
                drivers.lcd.display('No active home', 'configured', drivers.lcd.TEXT_STYLE_CENTER)
            elif self._configuration_result.no_bins_set_up:
                drivers.lcd.display('No bins set up', '', drivers.lcd.TEXT_STYLE_CENTER)
            # elif self._configuration_result.not_connected_to_internet:
            #     drivers.lcd.display('No internet', 'Please press the WPS button on your router', drivers.lcd.TEXT_STYLE_CENTER)

        pass

    def redirect(self):
        if self._configuration_result is not None:
            print(self._configuration_result.is_valid())
        if self._configuration_result is not None and self._configuration_result.is_valid():
            return LoadingBinDay()

        return None

class ConfigurationChecker:
    def validate(self):
        return ConfigurationCheckerResult(
            self._missing_active_home(),
            self._no_bins_set_up(),
            self._not_connected_to_internet(),
        )

    def _missing_active_home(self):
        return Home.get_active() is None

    def _no_bins_set_up(self):
        return Home.get_active().bins.count() == 0

    def _not_connected_to_internet(self):
        return False


class ConfigurationCheckerResult:
    def __init__(self, _is_missing_active_home, _no_bins_set_up, _not_connected_to_internet):
        self.is_missing_active_home = _is_missing_active_home
        self.no_bins_set_up = _no_bins_set_up
        self.not_connected_to_internet = _not_connected_to_internet

    def is_valid(self):
        if self.is_missing_active_home:
            return False

        if self.no_bins_set_up:
            return False

        if self.not_connected_to_internet:
            return False

        return True
