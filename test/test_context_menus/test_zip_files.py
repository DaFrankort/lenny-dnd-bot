import pytest
from test_context_menus.context_menu import TestAbstractContextMenu
from utils.mocking import (
    MockImage,
    MockInteraction,
    MockMessage,
)

from commands.command import BaseContextMenu
from context_menus.zip_files import ZipAttachmentsContextMenu


class TestZipFilesContextMenu(TestAbstractContextMenu):
    context_menu_name = ZipAttachmentsContextMenu.name

    async def test_valid_attachments(self, cmd: BaseContextMenu, itr: MockInteraction, message: MockMessage):
        """Try to zip the valid attachments to a message."""

        message.attachments = [MockImage(), MockImage()]

        await cmd.handle(itr, message)

    async def test_no_attachments(self, cmd: BaseContextMenu, itr: MockInteraction, message: MockMessage):
        """Try to zip a message with no attachments."""

        message.attachments = []

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)
