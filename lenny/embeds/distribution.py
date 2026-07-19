import discord
from discord.utils import MISSING

from logic.color import UserColor
from logic.distribution import DistributionResult, distribution
from logic.roll import Advantage
from methods import join_strings


class SingleDistributionEmbed(discord.Embed):
    chart: discord.File

    def __init__(self, itr: discord.Interaction, result: DistributionResult):
        color = UserColor.get(itr)

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

        self.chart = result.chart or MISSING
        self.set_image(url=f"attachment://{self.chart.filename}")


class MultiDistributionButton(discord.ui.Button[discord.ui.LayoutView]):
    expression: str
    advantage: Advantage

    def __init__(self, expression: str, advantage: Advantage) -> None:
        super().__init__(label=expression)
        self.expression = expression
        self.advantage = advantage
        self.callback = self.send_distribution

    async def send_distribution(self, interaction: discord.Interaction) -> None:
        # If the MultiDistributionView was sent without a timeout, then this one can
        # also be calculated without a timeout.
        color = UserColor.get(interaction)
        result = distribution(expressions=self.expression, advantage=self.advantage, color=color)
        embed = SingleDistributionEmbed(interaction, result)
        await interaction.response.send_message(embed=embed, file=embed.chart)


class MultiDistributionView(discord.ui.LayoutView):
    chart: discord.File
    advantage: Advantage

    def __init__(self, itr: discord.Interaction, result: DistributionResult) -> None:
        self.chart = result.chart
        self.advantage = result.advantage

        super().__init__(timeout=None)

        color = UserColor.get(itr)
        expressions = list(r.expression for r in result.distributions)
        joined_expressions = join_strings(expressions, ", ", " and ")

        title = f"### Distributions for {joined_expressions}!"
        range_text = f"**Range:** {result.min} ~ {result.max}"

        container = discord.ui.Container[MultiDistributionView](accent_color=color)
        button_row = discord.ui.ActionRow[MultiDistributionView]()
        for dist in result.distributions:
            button_row.add_item(MultiDistributionButton(dist.expression, result.advantage))

        image = discord.ui.MediaGallery["MultiDistributionView"]()
        image.add_item(media=self.chart)

        container.add_item(discord.ui.TextDisplay(title))
        container.add_item(discord.ui.TextDisplay(range_text))
        container.add_item(button_row)
        container.add_item(image)
        self.add_item(container)
