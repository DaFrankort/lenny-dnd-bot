from discord import Interaction
from discord.app_commands import choices, describe

from commands.command import BaseCommand
from embeds.distribution import MultiDistributionEmbed, SingleDistributionEmbed
from logic.color import UserColor
from logic.distribution import DistributionChartStyle, distribution
from logic.roll import Advantage
from methods import call_with_timeout


class DistributionCommand(BaseCommand):
    name = "distribution"
    desc = "Show the probability distribution of an expression."
    help = "Generates an image of the distribution of an expression."

    @choices(
        advantage=Advantage.choices(),
        style=DistributionChartStyle.choices(),
    )
    @describe(
        expression="The dice-expression to visualize (Example: 1d8ro1). Multiple distributions are supported if they are separated by commas (e.g. 1d8,2d4).",
        advantage="Whether to simulate a normal roll or the roll with advantage or disadvantage.",
        min_to_beat="Visualize the odds to roll above this value.",
        style="The chart style for multiple distributions.",
    )
    async def handle(
        self,
        itr: Interaction,
        expression: str,
        advantage: str = Advantage.NORMAL,
        min_to_beat: int | None = None,
        style: DistributionChartStyle = DistributionChartStyle.ADJACENT,
    ):
        timeout = 5  # seconds

        await itr.response.defer()
        color = UserColor.get(itr)
        result = call_with_timeout(
            timeout=timeout,
            func=distribution,
            args=[expression, Advantage(advantage), color, min_to_beat, style],
        )
        if result is None:
            raise TimeoutError("Distribution took too long to calculate! For more information, see `/help distribution`.")

        if len(result.distributions) == 1:
            embed = SingleDistributionEmbed(itr, result)
        else:
            embed = MultiDistributionEmbed(itr, result)

        await itr.followup.send(embed=embed, file=embed.chart)
