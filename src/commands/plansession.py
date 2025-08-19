import discord

from i18n import t
from polls import SessionPlanPoll


class PlanSessionCommand(discord.app_commands.Command):
    name = t("commands.plansession.name")
    description = t("commands.plansession.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    @discord.app_commands.describe(
        in_weeks=t("commands.plansession.args.in_weeks"),
        poll_duration=t("commands.plansession.args.poll_duration"),
    )
    async def callback(
        self,
        itr: discord.Interaction,
        in_weeks: discord.app_commands.Range[int, 0, 48],
        poll_duration: discord.app_commands.Range[int, 1, 168] = 24,
    ):
        poll = SessionPlanPoll(in_weeks, poll_duration)
        await itr.response.send_message(poll=poll)
