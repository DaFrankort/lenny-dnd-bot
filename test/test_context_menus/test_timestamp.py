import pytest
from test_context_menus.context_menu import TestAbstractContextMenu
from mocking import MockInteraction, MockMessage, MockUser

from context_menus.context_menu import BaseContextMenu
from context_menus.timestamp import RequestTimestampContextMenu


class TestTimestampContextMenu(TestAbstractContextMenu):
    context_menu_name = RequestTimestampContextMenu.name

    async def test_valid_timestamp(self, cmd: BaseContextMenu, user: MockUser):
        """Try to retrieve the timestamp from a valid message."""

        itr = MockInteraction(user)
        message = MockMessage(user, content="in 4 hours")

        await cmd.handle(itr, message)

    async def test_invalid_timestamp(self, cmd: BaseContextMenu, user: MockUser):
        """Try to retrieve the timestamp from a valid message."""

        itr = MockInteraction(user)
        message = MockMessage(user, content="somewhere in the future")

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)
