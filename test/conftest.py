import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item
from typing import List


def pytest_addoption(parser: Parser) -> None:
    """Add the --run-strict option to enable running heavier, stricter tests."""
    parser.addoption(
        "--run-strict",
        action="store_true",
        default=False,
        help="Run strict tests (heavier and slower).",
    )


def pytest_configure(config: Config) -> None:
    """Register the 'strict' marker for stricter or heavier tests."""
    config.addinivalue_line(
        "markers",
        "strict: Run stricter, heavier but also slower tests. (--run-strict)",
    )


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    """Skip tests marked as 'strict' unless --run-strict is passed."""
    if config.getoption("--run-strict"):
        # User explicitly asked to run strict tests — keep all.
        return

    skip_strict = pytest.mark.skip(reason="use --run-strict to run this test")
    for item in items:
        if "strict" in item.keywords:
            item.add_marker(skip_strict)
