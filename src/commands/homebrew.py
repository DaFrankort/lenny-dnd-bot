import discord
from embeds.homebrew import HomebrewEmbed, HomebrewEntryAddModal
from logic.app_commands import SimpleCommand, SimpleCommandGroup, check_is_guild
from logic.homebrew import DNDObjectTypes, HomebrewData


class HomebrewCommandGroup(SimpleCommandGroup):
    name = "homebrew"
    desc = "Manage your custom secrets for your tome of homebrew."

    def __init__(self):
        super().__init__()
        self.add_command(HomebrewAddCommand())
        self.add_command(HomebrewSearchCommand())
        self.add_command(HomebrewListCommand())


class HomebrewAddCommand(SimpleCommand):
    name = "add"
    desc = "Add custom content to your tome of homebrew."
    help = "Add new homebrew content to your server."

    @discord.app_commands.choices(dnd_type=DNDObjectTypes.choices())
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
    desc = "View and edit all content in your tome of homebrew."
    help = "Shows all homebrew content in your server and allows you to edit entries, if you have the correct permissions or are the author."

    @discord.app_commands.choices(filter=DNDObjectTypes.choices())
    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction, filter: str = None):
        self.log(itr)
        entries = HomebrewData.get(itr).get_all(filter)
        message = []
        for entry in entries:
            message.append(f"- {entry.name}")
        await itr.response.send_message("\n".join(message))
