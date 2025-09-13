from discord import Interaction, app_commands

from embeds.distribution import DistributionEmbed
from logic.app_commands import SimpleCommand
from dice import DiceRollMode
from logic.distribution import distribution
from user_colors import UserColor


DISTRIBUTION_COMMAND_ADVANTAGE_CHOICES = [
    app_commands.Choice(
        name=DiceRollMode.Advantage.value,
        value=DiceRollMode.Advantage.value,
    ),
    app_commands.Choice(
        name=DiceRollMode.Disadvantage.value,
        value=DiceRollMode.Disadvantage.value,
    ),
    app_commands.Choice(
        name=DiceRollMode.Normal.value,
        value=DiceRollMode.Normal.value,
    ),
]


class DistributionCommand(SimpleCommand):
    name = "distribution"
    desc = "Show the probability distribution of an expression."
    help = "Generates an image of the distribution of an expression."

    @app_commands.choices(advantage=DISTRIBUTION_COMMAND_ADVANTAGE_CHOICES)
    async def callback(
        self,
        itr: Interaction,
        expression: str,
        advantage: str = DiceRollMode.Normal.value,
        min_to_beat: int | None = None,
    ):
        self.log(itr)
        await itr.response.defer()
        color = UserColor.get(itr)
        result = distribution(expression, advantage, color, min_to_beat)
        embed = DistributionEmbed(itr, result)
        await itr.followup.send(embed=embed, file=embed.chart)
