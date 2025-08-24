import discord

from app_commands import SimpleCommand
from embeds import UserActionEmbed
from stats import Stats


class StatsCommand(SimpleCommand):
    name = "stats"
    desc = "Roll stats for a new character, using the 4d6 drop lowest method."
    help = "Performs six dice rolls using the 4d6 drop lowest method, providing you with six values to use for your new character's stats."

    def __init__(self):
        super().__init__()

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        stats = Stats(itr)
        embed = UserActionEmbed(
            itr=itr,
            title=stats.get_embed_title(),
            description=stats.get_embed_description(),
        )
        chart_image = stats.get_radar_chart(itr)
        embed.set_image(url=f"attachment://{chart_image.filename}")
        await itr.response.send_message(embed=embed, file=chart_image)
