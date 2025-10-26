import discord
from embeds.homebrew import HomebrewEntryAddModal
from logic.app_commands import SimpleCommand, check_is_guild
from logic.dnd.abstract import DNDObjectTypes


class HomebrewCommand(SimpleCommand):
    name = "homebrew"
    desc = "Add Homebrew content to your server."
    help = "Use this command to add, view, or manage homebrew content for your server."

    @discord.app_commands.choices(dnd_type=DNDObjectTypes.choices())
    @discord.app_commands.check(check_is_guild)
    async def callback(self, itr: discord.Interaction, dnd_type: str):
        self.log(itr)
        await itr.response.send_modal(HomebrewEntryAddModal(dnd_type))
