import discord
from discord.app_commands import choices
from commands.command import SimpleCommand, SimpleCommandGroup
from embeds.config.permissions import ConfigPermissionsView
from embeds.config.sources import ConfigSourcesView
from embeds.embed import ErrorEmbed
from logic.config import Config
from logic.dnd.source import ContentChoice


class ConfigSourcesCommand(SimpleCommand):
    name = "sources"
    desc = "Manage your server's sources!"
    help = "Open up an overview you can use to configure the bot's sources in your server."

    @choices(content=ContentChoice.choices())
    async def handle(self, itr: discord.Interaction, content: str):
        self.log(itr)

        config = Config.get(itr)
        content_choice = ContentChoice(content)
        if itr.guild is None:
            embed = ErrorEmbed("Sources can only be managed in a server!")
            await itr.response.send_message(embed=embed, ephemeral=True)
        elif config.user_is_admin_or_has_config_permissions(itr.user):
            view = ConfigSourcesView(itr=itr, allow_configuration=True, content=content_choice)
            await itr.response.send_message(view=view, ephemeral=True)
        else:
            view = ConfigSourcesView(itr=itr, allow_configuration=False, content=content_choice)
            await itr.response.send_message(view=view, ephemeral=True)


class ConfigPermissionsCommand(SimpleCommand):
    name = "permissions"
    desc = "Manage your server's permissions!"
    help = "Open up an overview you can use to configure the bot's permissions in your server."

    async def handle(self, itr: discord.Interaction):
        self.log(itr)

        config = Config.get(itr)
        if itr.guild is None:
            embed = ErrorEmbed("Permissions can only be managed in a server!")
            await itr.response.send_message(embed=embed, ephemeral=True)
        elif config.user_is_admin(itr.user):
            view = ConfigPermissionsView(itr=itr)
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
