import discord
from discord.app_commands import describe

from commands.command import BaseCommand
from embeds.plansession import SessionPlanPoll


class PlanSessionCommand(BaseCommand):
    name = "plansession"
    desc = "Stop squandering and poll your party's availability in x weeks!"
    help = "Creates a poll for players to select their availability in x weeks. Generates poll-answers from Monday - Sunday, along with an 'Earlier' and 'Later' option. If 0 is specified it will poll for the remaining days in the current week."

    def __init__(self):
        super().__init__()
        self.guild_only = True

    @describe(
        in_weeks="How many weeks from now? (0 = this week, 1 = next week, ...)",
        poll_duration="How long until the poll closes? (Defaults to 24h)",
    )
    async def handle(
        self,
        itr: discord.Interaction,
        in_weeks: discord.app_commands.Range[int, 0, 48],
        poll_duration: discord.app_commands.Range[int, 1, 168] = 24,
    ):
        self.log(itr)
        poll = SessionPlanPoll(in_weeks, poll_duration)
        await itr.response.send_message(poll=poll)
