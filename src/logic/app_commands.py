import logging
import discord
from abc import abstractmethod
from enum import Enum
from embed import SimpleEmbed


def get_error_embed(error: discord.app_commands.AppCommandError) -> discord.Embed:
    titles = {
        "CommandOnCooldown": "You're going too fast!",
        "MissingPermissions": "You don't have permission to do that!",
        "BotMissingPermissions": "I don't have permission to do that!",
        "CheckFailure": "You don't meet the requirements to do that!",
        "ValueError": "Invalid input!",
        "RuntimeError": "Can't do that right now!",
    }

    parts = str(error).split(": ")
    if len(parts) < 2:
        logging.error(f"Unknown error format: {error}")
        return SimpleEmbed(
            title="Something went wrong!",
            description="An unknown error occurred.",
            color=discord.Color.red(),
        )

    error_title = titles.get(parts[1], "Something went wrong!")
    error_msg = ": ".join(parts[2:]) if len(parts) > 2 else ""
    embed = SimpleEmbed(title=error_title, description=error_msg, color=discord.Color.red())

    return embed


class SimpleCommandGroup(discord.app_commands.Group):
    name: str = None
    desc: str = None

    def __init__(self):
        if self.name is None:
            raise NotImplementedError(f"'name' not defined in {type(self)}")
        if self.desc is None:
            raise NotImplementedError(f"'desc' not defined in {type(self)}")

        super().__init__(name=self.name, description=self.desc)


class SimpleCommand(discord.app_commands.Command):
    name: str = None
    desc: str = None
    help: str = None

    def __init__(self):
        if self.name is None:
            raise NotImplementedError(f"'name' not defined in {type(self)}")
        if self.desc is None:
            raise NotImplementedError(f"'desc' not defined in {type(self)}")
        if self.help is None:
            raise NotImplementedError(f"'help' not defined in {type(self)}")

        super().__init__(name=self.name, description=self.desc, callback=self.callback)
        self.on_error = self.error_handler

    @property
    def command_name(self) -> str:
        def get_command_string(name: str, cmd: discord.app_commands.Command | discord.app_commands.Group) -> str:
            if cmd.parent:
                name = f"{cmd.parent.name} {name}"
                return get_command_string(name, cmd.parent)
            return name

        return get_command_string(self.name, self)

    @property
    def command(self) -> str:
        args = []
        for param in self.parameters:
            arg = param.name
            arg = f"<{arg}>" if param.required else f"[{arg}]"
            args.append(arg)
        args_str = " ".join(args)

        return f"/{self.command_name} {args_str}".strip()

    def log(self, itr: discord.Interaction):
        """Log user's command-usage in the terminal"""

        try:
            criteria = [f"[{k}={v}]" for k, v in vars(itr.namespace).items()]
        except Exception:
            criteria = []
        criteria_text = " ".join(criteria)

        logging.info(f"{itr.user.name} => /{self.command_name} {criteria_text}")

    @abstractmethod
    async def callback(self, itr: discord.Interaction):
        raise NotImplementedError

    async def error_handler(
        self,
        _,
        itr: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        embed = get_error_embed(error)

        if not itr.response.is_done():
            await itr.response.send_message(embed=embed, ephemeral=True)
            return

        await itr.followup.send(embed=embed, ephemeral=True)
        message = await itr.original_response()
        await message.delete(delay=10)


class SimpleContextMenu(discord.app_commands.ContextMenu):
    name: str = None

    def __init__(self):
        if self.name is None:
            raise NotImplementedError(f"'name' not defined in {type(self)}")

        super().__init__(
            name=self.name,
            callback=self.callback,
        )

    def log(self, itr: discord.Interaction):
        logging.info(f"{itr.user.name} => {self.name}")

    @abstractmethod
    async def callback(self, itr: discord.Interaction):
        raise NotImplementedError


class ChoicedEnum(Enum):
    @classmethod
    def choices(cls) -> list[discord.app_commands.Choice]:
        return [discord.app_commands.Choice(name=e.name.title(), value=e.value) for e in cls]
