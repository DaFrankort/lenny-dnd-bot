import discord
from embed import SimpleEmbed
from embeds.timestamp import RelativeTimestampEmbed
from command import SimpleContextMenu
from logic.timestamp import get_relative_timestamp_from_message


class RequestTimestampContextMenu(SimpleContextMenu):
    name = "Request Timestamp from message"

    def __init__(self):
        super().__init__()

    async def callback(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        itr: discord.Interaction,
        message: discord.Message,
    ):
        if message.author.bot:
            user = itr.client.user
            name = user.name if user is not None else "The bot"
            error_message = f"{name} can't retrieve timestamps from their own messages."
            embed = SimpleEmbed(title="Something went wrong!", description=error_message, color=discord.Color.red())
            await itr.response.send_message(embed=embed, ephemeral=True)
            return

        result = get_relative_timestamp_from_message(message)
        if result is None:
            embed = SimpleEmbed(
                title="Something went wrong!",
                description="Couldn't find any mention of times in that message.",
                color=discord.Color.red(),
            )
            await itr.response.send_message(embed=embed, ephemeral=True)
            return
        embed = RelativeTimestampEmbed(timestamp=result)
        await itr.response.send_message(embed=embed, ephemeral=True)
