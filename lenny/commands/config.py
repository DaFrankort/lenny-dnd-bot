import discord
from discord.app_commands import autocomplete, choices

from commands.command import BaseCommand, BaseCommandGroup
from embeds.config.permissions import ConfigPermissionsView
from embeds.config.sources import ConfigSourcesView
from embeds.embed import ErrorEmbed
from logic.config import OFFICIAL_SOURCES, PARTNERED_SOURCES, Config
from logic.dnd.source import ContentChoice


async def source_autocomplete(itr: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    current = current.strip().upper().replace(" ", "")
    if not current:
        return []

    entries = []
    try:
        value = itr.data["options"][0]["options"][0]["value"]  # type: ignore
        content = ContentChoice(value)

        if content is ContentChoice.OFFICIAL:
            entries = OFFICIAL_SOURCES.entries
        elif content is ContentChoice.PARTNERED:
            entries = PARTNERED_SOURCES.entries
        else:
            entries = OFFICIAL_SOURCES.entries + PARTNERED_SOURCES.entries

    except Exception:
        return []  # If user fills in `search` before `content`, return nothing.

    # TODO use fuzzy matching instead.
    result: list[discord.app_commands.Choice[str]] = []
    for src in entries:
        if current in src.id.upper() or current in src.name.upper().replace(" ", ""):
            name = src.id if src.id == src.name else f"{src.id} - {src.name}"
            result.append(discord.app_commands.Choice(name=name, value=src.id))

    return result[:25]


class ConfigSourcesCommand(BaseCommand):
    name = "sources"
    desc = "Manage your server's sources!"
    help = "Open up an overview you can use to configure the bot's sources in your server."

    @choices(content=ContentChoice.choices())
    @autocomplete(search=source_autocomplete)
    async def handle(self, itr: discord.Interaction, content: str, search: str | None = None):
        config = Config.get(itr)
        content_choice = ContentChoice(content)
        if itr.guild is None:
            embed = ErrorEmbed("Sources can only be managed in a server!")
            await itr.response.send_message(embed=embed, ephemeral=True)
        elif config.user_is_admin_or_has_config_permissions(itr.user):
            view = ConfigSourcesView(itr=itr, allow_configuration=True, content=content_choice, search=search)
            await itr.response.send_message(view=view, ephemeral=True)
        else:
            view = ConfigSourcesView(itr=itr, allow_configuration=False, content=content_choice, search=search)
            await itr.response.send_message(view=view, ephemeral=True)


class ConfigPermissionsCommand(BaseCommand):
    name = "permissions"
    desc = "Manage your server's permissions!"
    help = "Open up an overview you can use to configure the bot's permissions in your server."

    async def handle(self, itr: discord.Interaction):
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


class ConfigCommand(BaseCommandGroup):
    name = "config"
    desc = "Configure your server's settings!"

    def __init__(self):
        super().__init__()
        self.add_command(ConfigPermissionsCommand())
        self.add_command(ConfigSourcesCommand())
        self.guild_only = True
