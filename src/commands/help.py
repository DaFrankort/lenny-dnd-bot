import discord

from embeds.help import HelpEmbed
from logic.app_commands import SimpleCommand


class HelpCommand(SimpleCommand):
    name = "help"
    desc = "Get an overview of all commands."
    help = "Show the help tab for the given section. If no section is provided, this overview is given."

    tree: discord.app_commands.CommandTree

    def __init__(self, tree: discord.app_commands.CommandTree):
        self.tree = tree
        super().__init__()

    @discord.app_commands.choices(tab=HelpEmbed.get_tab_choices())
    async def callback(self, itr: discord.Interaction, tab: str = None):
        self.log(itr)
        embed = HelpEmbed(self.tree, tab=tab)
        await itr.response.send_message(embed=embed, view=embed.view, ephemeral=True)
