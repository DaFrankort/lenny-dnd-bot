import datetime
import discord
from components.items import TitleTextDisplay
from embeds import SimpleEmbed
from logic.app_commands import SimpleCommand, SimpleCommandGroup, send_error_message

multipliers = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
}


class RelativeTimestampEmbed(SimpleEmbed):
    def __init__(self, timestamp: str):
        super().__init__(title=timestamp, description=f"```{timestamp}```")


class TimestampCommandGroup(SimpleCommandGroup):
    name = "timestamp"
    desc = "Generate timestamp tags, which update to be up-to-date or correct between timezones."

    def __init__(self):
        super().__init__()
        self.add_command(TimestampDateCommand())
        self.add_command(TimestampRelativeCommand())


class TimestampRelativeCommand(SimpleCommand):
    name = "relative"
    desc = "Generate a 'in x'-style timestamp, relative from when you use this command."
    help = "Generates a relative timestamp like this example: <t:2102148000:R>"

    async def callback(
        self,
        itr: discord.Interaction,
        seconds: discord.app_commands.Range[int, 0, 60] = 0,
        minutes: discord.app_commands.Range[int, 0, 60] = 0,
        hours: discord.app_commands.Range[int, 0, 24] = 0,
        days: discord.app_commands.Range[int, 0, 7] = 0,
        weeks: discord.app_commands.Range[int, 0, 54] = 0,
    ):
        total_seconds = (
            seconds * multipliers["s"]
            + minutes * multipliers["m"]
            + hours * multipliers["h"]
            + days * multipliers["d"]
            + weeks * multipliers["w"]
        )

        if total_seconds == 0:
            await send_error_message(itr, "You must specify a time!")

        now = discord.utils.utcnow().replace(second=0, microsecond=0)
        base_time = int(now.timestamp())
        unix_timestamp = base_time + total_seconds
        timestamp = f"<t:{unix_timestamp}:R>"

        embed = RelativeTimestampEmbed(timestamp=timestamp)
        await itr.response.send_message(embed=embed, ephemeral=True)


class TimestampButton(discord.ui.Button):
    timestamp: str

    def __init__(self, timestamp: str):
        super().__init__(style=discord.ButtonStyle.primary, label="Clip")
        self.timestamp = timestamp

    async def callback(self, itr: discord.Interaction):
        await itr.response.send_message(f"{self.timestamp}", ephemeral=True)


class TimestampDatesContainerView(discord.ui.LayoutView):
    def __init__(self, unix_timestamp: int):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_color=discord.Color.dark_green())

        title = f"Timestamps for <t:{unix_timestamp}:f>"
        container.add_item(TitleTextDisplay(name=title))

        formats = ["t", "T", "d", "D", "f", "F", "R"]
        for format in formats:
            timestamp = f"<t:{unix_timestamp}:{format}>"
            button = TimestampButton(timestamp=timestamp)
            section = discord.ui.Section(f"## {timestamp}", accessory=button)

            container.add_item(section)
            container.add_item(discord.ui.TextDisplay(f"```{timestamp}```"))

        self.add_item(container)


class TimestampDateCommand(SimpleCommand):
    name = "date"
    desc = "Generate a timestamp which is synced between timezones."
    help = "Will generate all variants of timestamps to copy paste in discord."

    async def callback(
        self,
        itr: discord.Interaction,
        time: str,
        timezone: discord.app_commands.Range[int, -14, 14],
        date: str = None,
    ):
        base_date = discord.utils.utcnow().date()
        if date:
            try:
                base_date = datetime.datetime.strptime(date, "%d/%m/%Y").date()
            except Exception as e:
                await send_error_message(itr, f"Invalid input: {e}")
                return

        time = time.replace(":", "")
        if not time.isdigit() or len(time) != 4:
            await send_error_message(
                itr, "Time must be in HHMM format (e.g. `0930` or `15:45`)."
            )
            return

        hours, minutes = divmod(int(time), 100)
        try:
            dt = datetime.datetime.combine(
                base_date, datetime.time(hour=hours, minute=minutes)
            )
        except ValueError as e:
            await send_error_message(itr, f"Invalid time: {e}")
            return

        dt_utc = dt - datetime.timedelta(hours=timezone)  # Adjust for timezone
        unix_timestamp = int(dt_utc.replace(tzinfo=datetime.timezone.utc).timestamp())

        view = TimestampDatesContainerView(unix_timestamp)
        await itr.response.send_message(view=view, ephemeral=True)
