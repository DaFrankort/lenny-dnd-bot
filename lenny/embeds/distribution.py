import discord
from discord.utils import MISSING

from logic.color import UserColor
from logic.distribution import DistributionResult


class DistributionEmbed(discord.Embed):
    chart: discord.File

    def __init__(self, itr: discord.Interaction, result: DistributionResult):
        color = UserColor.get(itr)

        if len(result.distributions) == 1:
            self._init_single_chart(color, result)
        else:
            self._init_multi_chart(color, result)

        self.chart = result.chart or MISSING
        self.set_image(url=f"attachment://{self.chart.filename}")

    def _init_single_chart(self, color: int, result: DistributionResult) -> None:
        dist = result.distributions[0]
        mean = dist.distribution.mean()
        stdev = dist.distribution.stdev()

        super().__init__(
            color=color,
            title=f"Distribution for {dist.expression}{result.advantage.title_suffix}!",
            type="rich",
        )

        self.add_field(name="Mean", value=f"{mean:.2f}", inline=True)
        self.add_field(name="Deviation", value=f"{stdev:.2f}", inline=True)
        self.add_field(name="Range", value=f"{result.min} ~ {result.max}", inline=True)

        if result.min_to_beat is not None:
            self.add_field(
                name=f"Odds to beat {result.min_to_beat}",
                value=f"{(100 * dist.min_to_beat_odds):.2f}%",
                inline=True,
            )

    def _init_multi_chart(self, color: int, result: DistributionResult) -> None:
        title = ", ".join(r.expression for r in result.distributions)
        super().__init__(
            color=color,
            title=f"Distribution for {title}{result.advantage.title_suffix}!",
            type="rich",
        )

        self.add_field(name="Range", value=f"{result.min} ~ {result.max}", inline=True)
