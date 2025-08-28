import re
import discord
from embeds import SimpleEmbed
from logic.app_commands import SimpleContextMenu, send_error_message


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

        matches = re.findall(r"(\d+)\s*([smhdw])", message.content, re.IGNORECASE)
        if not matches:
            await send_error_message(
                itr, "Couldn't find any mention of times in that message."
            )
            return

        multipliers = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800,
        }

        seconds = 0
        for amount, unit in matches:
            unit = unit.lower()
            if unit not in multipliers:
                continue
            seconds += int(amount) * multipliers[unit]

        base_time = int(message.created_at.timestamp())
        unix_timestamp = base_time + seconds
        timestamp = f"<t:{unix_timestamp}:R>"

        embed = SimpleEmbed(title=timestamp, description=f"```{timestamp}```")
        await itr.response.send_message(embed=embed, ephemeral=True)
