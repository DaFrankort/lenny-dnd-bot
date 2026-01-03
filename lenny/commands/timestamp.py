import discord
from discord.app_commands import Range, describe

from commands.command import BaseCommand, BaseCommandGroup
from embeds.timestamp import RelativeTimestampEmbed, TimestampDatesContainerView
from logic.timestamp import get_date_timestamp, get_relative_timestamp_from_now


class TimestampCommandGroup(BaseCommandGroup):
    name = "timestamp"
    desc = "Generate timestamp tags, which update to be up-to-date or correct between timezones."

    def __init__(self):
        super().__init__()
        self.add_command(TimestampDateCommand())
        self.add_command(TimestampRelativeCommand())


class TimestampRelativeCommand(BaseCommand):
    name = "relative"
    desc = "Generate a 'in x'-style timestamp, relative from when you use this command."
    help = "Generates a relative timestamp like this example: <t:2102148000:R>"

    @describe(
        seconds="Seconds from now (0-60)",
        minutes="Minutes from now (0-60)",
        hours="Hours from now (0-24)",
        days="Days from now (0-7)",
        weeks="Weeks from now (0-999)",
    )
    async def handle(
        self,
        itr: discord.Interaction,
        seconds: Range[int, 0, 60] = 0,
        minutes: Range[int, 0, 60] = 0,
        hours: Range[int, 0, 24] = 0,
        days: Range[int, 0, 7] = 0,
        weeks: Range[int, 0, 999] = 0,
    ):
        self.log(itr)
        result = get_relative_timestamp_from_now(seconds, minutes, hours, days, weeks)
        embed = RelativeTimestampEmbed(timestamp=result)
        await itr.response.send_message(embed=embed, ephemeral=True)


class TimestampDateCommand(BaseCommand):
    name = "date"
    desc = "Generate a timestamp which is synced between timezones."
    help = "Will generate all variants of timestamps to copy paste in discord."

    @describe(
        time="Time in HHMM or HH format (e.g. 930, 15:45 or 20).",
        timezone="Timezone offset from UTC (between -14 and +14).",
        date="Optional date in DD/MM/YYYY or DD/MM format (defaults to today).",
    )
    async def handle(
        self,
        itr: discord.Interaction,
        time: str,
        timezone: Range[int, -14, 14],
        date: str | None = None,
    ):
        self.log(itr)
        result = get_date_timestamp(time, timezone, date)
        view = TimestampDatesContainerView(result)
        await itr.response.send_message(view=view, ephemeral=True)
