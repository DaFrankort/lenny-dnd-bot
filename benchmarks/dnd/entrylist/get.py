from benchmarks.dnd.utils import parametrize_entry_lists
from pytest_benchmark.fixture import BenchmarkFixture

from logic.dnd.abstract import DNDEntry, DNDEntryList
from logic.dnd.source import ContentChoice, SourceList


@parametrize_entry_lists()
def test_dnd_entry_list_get(benchmark: BenchmarkFixture, entry_list: DNDEntryList[DNDEntry]) -> None:
    names: list[str] = [e.name for e in entry_list.entries]
    sources: set[str] = set({e.name for e in SourceList(content=ContentChoice.ALL).entries})
    index = 0

    def setup() -> tuple[tuple[str], dict[str, set[str]]]:
        nonlocal index
        name = names[index]
        index = (index + 1) % len(names)
        return (
            (name,),
            {"allowed_sources": sources},
        )

    benchmark.pedantic(  # type: ignore
        target=entry_list.get,
        setup=setup,
        rounds=max(len(names), 256),
    )
