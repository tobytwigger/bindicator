from logging import Logger
import threading
from core.scheduler.scheduler import BinCollectionExplorer
from hardware.drivers.drivers import Drivers
from schedule import Scheduler

class BinCollectionDataCaching:
    def __init__(self):
        self.data = BinCollectionExplorer()
        self._mqtt_subscribed = False  # Track subscription state
        self._cache_lock = threading.Lock()  # Thread-safe access to cache
        self.data.load_data()  # Initial load of data
        self.recently_updated = True

    def subscribe(self, logger: Logger, schedule: Scheduler, drivers: Drivers):
        # Subscribe to database update notifications via MQTT
        if drivers.mqtt and not self._mqtt_subscribed:
            try:
                drivers.mqtt.subscribe("bindicator/database/updated",
                                       lambda payload: self._on_database_updated(logger, payload, drivers))
                self._mqtt_subscribed = True
                logger.info("Subscribed to database updates via MQTT")
            except Exception as e:
                logger.warning(f"Failed to subscribe to MQTT: {e}")

        schedule.every(15).minutes.do(
            lambda: (
                self._cache_lock.acquire(),
                self.data.load_data(),
                setattr(self, "recently_updated", True),
                self._cache_lock.release()
            )
        )

    def unsubscribe(self, logger: Logger, drivers: Drivers):
        if drivers.mqtt and self._mqtt_subscribed:
            try:
                drivers.mqtt.unsubscribe("bindicator/database/updated")
                self._mqtt_subscribed = False
                logger.info("Unsubscribed from database updates")
            except Exception as e:
                logger.warning(f"Failed to unsubscribe from MQTT: {e}")


    def _on_database_updated(self, logger: Logger, payload, drivers: Drivers):
        """Thread-safe callback when database is updated via MQTT."""
        logger.info("Database update notification received")
        with self._cache_lock:
            try:
                self.data.load_data()
                self.recently_updated = True
                logger.debug("Cache refreshed after database update")
            except Exception as e:
                logger.error(f"Error refreshing cache: {e}", exc_info=True)

    def mark_update_handled(self):
        with self._cache_lock:
            self.recently_updated = False