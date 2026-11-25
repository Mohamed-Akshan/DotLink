import logging


def setup_logging() -> logging.Logger:
    """Configure readable application logs without request payloads."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    return logging.getLogger("dotlink")
