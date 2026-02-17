import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from logic.roll import Advantage, roll


@pytest.mark.parametrize(
    ("expression"),
    [
        ("1d20"),
        ("1d8+2+2d6"),
        ("1d8e8"),
        ("1d20mi10+5"),
        ("4d6kh3"),
    ],
)
@pytest.mark.parametrize(
    "advantage",
    [
        Advantage.NORMAL,
        Advantage.ADVANTAGE,
        Advantage.DISADVANTAGE,
    ],
)
def test_roll(benchmark: BenchmarkFixture, expression: str, advantage: Advantage):
    benchmark(roll, expression, advantage)
