import discord
from user_colors import UserColor
import d20distribution
import d20distribution.distribution


def get_distribution(
    expression: str, advantage: str
) -> d20distribution.distribution.DiceDistribution:
    distribution = d20distribution.parse(expression)

    if advantage == "advantage":
        distribution = distribution.advantage()
    elif advantage == "disadvantage":
        distribution = distribution.disadvantage()

    return distribution


class DiceDistributionEmbed(discord.Embed):
    image: discord.File

    def __init__(
        self,
        itr: discord.Interaction,
        expression: str,
        distribution: d20distribution.distribution.DiceDistribution,
        advantage: str,
        min_to_beat: int | None,
    ):
        color = UserColor.get(itr)

        if advantage == "advantage":
            title_suffix = " with advantage!"
        elif advantage == "disadvantage":
            title_suffix = " with disadvantage!"
        else:
            title_suffix = "!"

        super().__init__(
            color=color,
            title=f"Distribution for {expression}{title_suffix}",
            type="rich",
        )

        self.add_field(name="Mean", value=f"{distribution.mean():.2f}", inline=True)
        self.add_field(name="Stdev", value=f"{distribution.stdev():.2f}", inline=True)

        if min_to_beat is not None:
            odds = 0
            for key in distribution.keys():
                if key >= min_to_beat:
                    odds += distribution.get(key)
            self.add_field(name=f"Odds to beat {min_to_beat}", value=f"{100*odds:.2f}%")
