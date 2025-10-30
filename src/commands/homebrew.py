import discord
from embeds.homebrew import HomebrewEditModal, HomebrewEmbed, HomebrewEntryAddModal, HomebrewListView
from logic.app_commands import SimpleCommand, SimpleCommandGroup, check_is_guild
from logic.homebrew import DNDObjectType, HomebrewData


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


class HomebrewAddCommand(SimpleCommand):
    name = "add"
    desc = "Add custom content to your tome of homebrew."
    help = "Add new homebrew content to your server."

    @discord.app_commands.choices(dnd_type=DNDObjectType.choices())
    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction, dnd_type: str):
        self.log(itr)
        await itr.response.send_modal(HomebrewEntryAddModal(dnd_type))


class HomebrewSearchCommand(SimpleCommand):
    name = "search"
    desc = "Search for secrets in your tome of homebrew."
    help = "Search for existing homebrew content from your server."

    async def entry_autocomplete(self, itr: discord.Interaction, current: str):
        return HomebrewData.get(itr).get_autocomplete_suggestions(current)

    @discord.app_commands.autocomplete(entry=entry_autocomplete)
    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction, entry: str):
        self.log(itr)
        entry = HomebrewData.get(itr).get(entry)
        embed = HomebrewEmbed(itr, entry)
        await itr.response.send_message(embed=embed)


class HomebrewListCommand(SimpleCommand):
    name = "list"
    desc = "View all entries in your server's tome of homebrew!"
    help = "Shows all homebrew content in your server and filter by entry type."

    @discord.app_commands.choices(filter=DNDObjectType.choices())
    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction, filter: str = None):
        self.log(itr)
        view = HomebrewListView(itr, filter)
        await itr.response.send_message(view=view, ephemeral=True)


class HomebrewEditCommand(SimpleCommand):
    name = "edit"
    desc = "Edit entries in your tome of homebrew!"
    help = "Edit a homebrew entry you created. Can edit all entries if you have permissions to manage messages."

    async def entry_autocomplete(self, itr: discord.Interaction, current: str):
        return HomebrewData.get(itr).get_autocomplete_suggestions(current, itr=itr)

    @discord.app_commands.autocomplete(entry=entry_autocomplete)
    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction, entry: str):
        self.log(itr)
        entry_item = HomebrewData.get(itr).get(entry)
        modal = HomebrewEditModal(entry_item)
        await itr.response.send_modal(modal)


class HomebrewRemoveCommand(SimpleCommand):
    name = "remove"
    desc = "Remove entries in your tome of homebrew!"
    help = "Remove a homebrew entry you created. Can remove all entries if you have permissions to manage messages."

    async def entry_autocomplete(self, itr: discord.Interaction, current: str):
        return HomebrewData.get(itr).get_autocomplete_suggestions(current, itr=itr)

    @discord.app_commands.autocomplete(entry=entry_autocomplete)
    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction, entry: str):
        self.log(itr)
        entry = HomebrewData.get(itr).delete(itr, entry)
        embed = HomebrewEmbed(itr, entry)
        embed.color = discord.Color.red()
        await itr.response.send_message(f"{itr.user.display_name} Removed homebrew {entry.object_type.value}:", embed=embed)
