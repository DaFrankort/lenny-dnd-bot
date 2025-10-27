import discord
from embeds.homebrew import HomebrewEntryAddModal
from logic.app_commands import SimpleCommand, SimpleCommandGroup, check_is_guild
from logic.homebrew import DNDObjectTypes


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

    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        await itr.response.send_message("UNDER CONSTRUCTION :(")


class HomebrewListCommand(SimpleCommand):
    name = "list"
    desc = "View and edit all content in your tome of homebrew."
    help = "Shows all homebrew content in your server and allows you to edit entries, if you have the correct permissions or are the author."

    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        await itr.response.send_message("UNDER CONSTRUCTION :(")
