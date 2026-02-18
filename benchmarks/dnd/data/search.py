from pytest_benchmark.fixture import BenchmarkFixture

from lenny.logic.dnd.data import Data
from logic.dnd.source import ContentChoice, SourceList


def test_dnd_data_search(benchmark: BenchmarkFixture) -> None:
    names: list[str] = [e.name for entry_list in Data for e in entry_list.entries]
    sources: set[str] = set({e.name for e in SourceList(content=ContentChoice.ALL).entries})
    index = 0

    def setup() -> tuple[tuple[str], dict[str, set[str]]]:
        # In this benchmark we want to use every possible DND entry that can be looked up,
        # To achieve this a setup() is required so a different name is selected each round.
        nonlocal index
        name = names[index]
        index = (index + 1) % len(names)
        return (
            (name,),
            {"allowed_sources": sources},
        )

    benchmark.pedantic(  # type: ignore
        target=Data.search,
        setup=setup,
        rounds=len(names),
    )
