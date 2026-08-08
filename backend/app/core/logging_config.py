"""Console logging setup — loads config/logging.yaml."""

import logging
import logging.config
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "logging.yaml"


def setup_logging() -> None:
    """Load YAML logging config for console output."""
    with open(_CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)
    logging.getLogger("app").info("Logging initialised (console stream)")


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the 'app' hierarchy."""
    return logging.getLogger(name)
