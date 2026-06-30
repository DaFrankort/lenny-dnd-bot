import discord

from commands.command import BaseCommand
from embeds.sessionstats import UserSessionStatEmbed
from logic.session.stats import SessionStatistics


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
            result = stats.get_report(itr)
            embeds = [UserSessionStatEmbed(stat) for stat in result.users_stats[:10]]
            await itr.response.send_message(result.base_info, embeds=embeds)
