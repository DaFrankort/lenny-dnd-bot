from unittest.mock import MagicMock
import discord
import pytest
import pytest_asyncio
from embeds.search import MultiDNDSelectView
from logic.config import Config
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

    @pytest_asyncio.fixture(autouse=True)
    def setup(self):
        self.server = MagicMock(spec=discord.Guild)
        self.server.id = 1234
        self.config = Config(server=self.server)

    def test_dnddatalist_search(self):
        sources = Config.allowed_sources(server=self.server)
        for query in self.queries:
            for data in Data:
                try:
                    data.search(query, allowed_sources=sources)
                except Exception:
                    assert False, f"{data.entries[0].object_type} DNDDataList failed search()"

    def test_search_from_query(self):
        sources = Config.allowed_sources(server=self.server)
        for query in self.queries:
            try:
                Data.search(query, allowed_sources=sources)
            except Exception:
                assert False, "search_from_query threw an error."

    @pytest.mark.asyncio
    async def test_multidndselect(self):
        sources = Config.allowed_sources(server=self.server)
        name = "pot of awakening"
        entries = Data.items.get(name, sources)
        assert len(entries) >= 2, "Test requires at least 2 items, please update test data."
        try:
            MultiDNDSelectView(name, entries)
        except Exception as e:
            pytest.fail(f"MultiDNDSelectView failed to initialize: {e}")
