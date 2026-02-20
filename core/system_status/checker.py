from abc import abstractmethod, ABC
from dataclasses import dataclass

@dataclass
class SystemStatusCheckResult:
    wifi_connection_passed: bool
    user_has_bins_passed: bool


class SystemCheckerInterface(ABC):
    @abstractmethod
    def check(self) -> bool:
        pass

class SystemStatusChecker:
    @classmethod
    def run(cls) -> SystemStatusCheckResult:
        from core.system_status.no_bins import UserHasBinsChecker
        from core.system_status.wifi_checker import WifiChecker

        wifi_connection_passed = WifiChecker().check()
        user_has_bins_passed = UserHasBinsChecker().check()

        return SystemStatusCheckResult(
            wifi_connection_passed = wifi_connection_passed,
            user_has_bins_passed = user_has_bins_passed
        )