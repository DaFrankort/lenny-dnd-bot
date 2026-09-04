import discord
import pytest
from assertion import assert_embed_can_be_rendered, assert_layout_view_can_be_rendered
from mocking import MockInteraction

from embeds.search import MultiDNDSelectView, get_dnd_embed
from logic.config import Config
from logic.dnd.abstract import DNDEntry
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

    @pytest.mark.strict
    @pytest.mark.parametrize("entry", [entry for entries in Data for entry in entries.entries])
    async def test_all_embeds(self, itr: discord.Interaction, entry: DNDEntry):
        context = f"{entry.entry_type.value} {entry.title}"
        try:
            embed = get_dnd_embed(itr, entry)
        except Exception as e:
            pytest.fail(f"{context} could not initialize embed: {e}")

        if isinstance(embed, discord.Embed):
            assert_embed_can_be_rendered(embed, context=context)
        else:
            assert_layout_view_can_be_rendered(embed, context=context)
