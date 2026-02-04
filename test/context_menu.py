import pytest

# Required to mark the library as essential for testing in our workflows
import pytest_asyncio  # noqa: F401 # type: ignore
from utils.mocking import (
    MockBot,
    MockInteraction,
    MockServerTextChannel,
    MockServerTextMessage,
    MockTextMessageEmbed,
    MockUser,
)

from bot import Bot
from commands.command import BaseContextMenu
from context_menus.delete import DeleteContextMenu
from context_menus.favorites import AddFavoriteContextMenu
from context_menus.reroll import RerollContextMenu
from logic.dnd.data import Data


def get_context_menu_cmd(bot: Bot, name: str) -> BaseContextMenu:
    commands = bot.tree.get_commands()
    for command in commands:
        if command.name == name:
            if not isinstance(command, BaseContextMenu):
                raise ValueError(f"Command with name '{name}' is not a context menu!")
            return command

    raise ValueError(f"Context menu with name '{name}' not found!")


class TestDeleteContextMenu:
    @pytest.fixture()
    def cmd(self):
        return get_context_menu_cmd(MockBot(), DeleteContextMenu.name)

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


class TestFavoritesContextMenu:
    @pytest.fixture()
    def cmd(self):
        return get_context_menu_cmd(MockBot(), AddFavoriteContextMenu.name)

    async def test_add_valid_entry_to_favorites(self, cmd: BaseContextMenu):
        """Try to add a valid entry to favorites."""

        entry = Data.spells.entries[0]

        user = MockUser("bot")
        itr = MockInteraction(user)
        channel = MockServerTextChannel()
        message = MockServerTextMessage(user, channel)
        message.embeds = [MockTextMessageEmbed(title=entry.title)]

        await cmd.handle(itr, message)

    async def test_add_invalid_title_entry_to_favorites(self, cmd: BaseContextMenu):
        """Try to add an invalid entry with an invalid title to favorites."""

        user = MockUser("bot")
        itr = MockInteraction(user)
        channel = MockServerTextChannel()
        message = MockServerTextMessage(user, channel)
        message.embeds = [MockTextMessageEmbed(title="Invalid title")]

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)

    async def test_add_invalid_user_entry_to_favorites(self, cmd: BaseContextMenu):
        """Try to add an invalid entry with an embed from a different user to favorites."""

        entry = Data.spells.entries[0]
        user = MockUser("bot")
        other = MockUser("other")

        itr = MockInteraction(user)
        channel = MockServerTextChannel()
        message = MockServerTextMessage(other, channel)
        message.embeds = [MockTextMessageEmbed(title=entry.title)]

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)

    async def test_add_invalid_embeds_entry_to_favorites(self, cmd: BaseContextMenu):
        """Try to add an invalid entry with no entry embeds to favorites."""

        user = MockUser("bot")

        itr = MockInteraction(user)
        channel = MockServerTextChannel()
        message = MockServerTextMessage(user, channel)
        message.embeds = []

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)

    async def test_add_invalid_nonexistent_entry_to_favorites(self, cmd: BaseContextMenu):
        """Try to add non-existent entry to favorites."""

        user = MockUser("bot")

        itr = MockInteraction(user)
        channel = MockServerTextChannel()
        message = MockServerTextMessage(user, channel)
        message.embeds = [MockTextMessageEmbed(title="Does-Not-Exist (DoesNotExist)")]

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)


class TestRerollContextMenu:
    @pytest.fixture()
    def cmd(self):
        return get_context_menu_cmd(MockBot(), RerollContextMenu.name)

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
    async def test_reroll_embeds(self, cmd: BaseContextMenu, is_valid: bool, title: str):
        """Attempt to re-roll on various titles."""

        user = MockUser("bot")
        itr = MockInteraction(user)
        channel = MockServerTextChannel()
        message = MockServerTextMessage(user, channel)

        message.embeds = [self.create_roll_embed(title)]

        if is_valid:
            await cmd.handle(itr, message)
        else:
            with pytest.raises(ValueError):
                await cmd.handle(itr, message)

    async def test_invalid_embed_reroll(self, cmd: BaseContextMenu):
        """Try to roll on message with no embeds."""
        user = MockUser("bot")
        itr = MockInteraction(user)
        channel = MockServerTextChannel()
        message = MockServerTextMessage(user, channel)
        message.embeds = []

        with pytest.raises(ValueError):
            await cmd.handle(itr, message)

    async def test_invalid_user_reroll(self, cmd: BaseContextMenu):
        """Try to roll on an embed from a different user."""

        user = MockUser("bot")
        other = MockUser("other")

        itr = MockInteraction(user)
        channel = MockServerTextChannel()
        message = MockServerTextMessage(other, channel)

        with pytest.raises(PermissionError):
            await cmd.handle(itr, message)
