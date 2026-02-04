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
from context_menus.favorites import AddFavoriteContextMenu
from logic.dnd.data import Data


class TestFavoritesContextMenu(TestAbstractContextMenu):
    context_menu_name = AddFavoriteContextMenu.name

    async def test_add_valid_entry_to_favorites(
        self,
        cmd: BaseContextMenu,
        itr: MockInteraction,
        message: MockServerTextMessage,
    ):
        """Try to add a valid entry to favorites."""

        entry = Data.spells.entries[0]
        message.embeds = [MockTextMessageEmbed(title=entry.title)]

        await cmd.handle(itr, message)

    async def test_add_invalid_title_entry_to_favorites(
        self,
        cmd: BaseContextMenu,
        itr: MockInteraction,
        message: MockServerTextMessage,
    ):
        """Try to add an invalid entry with an invalid title to favorites."""

        message.embeds = [MockTextMessageEmbed(title="Invalid title")]

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)

    async def test_add_invalid_user_entry_to_favorites(
        self,
        cmd: BaseContextMenu,
        itr: MockInteraction,
        channel: MockServerTextChannel,
    ):
        """Try to add a valid entry with an embed from a different user to favorites."""

        entry = Data.spells.entries[0]
        other = MockUser("other")

        message = MockServerTextMessage(other, channel)
        message.embeds = [MockTextMessageEmbed(title=entry.title)]

        assert itr.user.id != message.author.id
        with pytest.raises(ValueError):
            await cmd.handle(itr, message)

    async def test_add_invalid_embeds_entry_to_favorites(
        self,
        cmd: BaseContextMenu,
        itr: MockInteraction,
        message: MockServerTextMessage,
    ):
        """Try to add an invalid entry with no entry embeds to favorites."""

        message.embeds = []

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)

    async def test_add_invalid_nonexistent_entry_to_favorites(
        self,
        cmd: BaseContextMenu,
        itr: MockInteraction,
        message: MockServerTextMessage,
    ):
        """Try to add non-existent entry to favorites."""

        message.embeds = [MockTextMessageEmbed(title="Does-Not-Exist (DoesNotExist)")]

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)
