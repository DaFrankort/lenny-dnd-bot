import discord
from embeds.homebrew import HomebrewEntryAddModal
from logic.app_commands import SimpleCommand, SimpleCommandGroup, check_is_guild
from logic.dnd.abstract import DNDObjectTypes
from logic.dnd.data import Data


class HomebrewCommandGroup(SimpleCommandGroup):
    name = "homebrew"
    desc = "Manage Homebrew content for your server."

    def __init__(self):
        super().__init__()
        self.add_command(HomebrewAddCommand())
        self.add_command(HomebrewRemoveCommand())


class HomebrewAddCommand(SimpleCommand):
    name = "add"
    desc = "Inscribe a new secret into your mystical tome of homebrew!"
    help = "Remove a Homebrew entry from your server's collection."

    @discord.app_commands.choices(dnd_type=DNDObjectTypes.choices())
    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction, dnd_type: str):
        self.log(itr)
        await itr.response.send_modal(HomebrewEntryAddModal(dnd_type))


class HomebrewRemoveCommand(SimpleCommand):
    name = "remove"
    desc = "Strike records of a secret from your mystical tome of homebrew!"
    help = "Remove a Homebrew entry from your server's collection. You can only delete entries you created, unless you have permission to manage messages."

    async def entry_autocomplete(self, itr: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
        return Data.get_homebrew_autocomplete_suggestions(current, itr)

    @discord.app_commands.autocomplete(entry=entry_autocomplete)
    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction, entry: str):
        self.log(itr)
        await itr.response.send_message(
            f"If I programmed this command, I would now remove the homebrew entry '{entry}' from the server.", ephemeral=True
        )
