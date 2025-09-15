from unittest.mock import MagicMock
import discord
import pytest_asyncio
from logic.config import Config
from dnd import Data


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
                    assert (
                        False
                    ), f"{data.entries[0].object_type} DNDDataList failed search()"

    def test_search_from_query(self):
        sources = Config.allowed_sources(server=self.server)
        for query in self.queries:
            try:
                Data.search(query, allowed_sources=sources)
            except Exception:
                assert False, "search_from_query threw an error."
