import discord
from discord.utils import MISSING

from logic.color import UserColor
from logic.distribution import DistributionResult


class DistributionEmbed(discord.Embed):
    chart: discord.File

    def __init__(self, itr: discord.Interaction, result: DistributionResult):
        self.chart = result.chart or MISSING
        color = UserColor.get(itr)

        super().__init__(
            color=color,
            title=f"Distribution for {result.expression}{result.advantage.title_suffix}!",
            type="rich",
        )

        self.add_field(name="Mean", value=f"{result.mean:.2f}", inline=True)
        self.add_field(name="Stdev", value=f"{result.stdev:.2f}", inline=True)
        self.set_image(url=f"attachment://{self.chart.filename}")

        if result.min_to_beat is not None:
            min_to_beat, odds = result.min_to_beat
            self.add_field(
                name=f"Odds to beat {min_to_beat}",
                value=f"{100 * odds:.2f}%",
                inline=True,
            )
