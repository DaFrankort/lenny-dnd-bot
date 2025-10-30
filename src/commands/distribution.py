from discord import Interaction, app_commands

from embeds.distribution import DistributionEmbed
from command import SimpleCommand
from logic.distribution import distribution
from logic.color import UserColor
from logic.roll import Advantage


class DistributionCommand(SimpleCommand):
    name = "distribution"
    desc = "Show the probability distribution of an expression."
    help = "Generates an image of the distribution of an expression."

    @app_commands.choices(advantage=Advantage.choices())
    async def callback(
        self,
        itr: Interaction,
        expression: str,
        advantage: str = Advantage.Normal.value,
        min_to_beat: int | None = None,
    ):
        self.log(itr)
        await itr.response.defer()
        color = UserColor.get(itr)
        result = distribution(expression, advantage, color, min_to_beat)
        embed = DistributionEmbed(itr, result)
        await itr.followup.send(embed=embed, file=embed.chart)
