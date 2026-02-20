from core.database.database import SessionLocal
from core.database.repositories import BinRepository
from core.system_status.checker import SystemCheckerInterface
import requests

from hardware.utils.logging_config import setup_logger

logging = setup_logger('WIFI CHECKER')

class UserHasBinsChecker(SystemCheckerInterface):
    def check(self) -> bool:
        return self._has_bins_set_up()

    @classmethod
    def _has_bins_set_up(cls) -> bool:
        with SessionLocal() as db:
            bin_repo = BinRepository(db)
            return bin_repo.count() > 0

