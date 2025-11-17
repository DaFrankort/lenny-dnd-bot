import discord
from discord.app_commands import choices, describe

from commands.command import SimpleCommand
from embeds.help import HelpEmbed


class HelpCommand(SimpleCommand):
    name = "help"
    desc = "Get an overview of all commands."
    help = "Show the help tab for the given section. If no section is provided, this overview is given."

    tree: discord.app_commands.CommandTree

    def __init__(self, tree: discord.app_commands.CommandTree):
        self.tree = tree
        super().__init__()

    @choices(tab=HelpEmbed.get_tab_choices())
    @describe(tab="Specify a page for more information on it's commands. Shows a general overview by default.")
    async def handle(self, itr: discord.Interaction, tab: str | None = None):
        self.log(itr)
        embed = HelpEmbed(self.tree, tab=tab)
        await itr.response.send_message(embed=embed, view=embed.view, ephemeral=True)
