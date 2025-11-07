import discord
from components.items import TitleTextDisplay
from embed import SimpleEmbed


class RelativeTimestampEmbed(SimpleEmbed):
    def __init__(self, timestamp: str):
        super().__init__(title=timestamp, description=f"```{timestamp}```")


class TimestampButton(discord.ui.Button):
    timestamp: str

    def __init__(self, timestamp: str):
        super().__init__(style=discord.ButtonStyle.primary, label="Clip")
        self.timestamp = timestamp

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{self.timestamp}", ephemeral=True)


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
