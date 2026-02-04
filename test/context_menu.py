import pytest

# Required to mark the library as essential for testing in our workflows
import pytest_asyncio  # noqa: F401 # type: ignore


from bot import Bot
from commands.command import BaseContextMenu
from context_menus.delete import DeleteContextMenu
from utils.mocking import MockBot, MockInteraction, MockServerTextChannel, MockServerTextMessage, MockUser


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
