from discord import Interaction
from discord.app_commands import choices, describe

from commands.command import BaseCommand
from embeds.distribution import DistributionEmbed
from logic.color import UserColor
from logic.distribution import distribution
from logic.roll import Advantage
from methods import call_with_timeout


class DistributionCommand(BaseCommand):
    name = "distribution"
    desc = "Show the probability distribution of an expression."
    help = "Generates an image of the distribution of an expression."

    @choices(advantage=Advantage.choices())
    @describe(
        expression="The dice-expression to visualize (Example: 1d8ro1).",
        advantage="Whether to simulate a normal roll or the roll with advantage or disadvantage.",
        min_to_beat="Visualize the odds to roll above this value.",
    )
    async def handle(
        self,
        itr: Interaction,
        expression: str,
        advantage: str = Advantage.NORMAL,
        min_to_beat: int | None = None,
    ):
        timeout = 5  # seconds

        await itr.response.defer()
        color = UserColor.get(itr)
        result = call_with_timeout(
            timeout=timeout,
            func=distribution,
            args=[expression, Advantage(advantage), color, min_to_beat],
        )
        if result is None:
            raise TimeoutError("Distribution calculation took too long to finish!")

        embed = DistributionEmbed(itr, result)
        await itr.followup.send(embed=embed, file=embed.chart)
