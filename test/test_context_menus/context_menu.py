import pytest
from mocking import MockBot, MockInteraction, MockMessage, MockUser

from bot import Bot
from context_menus.context_menu import BaseContextMenu


def get_context_menu_cmd(bot: Bot, name: str) -> BaseContextMenu:
    commands = bot.tree.get_commands()
    for command in commands:
        if command.name == name:
            if not isinstance(command, BaseContextMenu):
                raise TypeError(f"Command with name '{name}' is not a context menu!")
            return command

    raise LookupError(f"Context menu with name '{name}' not found!")


class TestAbstractContextMenu:
    context_menu_name: str = ""

    @pytest.fixture()
    def cmd(self):
        if not self.context_menu_name:
            raise NotImplementedError(
                f"Context menu test class '{self.__class__.__name__}' does not have its context_menu_name value set!"
            )
        return get_context_menu_cmd(MockBot(), self.context_menu_name)

    @pytest.fixture()
    def user(self):
        return MockUser("bot")

    @pytest.fixture()
    def itr(self, user: MockUser):
        return MockInteraction(user)

    @pytest.fixture()
    def message(self, user: MockUser):
        return MockMessage(user)
