import pytest
import logging


@pytest.fixture(autouse=True)
def disable_logging():
    """Disable logging in all tests."""
    logging.disable(logging.CRITICAL)
