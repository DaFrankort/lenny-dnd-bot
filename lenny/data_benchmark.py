# DND DATA BENCHMARKS
# To test if adjustments to the way DNDEntries are handled cause performance improvements.

# BENCHMARKS PRE-CHANGE
# Windows 10 | Intel i7-7700HQ 2.8GHz | 16GB RAM
# - Average Time    0.00396 ms/search
# - Max Capacity    252.8 searches/ms

# Windows 10 | AMD Ryzen 7 5800x | 32GB RAM
# - Average Time    0.00181 ms/search
# - Max Capacity    552.7 searches/ms


import time

from logic.dnd.data import Data, DNDData
from logic.dnd.source import ContentChoice, SourceList


class BenchmarkTimer:
    def __init__(self):
        self.start = time.time()

    def log(self, message: str, do_print: bool = True) -> float:
        latency = time.time() - self.start
        if do_print:
            print(f"{message} \t\t| {latency}ms")
        self.start = time.time()
        return latency


def _run_benchmark_load_time():
    timer = BenchmarkTimer()
    DNDData()
    timer.log("Load Data")


def _run_benchmark_search_all():

    inputs: dict[str, float | None] = {}  # {"search_term": latency}
    for entry_lists in Data:
        for entry in entry_lists.entries:
            inputs[entry.name] = None

    source_set = set([e.name for e in SourceList(content=ContentChoice.ALL).entries])
    timer = BenchmarkTimer()
    for name in inputs.keys():
        Data.search(name, allowed_sources=source_set)
        inputs[name] = timer.log(f"Search All - {name}", False)

    total_entries = len(inputs.keys())
    total_time = sum(v for v in inputs.values() if v)
    average = total_time / total_entries
    print(f"### {total_entries} Searches")
    print(f"### Total time: {(total_time*1000):.1f}s")
    print(f"### Average time: {average:.5f} ms/search")
    print(f"### Max load: {(1/average):.1f} searches/ms")


def run_data_benchmarks():
    _run_benchmark_load_time()
    print()
    _run_benchmark_search_all()


run_data_benchmarks()
