import discord

from embeds.config import ConfigSourcesView
from logic.app_commands import SimpleCommand
from logic.dnd.data import DNDData


class ConfigCommand(SimpleCommand):
    name = "config"
    desc = "Configure your server's settings!"
    help = "Open up an overview you can use to configure the bot's settings in your server."

    data: DNDData

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        view = ConfigSourcesView(server=itr.guild)
        await itr.response.send_message(view=view)
