import datetime
import discord
from components.items import TitleTextDisplay
from logic.app_commands import SimpleCommand, SimpleCommandGroup, send_error_message
from logic.time import TIME_MULTIPLIERS, RelativeTimestampEmbed, get_relative_timestamp


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

    @discord.app_commands.describe(
        seconds="Seconds from now (0-60)",
        minutes="Minutes from now (0-60)",
        hours="Hours from now (0-24)",
        days="Days from now (0-7)",
        weeks="Weeks from now (0-999)",
    )
    async def callback(
        self,
        itr: discord.Interaction,
        seconds: discord.app_commands.Range[int, 0, 60] = 0,
        minutes: discord.app_commands.Range[int, 0, 60] = 0,
        hours: discord.app_commands.Range[int, 0, 24] = 0,
        days: discord.app_commands.Range[int, 0, 7] = 0,
        weeks: discord.app_commands.Range[int, 0, 999] = 0,
    ):
        total_seconds = (
            seconds * TIME_MULTIPLIERS["s"]
            + minutes * TIME_MULTIPLIERS["m"]
            + hours * TIME_MULTIPLIERS["h"]
            + days * TIME_MULTIPLIERS["d"]
            + weeks * TIME_MULTIPLIERS["w"]
        )

        if total_seconds == 0:
            await send_error_message(itr, "You must specify a time!")
            return

        timestamp = get_relative_timestamp(discord.utils.utcnow(), seconds)
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

    @discord.app_commands.describe(
        time="Time in HHMM or HH format (e.g. 930, 15:45 or 20).",
        timezone="Timezone offset from UTC (between -14 and +14).",
        date="Optional date in DD/MM/YYYY or DD/MM format (defaults to today).",
    )
    async def callback(
        self,
        itr: discord.Interaction,
        time: str,
        timezone: discord.app_commands.Range[int, -14, 14],
        date: str = None,
    ):
        base_date = discord.utils.utcnow().date()
        if date:
            date = date.replace(".", "/").strip()
            parts = date.split("/")

            try:
                if len(parts) == 1:  # DD
                    day = int(parts[0])
                    month = discord.utils.utcnow().month
                    year = discord.utils.utcnow().year
                    date = f"{day:02d}/{month:02d}/{year}"
                elif len(parts) == 2:  # DD/MM
                    day, month = map(int, parts)
                    year = discord.utils.utcnow().year
                    date = f"{day:02d}/{month:02d}/{year}"
                elif len(parts) == 3:  # DD/MM/YYYY
                    pass
                else:
                    raise ValueError("Invalid date format")

                base_date = datetime.datetime.strptime(date, "%d/%m/%Y").date()
            except Exception:
                await send_error_message(
                    itr,
                    "Date must be in `DD`, `DD/MM`, or `DD/MM/YYYY` format, and must be a valid date!",
                )
                return

        time = time.replace(":", "").strip()
        if not time.isdigit() or not (1 <= len(time) <= 4):
            await send_error_message(
                itr,
                "Time must be in HHMM or HH format (e.g. `0930`, `15:45`, `700`, or `7`).",
            )
            return

        if len(time) <= 2:
            time = f"{time}00"
        time = time.zfill(4)

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
