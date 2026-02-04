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

    async def test_delete_bot_message(self, cmd: BaseContextMenu, itr: MockInteraction, message: MockServerTextMessage):
        """Verify that the bot is allowed to delete its own message."""

        assert itr.user.id == message.author.id
        await cmd.handle(itr, message)

    async def test_delete_other_message(self, cmd: BaseContextMenu, itr: MockInteraction, channel: MockServerTextChannel):
        """Verify that the bot is not allowed to delete another user's message."""

        other = MockUser("other")
        message = MockServerTextMessage(other, channel)

        assert itr.user.id != message.author.id
        with pytest.raises(PermissionError):
            await cmd.handle(itr, message)
