import discord

from embeds.config.sources import ConfigSourcesView
from logic.app_commands import SimpleCommand, SimpleCommandGroup


class ConfigManageSourcesCommand(SimpleCommand):
    name = "sources"
    desc = "Manage your server's sources!"
    help = "Open up an overview you can use to configure the bot's settings in your server."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        view = ConfigSourcesView(server=itr.guild, allow_configuration=True)
        await itr.response.send_message(view=view, ephemeral=True)


class ConfigViewSourcesCommand(SimpleCommand):
    name = "sources"
    desc = "View your server's sources!"
    help = "Open up an overview you can use to view the bot's settings in your server."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        view = ConfigSourcesView(server=itr.guild, allow_configuration=False)
        await itr.response.send_message(view=view, ephemeral=True)


class ConfigManageCommandGroup(SimpleCommandGroup):
    name = "manage"
    desc = "Manage your server's settings!"

    def __init__(self):
        super().__init__()
        self.add_command(ConfigManageSourcesCommand())


class ConfigViewCommandGroup(SimpleCommandGroup):
    name = "view"
    desc = "View your server's settings!"

    def __init__(self):
        super().__init__()
        self.add_command(ConfigViewSourcesCommand())


class ConfigCommand(SimpleCommandGroup):
    name = "config"
    desc = "Configure your server's settings!"

    def __init__(self):
        super().__init__()
        self.add_command(ConfigManageCommandGroup())
        self.add_command(ConfigViewCommandGroup())
