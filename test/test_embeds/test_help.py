from test.assertion import assert_embed_can_be_rendered
from test.mocking import MockBot

import pytest

from embeds.help import HelpEmbed
from logic.help import HelpTabs


class TestHelp:
    @pytest.mark.parametrize("tab", HelpTabs.keys)
    def test_tab_rendering(self, tab: str):
        bot = MockBot()
        embed = HelpEmbed(bot.tree, tab=tab)
        assert_embed_can_be_rendered(embed, tab)
