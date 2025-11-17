import discord

from components.items import TitleTextDisplay
from embeds.embed import SimpleEmbed


class RelativeTimestampEmbed(SimpleEmbed):
    def __init__(self, timestamp: str):
        super().__init__(title=timestamp, description=f"```{timestamp}```")


class TimestampButton(discord.ui.Button["TimestampDatesContainerView"]):
    timestamp: str

    def __init__(self, timestamp: str):
        super().__init__(style=discord.ButtonStyle.primary, label="Clip")
        self.timestamp = timestamp

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{self.timestamp}", ephemeral=True)


class TimestampDatesContainerView(discord.ui.LayoutView):
    def __init__(self, unix_timestamp: int):
        super().__init__(timeout=None)
        container = discord.ui.Container[TimestampDatesContainerView](accent_color=discord.Color.dark_green())

        title = f"Timestamps for <t:{unix_timestamp}:f>"
        container.add_item(TitleTextDisplay(name=title))

        time_formats = ["t", "T", "d", "D", "f", "F", "R"]
        for time_format in time_formats:
            timestamp = f"<t:{unix_timestamp}:{time_format}>"
            button = TimestampButton(timestamp=timestamp)
            section = discord.ui.Section(f"## {timestamp}", accessory=button)

            container.add_item(section)
            container.add_item(discord.ui.TextDisplay(f"```{timestamp}```"))

        self.add_item(container)
