import discord

from commands.command import SimpleContextMenu
from embeds.timestamp import RelativeTimestampEmbed
from logic.timestamp import get_relative_timestamp_from_message


class RequestTimestampContextMenu(SimpleContextMenu):
    name = "Request timestamp from message"
    help = (
        "Generates a timestamp relative to when a message was sent.\n"
        "Example: A message saying 'I am ready in 5 minutes!', sent at 14:00: this context will create a timestamp for 14:05."
    )

    def __init__(self):
        super().__init__()

    async def handle(self, interaction: discord.Interaction, message: discord.Message):
        result = get_relative_timestamp_from_message(message)
        if result is None:
            raise ValueError("Couldn't find any mention of times in that message!")

        embed = RelativeTimestampEmbed(timestamp=result)
        await interaction.response.send_message(embed=embed, ephemeral=True)
