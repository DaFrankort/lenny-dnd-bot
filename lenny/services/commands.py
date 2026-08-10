import importlib
import inspect
import logging
import pkgutil
from collections.abc import Sequence
from typing import Any

import discord

import commands
import context_menus
from commands.command import BaseCommand, BaseCommandGroup
from commands.help import HelpCommand
from context_menus.context_menu import BaseContextMenu


class CommandRegistry:
    def __init__(self, tree: discord.app_commands.CommandTree):
        self.tree = tree

    def find_and_register(self):
        logging.info("Finding and registering discord commands...")
        for pkg in (commands, context_menus):
            for _, mod_name, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
                importlib.import_module(mod_name)

        command_set: set[Any] = set()
        for cls in BaseCommandGroup.__subclasses__():
            if not inspect.isabstract(cls):
                group = cls()
                self.tree.add_command(group)
                logging.debug("# %s", str(cls.__name__))
                for cmd in group.walk_commands():
                    logging.debug("\t+ %s", type(cmd).__name__)
                    command_set.add(type(cmd))

        for cls in BaseCommand.__subclasses__():
            if cls in command_set:
                continue

            logging.debug("+ %s", str(cls.__name__))
            if cls == HelpCommand:  # Exception, requires the tree to work.
                self.tree.add_command(HelpCommand(self.tree))
            elif not inspect.isabstract(cls):
                self.tree.add_command(cls())

        for cls in BaseContextMenu.__subclasses__():
            if not inspect.isabstract(cls):
                self.tree.add_command(cls())

    async def sync(self, guild_id: int | None = None, client_guilds: Sequence[discord.Guild] | None = None) -> None:
        if guild_id and client_guilds:
            guild = discord.utils.get(client_guilds, id=guild_id)
            if guild:
                await self.tree.sync(guild=guild)
                logging.info("Synced commands to guild: %s (%d)", guild.name, guild.id)
            else:
                logging.warning("Could not find guild ID %d for syncing", guild_id)

        await self.tree.sync()
        logging.info("Synced global command tree.")
