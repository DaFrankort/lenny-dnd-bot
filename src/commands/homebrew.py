import discord
from logic.app_commands import SimpleCommand
from logic.dnd.abstract import DNDObjectTypes


class HomebrewCommand(SimpleCommand):
    name = "homebrew"
    desc = "Add Homebrew content to your server."
    help = "Use this command to add, view, or manage homebrew content for your server."

    @discord.app_commands.choices(dnd_type=DNDObjectTypes.choices())
    async def callback(self, itr: discord.Interaction, dnd_type: str):
        await itr.response.send_message(f"UNDER CONSTRUCTION", ephemeral=True)
