from database.db import Home
from dataclasses import dataclass

@dataclass
class Config:
    timeout: int

    @staticmethod
    def default():
        return Config(
            timeout=60
        )


class ConfigRepository:
    def __init__(self):
        self.config = Config.default()
        self.load()

    def load(self):
        try:
            home = Home.get_active()
            default_config = Config.default()

            self.config = Config(
                timeout=home.timeout if home else default_config.timeout
            )
        except Exception as e:
            self.config = Config.default()

    def get(self):
        """

        :return: Config
        """
        return self.config or Config.default()