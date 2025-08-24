from abc import abstractmethod
import logging
import discord


class SimpleCommandGroup(discord.app_commands.Group):
    name: str
    desc: str

    def __init__(self):
        super().__init__(name=self.name, description=self.desc)


class SimpleCommand(discord.app_commands.Command):
    name: str
    desc: str
    help: str

    def __init__(self):
        super().__init__(name=self.name, description=self.desc, callback=self.callback)

    @property
    def command_name(self) -> str:
        def get_command_string(
            name: str, cmd: discord.app_commands.Command | discord.app_commands.Group
        ) -> str:
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

        return f"/{self.command_name} {args_str}"

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


class SimpleContextMenu(discord.app_commands.ContextMenu):
    name: str

    def __init__(self):
        super().__init__(
            name=self.name,
            callback=self.callback,
        )

    def log(self, itr: discord.Interaction):
        logging.info(
            f"{itr.user.name} => {itr.message.author.name} / {itr.message.id} / Apps / {itr.command.name}"
        )

    @abstractmethod
    async def callback(self, itr: discord.Interaction):
        raise NotImplementedError
