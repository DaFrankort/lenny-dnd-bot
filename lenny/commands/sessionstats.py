import discord

from commands.command import BaseCommand
from logic.sessionsstats import SessionStatistics


class SessionStatsCommand(BaseCommand):
    name = "session"
    desc = "test"
    help = "wip."

    def __init__(self):
        super().__init__()
        self.guild_only = True

    async def handle(self, itr: discord.Interaction):
        stats = SessionStatistics.get(itr)
        if stats is None:
            await itr.response.send_message("No session active!", ephemeral=True)
        else:
            await itr.response.send_message(stats.get_report(itr))
