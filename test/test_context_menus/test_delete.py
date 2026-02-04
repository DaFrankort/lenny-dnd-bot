import pytest
from test_context_menus.context_menu import TestAbstractContextMenu
from utils.mocking import (
    MockInteraction,
    MockServerTextChannel,
    MockServerTextMessage,
    MockUser,
)

from commands.command import BaseContextMenu
from context_menus.delete import DeleteContextMenu


class TestDeleteContextMenu(TestAbstractContextMenu):
    context_menu_name = DeleteContextMenu.name

    async def test_delete_bot_message(self, cmd: BaseContextMenu):
        """Verify that the bot is allowed to delete its own message."""

        user = MockUser("bot")
        itr = MockInteraction(user)
        channel = MockServerTextChannel()
        message = MockServerTextMessage(user, channel)

        await cmd.handle(itr, message)

    async def test_delete_other_message(self, cmd: BaseContextMenu):
        """Verify that the bot is not allowed to delete another user's error."""

        user = MockUser("bot")
        itr = MockInteraction(user)

        other = MockUser("other")
        channel = MockServerTextChannel()
        message = MockServerTextMessage(other, channel)

        with pytest.raises(PermissionError):
            await cmd.handle(itr, message)
