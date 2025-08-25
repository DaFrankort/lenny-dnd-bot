import discord

from charts import get_radar_chart
from logic.app_commands import SimpleCommand, SimpleCommandGroup
from embeds import UserActionEmbed
from stats import Stats
from user_colors import UserColor


class StatsCommandGroup(SimpleCommandGroup):
    name = "stats"
    desc = "Roll or visualise stats for a D&D character!"

    def __init__(self):
        super().__init__()
        self.add_command(StatsRollCommand())
        self.add_command(StatsVisualiseCommand())


class StatsRollCommand(SimpleCommand):
    name = "roll"
    desc = "Roll stats for a new character, using the 4d6 drop lowest method."
    help = "Performs six dice rolls using the 4d6 drop lowest method, providing you with six values to use for your new character's stats."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        stats = Stats(itr)
        embed = UserActionEmbed(
            itr=itr,
            title=stats.get_embed_title(),
            description=stats.get_embed_description(),
        )
        color = UserColor.get(itr)
        chart_image = stats.get_radar_chart(color)
        embed.set_image(url=f"attachment://{chart_image.filename}")
        await itr.response.send_message(embed=embed, file=chart_image)


class StatsVisualiseCommand(SimpleCommand):
    name = "visualise"
    desc = "Visualise your stats onto a radar graph!"
    help = "Visualises your character's stats inside of a radar graph."

    async def callback(
        self,
        itr: discord.Interaction,
        str: discord.app_commands.Range[int, 0, 48],
        dex: discord.app_commands.Range[int, 0, 48],
        con: discord.app_commands.Range[int, 0, 48],
        int: discord.app_commands.Range[int, 0, 48],
        wis: discord.app_commands.Range[int, 0, 48],
        cha: discord.app_commands.Range[int, 0, 48],
    ):
        self.log(itr)
        embed = UserActionEmbed(
            itr=itr,
            title=f"{itr.user.display_name}'s stats visualised!",
            description="",
        )
        color = UserColor.get(itr)
        chart_image = get_radar_chart(
            results=[str, dex, con, int, wis, cha],
            labels=["STR", "DEX", "CON", "INT", "WIS", "CHA"],
            color=color
        )
        embed.set_image(url=f"attachment://{chart_image.filename}")
        await itr.response.send_message(embed=embed, file=chart_image)
