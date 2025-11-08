import logging
from typing import Any
import discord
from abc import abstractmethod
from embed import SimpleEmbed


def get_error_embed(error: discord.app_commands.AppCommandError | Exception) -> discord.Embed:
    if isinstance(error, discord.app_commands.CheckFailure):
        return SimpleEmbed(
            title="You don't meet the requirements to do that!",
            description=str(error),
            color=discord.Color.red(),
        )

    titles = {
        "ValueError": "Invalid input!",
        "RuntimeError": "Can't do that right now!",
    }
    parts = str(error).split(": ")
    if len(parts) < 2:
        error_title = "Something went wrong!"
        error_msg = str(error)
    else:
        error_title = titles.get(parts[1], "Something went wrong!")
        error_msg = ": ".join(parts[2:]) if len(parts) > 2 else ""
    embed = SimpleEmbed(title=error_title, description=error_msg, color=discord.Color.red())

    return embed


class SimpleCommandGroup(discord.app_commands.Group):
    name: str = ""
    desc: str = ""

    def __init__(self):
        if not self.name:
            raise NotImplementedError(f"'name' not defined in {type(self)}")
        if not self.desc:
            raise NotImplementedError(f"'desc' not defined in {type(self)}")

        super().__init__(name=self.name, description=self.desc)


class SimpleCommand(discord.app_commands.Command[SimpleCommandGroup, Any, None]):
    name: str = ""
    desc: str = ""
    help: str = ""

    def __init__(self):
        if not self.name:
            raise NotImplementedError(f"'name' not defined in {type(self)}")
        if not self.desc:
            raise NotImplementedError(f"'desc' not defined in {type(self)}")
        if not self.help:
            raise NotImplementedError(f"'help' not defined in {type(self)}")

        super().__init__(name=self.name, description=self.desc, callback=self.callback)  # type: ignore
        self.on_error = self.error_handler

    @property
    def command(self) -> str:
        args: list[str] = []
        for param in self.parameters:
            arg = param.name
            arg = f"<{arg}>" if param.required else f"[{arg}]"
            args.append(arg)
        args_str = " ".join(args)

        return f"/{self.qualified_name} {args_str}".strip()

    def log(self, itr: discord.Interaction):
        """Log user's command-usage in the terminal"""

        try:
            criteria = [f"[{k}={v}]" for k, v in vars(itr.namespace).items()]
        except Exception:
            criteria = []
        criteria_text = " ".join(criteria)

        logging.info(f"{itr.user.name} => /{self.qualified_name} {criteria_text}")

    @abstractmethod
    async def callback(self, itr: discord.Interaction):  # pyright: ignore
        raise NotImplementedError

    async def error_handler(
        self,
        _: Any,
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

    @property
    def params(self):
        return self._params


class SimpleContextMenu(discord.app_commands.ContextMenu):
    name: str = ""
    help: str = ""

    def __init__(self):
        if not self.name:
            raise NotImplementedError(f"'name' not defined in {type(self)}")
        if not self.help:
            raise NotImplementedError(f"'help' not defined in {type(self)}")

        super().__init__(
            name=self.name,
            callback=self.callback,
        )

    def log(self, itr: discord.Interaction):
        logging.info(f"{itr.user.name} => {self.name}")

    @abstractmethod
    async def callback(self, interaction: discord.Interaction, message: discord.Message):  # pyright: ignore
        raise NotImplementedError
