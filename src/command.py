import logging
import discord
from abc import abstractmethod
from embed import SimpleEmbed


def check_is_guild(itr: discord.Interaction) -> bool:
    if itr.guild is None:
        raise discord.app_commands.CheckFailure("This command can only be used in a server.")
    return True


def get_error_embed(error: discord.app_commands.AppCommandError) -> discord.Embed:
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
    def command(self) -> str:
        args = []
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
