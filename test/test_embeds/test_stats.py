import discord
import pytest
from utils.mocking import MockInteraction

from embeds.stats import StatsEmbed
from logic.stats import Stats


class TestStats:
    @pytest.fixture()
    def itr(self):
        return MockInteraction()

    @pytest.fixture()
    def stats(self):
        return Stats()

    def test_get_embed_title(self, itr: discord.Interaction, stats: Stats):
        embed = StatsEmbed(itr, stats)
        embed_title = embed.get_title()

        assert itr.user.display_name in embed_title, "Embed title should contain the user's display name"

    def test_get_embed_description(self, itr: discord.Interaction, stats: Stats):
        embed = StatsEmbed(itr, stats)
        description = embed.get_description()

        for rolls, result in stats.stats:
            for index, roll in enumerate(rolls):
                assert str(roll) in description, f"Description should contain the roll {roll} at index {index}"
            assert str(result) in description, f"Description should contain the result {result}"

        total = sum(result for _, result in stats.stats)
        assert str(total) in description, "Description should contain the total of all stats"
