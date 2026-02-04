import discord
import pytest
from utils.mocking import MockInteraction

from embeds.search import MultiDNDSelectView
from logic.config import Config
from logic.dnd.data import Data


class TestDNDEmbed:
    @pytest.fixture()
    def itr(self):
        return MockInteraction()

    async def test_multidndselect(self, itr: discord.Interaction):
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
