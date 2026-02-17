# This file is required so we can run all benchmarks using:
# python -m pytest benchmarks
# It overwrites the basic behavior requiring all files to start with 'test_'.

import pytest


def pytest_configure(config: pytest.Config):
    config.addinivalue_line("python_files", "*.py")
    config.addinivalue_line("python_functions", "test_*")
