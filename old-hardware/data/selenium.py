import uk_bin_collection.uk_bin_collection.common
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.constants import (
    DEFAULT_PROJECT_ROOT_CACHE_PATH,
    DEFAULT_USER_HOME_CACHE_PATH, ROOT_FOLDER_NAME,
)
import os
import datetime
import json
from selenium import webdriver
from uk_bin_collection.uk_bin_collection.common import *

from webdriver_manager.core.driver_cache import DriverCacheManager


def create_webdriver(
        web_driver: str = None,
        headless: bool = True,
        user_agent: str = None,
        session_name: str = None,
) -> webdriver.Chrome:
    """
    Create and return a Chrome WebDriver configured for optional headless operation.

    :param web_driver: URL to the Selenium server for remote web drivers. If None, a local driver is created.
    :param headless: Whether to run the browser in headless mode.
    :param user_agent: Optional custom user agent string.
    :param session_name: Optional custom session name string.
    :return: An instance of a Chrome WebDriver.
    :raises WebDriverException: If the WebDriver cannot be created.
    """

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    if user_agent:
        options.add_argument(f"--user-agent={user_agent}")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    if session_name and web_driver:
        options.set_capability("se:name", session_name)

    try:
        if web_driver:
            return webdriver.Remote(command_executor=web_driver, options=options)
        else:
            return webdriver.Chrome(
                service=ChromeService('/usr/bin/chromedriver'), options=options
            )
    except MaxRetryError as e:
        print(f"Failed to create WebDriver: {e}")
        raise

class SeleniumDriverManager:

    def setup_cache(self):
        """
        In order to run selenium on a raspberry pi, we need to use /usr/bin/chromedriver rather than any google downloaded driver.
        This is because the google drivers are not compiled for ARM processors.

        The problem is that the uk_bin_collection package does not support overriding the driver path. Instead, it uses Chrome().install() to either
        install or get the path of the installed driver.

        We can use monkey patching to override the create_webdriver function and return our own implementation. This is identical, except it overrides the
        Chrome().install() function.

        Longer term we may consider using docker to run a selenium server, especially if monkey patching leads to long delays as selenium boots (not sure if that's a thing or not)
        :return:
        """

        uk_bin_collection.uk_bin_collection.common.create_webdriver = create_webdriver

        # driver = ChromeDriverManager()
        # key = driver._cache_manager._DriverCacheManager__get_metadata_key(driver.driver)
        #
        # data = {
        #     key: {
        #         "timestamp": datetime.date.today().strftime('%d/%m/%Y'),
        #         "binary_path": '/usr/bin/chromedriver',
        #     }
        # }
        #
        # with open(self._drivers_json_path, "w") as outfile:
        #     json.dump(data, outfile, indent=4)
        #
        # Print out the contents of self._drivers_json_path
        # with open(self._drivers_json_path, "r") as infile:
        #     print(infile.read())
        #
        # print('Cache has been set up and printed above')

