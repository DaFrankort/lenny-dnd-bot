import pytest
from utils.mocking import MockInteraction

from embeds.search import MultiDNDSelectView
from logic.config import Config
from logic.dnd.abstract import fuzzy_matches
from logic.dnd.data import Data


class TestDndData:
    queries: list[str] = [
        "fireball",
        "dagger",
        "poisoned",
        "goblin",
        "initiative",
        "attack",
        "tough",
        "ABCDF",
    ]

    def test_dnddatalist_search(self):
        itr = MockInteraction()
        config = Config.get(itr)
        sources = config.allowed_sources
        for query in self.queries:
            for data in Data:
                try:
                    data.search(query, allowed_sources=sources)
                except Exception:
                    assert False, f"{data.entries[0].entry_type} DNDDataList failed search()"

    def test_search_from_query(self):
        itr = MockInteraction()
        config = Config.get(itr)
        sources = config.allowed_sources
        for query in self.queries:
            try:
                Data.search(query, allowed_sources=sources)
            except Exception:
                assert False, "search_from_query threw an error."

    @pytest.mark.asyncio
    async def test_multidndselect(self):
        itr = MockInteraction()
        config = Config.get(itr)
        sources = config.allowed_sources
        name = "pot of awakening"
        entries = Data.items.get(name, sources)
        assert len(entries) >= 2, "Test requires at least 2 items, please update test data."
        try:
            MultiDNDSelectView(name, entries)
        except Exception as e:
            pytest.fail(f"MultiDNDSelectView failed to initialize: {e}")

    @pytest.mark.parametrize(
        "query, value, result",
        [
            ("fire bolt", "fireball", True),
            ("fire bolt", "ray of sickness", False),
            ("ray", "aura", True),
        ],
    )
    def test_fuzzy(self, query: str, value: str, result: bool):
        fuzzy = fuzzy_matches(query, value, fuzzy_threshold=75)
        assert (fuzzy is not None) == result
