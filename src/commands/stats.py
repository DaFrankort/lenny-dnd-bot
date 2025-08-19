import discord

from embeds import UserActionEmbed
from i18n import t
from logger import log_cmd
from stats import Stats


class StatsCommand(discord.app_commands.Command):
    name = t("commands.stats.name")
    description = t("commands.stats.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
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
