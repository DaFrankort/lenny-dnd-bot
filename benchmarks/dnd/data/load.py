from pytest_benchmark.fixture import BenchmarkFixture

from lenny.logic.dnd.data import DNDData


def test_load_data(benchmark: BenchmarkFixture) -> None:
    benchmark(DNDData)
