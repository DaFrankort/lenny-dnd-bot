import re
import discord
from logic.app_commands import SimpleContextMenu, send_error_message
from logic.time import TIME_MULTIPLIERS, RelativeTimestampEmbed, get_relative_timestamp


class RequestTimestampContextMenu(SimpleContextMenu):
    name = "Request Timestamp from message"

    def __init__(self):
        super().__init__()

    async def callback(self, itr: discord.Interaction, message: discord.Message):
        if message.author.bot:
            await send_error_message(
                itr,
                f"{itr.client.user.name} can't retrieve timestamps from their own messages.",
            )
            return

        matches = re.findall(
            r"(\d+(?:[.,]\d+)?)\s*([smhdw])", message.content, re.IGNORECASE
        )
        if not matches:
            await send_error_message(
                itr, "Couldn't find any mention of times in that message."
            )
            return

        seconds = 0
        for amount, unit in matches:
            unit = unit.lower()
            if unit not in TIME_MULTIPLIERS:
                continue
            amount = amount.replace(",", ".")
            seconds += float(amount) * TIME_MULTIPLIERS[unit]

        timestamp = get_relative_timestamp(message.created_at, seconds)
        embed = RelativeTimestampEmbed(timestamp=timestamp)
        await itr.response.send_message(embed=embed, ephemeral=True)
