import discord
from embeds.timestamp import RelativeTimestampEmbed
from logic.app_commands import SimpleContextMenu, send_error_message
from logic.timestamp import get_relative_timestamp_from_message


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

        result = get_relative_timestamp_from_message(message)
        if result is None:
            await send_error_message(
                itr, "Couldn't find any mention of times in that message."
            )
            return
        embed = RelativeTimestampEmbed(timestamp=result)
        await itr.response.send_message(embed=embed, ephemeral=True)
