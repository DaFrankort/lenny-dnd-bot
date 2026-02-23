from benchmarks.dnd.dnd_utils import benchmark_entry_list, parametrize_entry_lists
from pytest_benchmark.fixture import BenchmarkFixture

from logic.dnd.abstract import DNDEntry, DNDEntryList


@parametrize_entry_lists()
def test_dnd_entry_list_get(benchmark: BenchmarkFixture, entry_list: DNDEntryList[DNDEntry]) -> None:
    benchmark_entry_list(benchmark, entry_list, "get")
