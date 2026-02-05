from abc import abstractmethod

import discord

from commands.command import handle_command_error


class BaseContextMenu(discord.app_commands.ContextMenu):
    name: str = ""
    help: str = ""

    def __init__(self):
        if not self.name:
            raise NotImplementedError(f"'name' not defined in {type(self)}")
        if not self.help:
            raise NotImplementedError(f"'help' not defined in {type(self)}")

        super().__init__(
            name=self.name,
            callback=self.handle,
        )
        self.on_error = self.error_handler

    @abstractmethod
    async def handle(self, interaction: discord.Interaction, message: discord.Message) -> None:
        raise NotImplementedError()

    @staticmethod
    async def error_handler(itr: discord.Interaction, error: discord.app_commands.AppCommandError):
        await handle_command_error(itr, error)
