import discord

from commands.command import BaseCommand, BaseCommandGroup
from embeds.embed import UserActionEmbed
from embeds.session import UserSessionStatEmbed
from logic.session.stats import SessionStatistics


class SessionStatsCommandGroup(BaseCommandGroup):
    name = "sessionstats"
    desc = "Track user data during a session."

    def __init__(self):
        super().__init__()
        self.add_command(SessionStatsStartCommand())
        self.add_command(SessionStatsStopCommand())
        self.add_command(SessionStatsViewCommand())


class SessionStatsStartCommand(BaseCommand):
    name = "start"
    desc = "Start tracking dice-statistics from users in this text-channel!"
    help = "Your dice-roll results are tracked and statistics can be drawn using this command!"

    def __init__(self):
        super().__init__()
        self.guild_only = True

    async def handle(self, itr: discord.Interaction):
        if itr.channel is None:
            raise PermissionError("Can only start session-tracking in a valid text-channel.")

        SessionStatistics.start(itr)
        embed = UserActionEmbed(
            itr=itr,
            title=f"{itr.user.name} started session-tracking for this channel!",
            description=f"Tracking statistics for <#{itr.channel.id}>.",
        )
        await itr.response.send_message(embed=embed)


class SessionStatsStopCommand(BaseCommand):
    name = "stop"
    desc = "Stop tracking dice-statistics from users in this text-channel."
    help = "Clears the current data from on-going session."

    def __init__(self):
        super().__init__()
        self.guild_only = True

    async def handle(self, itr: discord.Interaction):
        stats = SessionStatistics.stop(itr)
        result = stats.get_report(itr)
        embeds = [UserSessionStatEmbed(stat) for stat in result.users_stats[:10]]
        await itr.response.send_message(
            f"Session tracking stopped by {itr.user.mention}!\n{result.base_info}", embeds=embeds, files=result.files()
        )


class SessionStatsViewCommand(BaseCommand):
    name = "view"
    desc = "View details about your current session!"
    help = "You can view the statistics of all dice-rolls that happened in this channel since start of tracking."

    def __init__(self):
        super().__init__()
        self.guild_only = True

    async def handle(self, itr: discord.Interaction):
        stats = SessionStatistics.get(itr)
        if stats is None:
            raise KeyError("No session active in this channel!")
        else:
            result = stats.get_report(itr)
            embeds = [UserSessionStatEmbed(stat) for stat in result.users_stats[:10]]
            await itr.response.send_message(result.base_info, embeds=embeds, files=result.files())
