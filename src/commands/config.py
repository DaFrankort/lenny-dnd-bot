import discord

from embeds.embed import ErrorEmbed
from embeds.config.permissions import ConfigPermissionsView
from embeds.config.sources import ConfigSourcesView
from commands.command import SimpleCommand, SimpleCommandGroup
from logic.config import user_is_admin, user_is_admin_or_has_config_permissions


class ConfigSourcesCommand(SimpleCommand):
    name = "sources"
    desc = "Manage your server's sources!"
    help = "Open up an overview you can use to configure the bot's sources in your server."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)

        if itr.guild is None:
            embed = ErrorEmbed("Sources can only be managed in a server!")
            await itr.response.send_message(embed=embed, ephemeral=True)
        elif user_is_admin_or_has_config_permissions(itr.guild, itr.user):
            view = ConfigSourcesView(server=itr.guild, allow_configuration=True)
            await itr.response.send_message(view=view, ephemeral=True)
        else:
            view = ConfigSourcesView(server=itr.guild, allow_configuration=False)
            await itr.response.send_message(view=view, ephemeral=True)


class ConfigPermissionsCommand(SimpleCommand):
    name = "permissions"
    desc = "Manage your server's permissions!"
    help = "Open up an overview you can use to configure the bot's permissions in your server."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)

        if itr.guild is None:
            embed = ErrorEmbed("Permissions can only be managed in a server!")
            await itr.response.send_message(embed=embed, ephemeral=True)
        elif user_is_admin(itr.user):
            view = ConfigPermissionsView(server=itr.guild)
            await itr.response.send_message(view=view, ephemeral=True)
        else:
            embed = ErrorEmbed("You don't have permission to manage permissions!")
            await itr.response.send_message(embed=embed, ephemeral=True)


class ConfigCommand(SimpleCommandGroup):
    name = "config"
    desc = "Configure your server's settings!"

    def __init__(self):
        super().__init__()
        self.add_command(ConfigPermissionsCommand())
        self.add_command(ConfigSourcesCommand())
        self.guild_only = True
