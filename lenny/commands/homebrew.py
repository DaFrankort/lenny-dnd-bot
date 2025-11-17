import discord
from discord.app_commands import autocomplete, choices, describe

from commands.command import SimpleCommand, SimpleCommandGroup
from embeds.homebrew import (
    HomebrewEditModal,
    HomebrewEmbed,
    HomebrewEntryAddModal,
    HomebrewListView,
)
from logic.homebrew import HomebrewData, HomebrewEntryType
from logic.markdown import MDFile


class HomebrewCommandGroup(SimpleCommandGroup):
    name = "homebrew"
    desc = "Manage your custom secrets for your tome of homebrew."

    def __init__(self):
        super().__init__()
        self.add_command(HomebrewAddCommand())
        self.add_command(HomebrewSearchCommand())
        self.add_command(HomebrewListCommand())
        self.add_command(HomebrewEditCommand())
        self.add_command(HomebrewRemoveCommand())
        self.guild_only = True


class HomebrewAddCommand(SimpleCommand):
    name = "add"
    desc = "Add custom content to your tome of homebrew."
    help = "Add new homebrew content to your server."

    async def handle(self, itr: discord.Interaction, md_file: discord.Attachment | None = None):
        self.log(itr)
        md_data = None
        if md_file:
            md_data = await MDFile.from_attachment(md_file)
        modal = HomebrewEntryAddModal(itr, md_data)
        await itr.response.send_modal(modal)


async def homebrew_name_autocomplete(itr: discord.Interaction, current: str):
    return HomebrewData.get(itr).get_autocomplete_suggestions(itr, current)


class HomebrewSearchCommand(SimpleCommand):
    name = "search"
    desc = "Search for secrets in your tome of homebrew."
    help = "Search for existing homebrew content from your server."

    @autocomplete(name=homebrew_name_autocomplete)
    @describe(name="The name of the entry you want to find.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        entry = HomebrewData.get(itr).get(name)
        embed = HomebrewEmbed(itr, entry)
        await itr.response.send_message(embed=embed)


class HomebrewListCommand(SimpleCommand):
    name = "list"
    desc = "View all entries in your server's tome of homebrew!"
    help = "Shows all homebrew content in your server and filter by entry type."

    @choices(filter=HomebrewEntryType.choices())
    @describe(filter="Show only homebrew entries of a certain type. Shows all by default.")
    async def handle(self, itr: discord.Interaction, filter: str | None = None):  # pylint: disable=redefined-builtin
        self.log(itr)
        view = HomebrewListView(itr, filter)
        await itr.response.send_message(view=view, ephemeral=True)


class HomebrewEditCommand(SimpleCommand):
    name = "edit"
    desc = "Edit entries in your tome of homebrew!"
    help = "Edit a homebrew entry you created. Can edit all entries if you have permissions to manage messages."

    @autocomplete(name=homebrew_name_autocomplete)
    @describe(name="The name of the entry you want to edit.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        entry = HomebrewData.get(itr).get(name)
        modal = HomebrewEditModal(itr, entry)
        await itr.response.send_modal(modal)


class HomebrewRemoveCommand(SimpleCommand):
    name = "remove"
    desc = "Remove entries in your tome of homebrew!"
    help = "Remove a homebrew entry you created. Can remove all entries if you have permissions to manage messages."

    @autocomplete(name=homebrew_name_autocomplete)
    @describe(name="The name of the entry you want to remove.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        entry = HomebrewData.get(itr).delete(itr, name)
        embed = HomebrewEmbed(itr, entry)
        embed.color = discord.Color.red()
        await itr.response.send_message(f"{itr.user.mention} removed a homebrew {entry.entry_type.value}:", embed=embed)
