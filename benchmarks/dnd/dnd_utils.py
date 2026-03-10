import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from logic.dnd.abstract import DNDEntry, DNDEntryList
from logic.dnd.data import Data
from logic.dnd.source import ContentChoice, SourceList

ENTRY_LIST_PARAMS = [
    ("actions", Data.actions),
    ("backgrounds", Data.backgrounds),
    ("boons", Data.boons),
    ("classes", Data.classes),
    ("conditions", Data.conditions),
    ("creatures", Data.creatures),
    ("cults", Data.cults),
    ("deities", Data.deities),
    ("feats", Data.feats),
    ("hazards", Data.hazards),
    ("items", Data.items),
    ("objects", Data.objects),
    ("rules", Data.rules),
    ("skills", Data.skills),
    ("species", Data.species),
    ("spells", Data.spells),
    ("tables", Data.tables),
    ("vehicles", Data.vehicles),
]


def parametrize_entry_lists():
    """Adds a pytest parametrization for ``entry_list`` with type ``DNDEntryList`` of all possible lists."""
    return pytest.mark.parametrize(
        "entry_list",
        [v for _, v in ENTRY_LIST_PARAMS],
        ids=[k for k, _ in ENTRY_LIST_PARAMS],
    )


@parametrize_entry_lists()
def benchmark_entry_list(benchmark: BenchmarkFixture, entry_list: DNDEntryList[DNDEntry], method: str) -> None:
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
        target=getattr(entry_list, method),
        setup=setup,
        rounds=max(len(names), 256),
    )
