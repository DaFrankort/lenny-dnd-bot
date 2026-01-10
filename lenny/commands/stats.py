import discord
from discord.app_commands import describe

from commands.command import BaseCommand, BaseCommandGroup
from embeds.embed import UserActionEmbed
from embeds.stats import StatsEmbed
from logic.charts import get_radar_chart
from logic.color import UserColor
from logic.stats import Stats


class StatsCommandGroup(BaseCommandGroup):
    name = "stats"
    desc = "Roll or visualize stats for a D&D character!"

    def __init__(self):
        super().__init__()
        self.add_command(StatsRollCommand())
        self.add_command(StatsVisualizeCommand())


class StatsRollCommand(BaseCommand):
    name = "roll"
    desc = "Roll stats for a new character, using the 4d6 drop lowest method."
    help = "Performs six dice rolls using the 4d6 drop lowest method, providing you with six values to use for your new character's stats."

    @describe(min_total="The minimum value your stats should total to. Higher totals may fail to generate.")
    async def handle(self, itr: discord.Interaction, min_total: discord.app_commands.Range[int, 18, 108] = 18):
        # Min total is between 18 (3*6) and 108 (18*6), because these are the lowest and highest stats a player can roll.
        self.log(itr)
        await itr.response.defer()
        stats = Stats(min_total)
        embed = StatsEmbed(itr, stats)
        chart = embed.chart

        embed.set_image(url=f"attachment://{chart.filename}")
        await itr.followup.send(embed=embed, file=chart)


class StatsVisualizeCommand(BaseCommand):
    name = "visualize"
    desc = "Visualize your stats onto a radar graph!"
    help = "Visualizes your character's stats inside of a radar graph."

    @describe(
        str="A value from 0-48 representing your Strength score.",
        dex="A value from 0-48 representing your Dexterity score.",
        con="A value from 0-48 representing your Constitution score.",
        int="A value from 0-48 representing your Intelligence score.",
        wis="A value from 0-48 representing your Wisdom score.",
        cha="A value from 0-48 representing your Charisma score.",
    )
    async def handle(  # pyright:ignore
        self,
        itr: discord.Interaction,
        str: discord.app_commands.Range[int, 0, 48],  # pylint: disable=redefined-builtin
        dex: discord.app_commands.Range[int, 0, 48],
        con: discord.app_commands.Range[int, 0, 48],
        int: discord.app_commands.Range[int, 0, 48],  # pylint: disable=redefined-builtin
        wis: discord.app_commands.Range[int, 0, 48],
        cha: discord.app_commands.Range[int, 0, 48],
    ):
        self.log(itr)
        embed = UserActionEmbed(
            itr=itr,
            title=f"{itr.user.display_name}'s stats visualized!",
            description="",
        )
        color = UserColor.get(itr)
        values = [str, dex, con, int, wis, cha]
        labels = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        chart = get_radar_chart(values=values, labels=labels, color=color)
        embed.set_image(url=f"attachment://{chart.filename}")
        await itr.response.send_message(embed=embed, file=chart)
