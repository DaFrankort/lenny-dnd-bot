import discord
import discord.app_commands
from discord import Interaction, app_commands

from charts import get_distribution_chart
from dice import DiceRollMode
from distribution import DiceDistributionEmbed, get_distribution
from embeds import SimpleEmbed
from i18n import t
from logger import log_cmd


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


class DistributionCommand(discord.app_commands.Command):
    name = t("commands.distribution.name")
    description = t("commands.distribution.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    @app_commands.choices(advantage=DISTRIBUTION_COMMAND_ADVANTAGE_CHOICES)
    async def callback(
        self,
        itr: Interaction,
        expression: str,
        advantage: str = DiceRollMode.Normal.value,
        min_to_beat: int | None = None,
    ):
        log_cmd(itr)
        await itr.response.defer()
        try:
            distribution = get_distribution(expression, advantage=advantage)
            chart = get_distribution_chart(itr, distribution, min_to_beat or -9999999)
            embed = DiceDistributionEmbed(
                itr, expression, distribution, advantage, min_to_beat
            )
            embed.set_image(url=f"attachment://{chart.filename}")
            await itr.followup.send(embed=embed, file=chart)
        except Exception as e:
            title = f"Error in {expression}!"
            desc = f"⚠️ {str(e)}"
            await itr.followup.send(embed=SimpleEmbed(title=title, description=desc))
