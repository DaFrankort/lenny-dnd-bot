import discord

from embed import ErrorEmbed
from embeds.config.sources import ConfigSourcesView
from logic.app_commands import SimpleCommand, SimpleCommandGroup
from logic.config import user_has_config_permissions, user_is_admin


class ConfigManageSourcesCommand(SimpleCommand):
    name = "sources"
    desc = "Manage your server's sources!"
    help = "Open up an overview you can use to configure the bot's settings in your server."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)

        if itr.guild is None:
            embed = ErrorEmbed("Sources can only be managed in a server!")
            await itr.response.send_message(embed=embed, ephemeral=True)
        elif user_is_admin(itr.user) or user_has_config_permissions(itr.guild, itr.user):
            view = ConfigSourcesView(server=itr.guild, allow_configuration=True)
            await itr.response.send_message(view=view, ephemeral=True)
        else:
            embed = ErrorEmbed("You don't have permission to manage sources!")
            await itr.response.send_message(embed=embed, ephemeral=True)


class ConfigViewSourcesCommand(SimpleCommand):
    name = "sources"
    desc = "View your server's sources!"
    help = "Open up an overview you can use to view the bot's settings in your server."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        if itr.guild is None:
            embed = ErrorEmbed("Sources can only be viewed in a server!")
            await itr.response.send_message(embed=embed, ephemeral=True)
        else:
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
