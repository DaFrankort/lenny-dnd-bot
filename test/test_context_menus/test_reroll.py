import pytest
from test_context_menus.context_menu import TestAbstractContextMenu
from utils.mocking import (
    MockInteraction,
    MockServerTextChannel,
    MockServerTextMessage,
    MockTextMessageEmbed,
    MockUser,
)

from commands.command import BaseContextMenu
from context_menus.reroll import RerollContextMenu


class TestRerollContextMenu(TestAbstractContextMenu):
    context_menu_name = RerollContextMenu.name

    def create_roll_embed(self, title: str):
        # Note, the roll embeds specifically use message.author.name as the title, thus the author
        # needs to be set explicitly.
        return MockTextMessageEmbed(title=title, author=title, contents="Result: 20")

    @pytest.mark.parametrize(
        "is_valid, title",
        [
            (True, "Rolling 1d20!"),
            (True, "Rolling 1d20 + 3 with advantage!"),
            (True, "Rolling 4 with disadvantage!"),
            (True, "Re-rolling 4d4 with elven accuracy!"),
            (False, "abcdef"),
            (False, "Fireball (XPHB)"),
            (False, "roll 1d8"),
        ],
    )
    async def test_reroll_embeds(
        self,
        cmd: BaseContextMenu,
        user: MockUser,
        channel: MockServerTextChannel,
        is_valid: bool,
        title: str,
    ):
        """Attempt to re-roll on various titles."""

        itr = MockInteraction(user)
        message = MockServerTextMessage(user, channel)

        message.embeds = [self.create_roll_embed(title)]

        if is_valid:
            await cmd.handle(itr, message)
        else:
            with pytest.raises(ValueError):
                await cmd.handle(itr, message)

    async def test_invalid_embed_reroll(self, cmd: BaseContextMenu, user: MockUser, channel: MockServerTextChannel):
        """Try to roll on message with no embeds."""
        itr = MockInteraction(user)
        message = MockServerTextMessage(user, channel)
        message.embeds = []

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)

    async def test_invalid_user_reroll(self, cmd: BaseContextMenu, user: MockUser, channel: MockServerTextChannel):
        """Try to roll on an embed from a different user."""

        itr = MockInteraction(user)
        other = MockUser("other")
        message = MockServerTextMessage(other, channel)

        with pytest.raises(PermissionError):
            await cmd.handle(itr, message)
