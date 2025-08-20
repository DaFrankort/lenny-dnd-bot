import discord

from embeds import UserActionEmbed
from logger import log_cmd
from stats import Stats


class StatsCommand(discord.app_commands.Command):
    name = "stats"
    desc = "Roll stats for a new character, using the 4d6 drop lowest method."
    help = "Performs six dice rolls using the 4d6 drop lowest method, providing you with six values to use for your new character's stats."
    command = "/stats"

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction):
        log_cmd(itr)
        stats = Stats(itr)
        embed = UserActionEmbed(
            itr=itr,
            title=stats.get_embed_title(),
            description=stats.get_embed_description(),
        )
        chart_image = stats.get_radar_chart(itr)
        embed.set_image(url=f"attachment://{chart_image.filename}")
        await itr.response.send_message(embed=embed, file=chart_image)
