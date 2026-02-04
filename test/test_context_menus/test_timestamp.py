import pytest
from test_context_menus.context_menu import TestAbstractContextMenu
from utils.mocking import (
    MockInteraction,
    MockServerTextChannel,
    MockServerTextMessage,
    MockUser,
)

from commands.command import BaseContextMenu
from context_menus.timestamp import RequestTimestampContextMenu


class TestTimestampContextMenu(TestAbstractContextMenu):
    context_menu_name = RequestTimestampContextMenu.name

    async def test_valid_timestamp(self, cmd: BaseContextMenu, user: MockUser, channel: MockServerTextChannel):
        """Try to retrieve the timestamp from a valid message."""

        itr = MockInteraction(user)
        message = MockServerTextMessage(user, channel, "in 4 hours")

        await cmd.handle(itr, message)

    async def test_invalid_timestamp(self, cmd: BaseContextMenu, user: MockUser, channel: MockServerTextChannel):
        """Try to retrieve the timestamp from a valid message."""

        itr = MockInteraction(user)
        message = MockServerTextMessage(user, channel, "somewhere in the future")

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)
