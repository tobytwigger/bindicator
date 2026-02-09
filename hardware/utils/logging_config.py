"""
Centralized logging configuration for the hardware application.

All logs are formatted as: [COMPONENT] {datetime}: LOG MESSAGE
"""
import logging
import sys
from datetime import datetime


class ComponentFormatter(logging.Formatter):
    """Custom formatter that includes component name and timestamp."""

    def __init__(self, component_name: str):
        self.component_name = component_name
        super().__init__()

    def format(self, record):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        message = record.getMessage()
        return f"[{self.component_name}] {timestamp}: {message}"


def setup_logger(component_name: str, level=logging.DEBUG) -> logging.Logger:
    """
    Set up a logger for a specific component.

    Args:
        component_name: Name of the component (e.g., 'MQTT', 'LCD DRIVER', 'APP RUNNER')
        level: Logging level (default: DEBUG)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(component_name)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = ComponentFormatter(component_name)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

    return logger
