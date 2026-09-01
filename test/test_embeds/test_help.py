import pytest
from assertion import assert_embed_can_be_rendered
from mocking import MockBot

from bot import Bot
from embeds.help import HelpEmbed
from logic.help import HelpTabs


class TestHelp:
    @pytest.mark.parametrize("tab", HelpTabs.keys)
    def test_tab_rendering(self, tab: str):
        bot: Bot = MockBot()
        embed = HelpEmbed(bot.tree, tab=tab)
        assert_embed_can_be_rendered(embed, tab)
