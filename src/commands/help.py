import discord

from embeds import UserActionEmbed
from help import HelpEmbed
from i18n import t
from logger import log_cmd
from stats import Stats


class HelpCommand(discord.app_commands.Command):
    name = t("commands.help.name")
    description = t("commands.help.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    @discord.app_commands.choices(tab=HelpEmbed.get_tab_choices())
    async def callback(itr: discord.Interaction, tab: str = None):
        log_cmd(itr)
        embed = HelpEmbed(tab)
        await itr.response.send_message(embed=embed, view=embed.view, ephemeral=True)
