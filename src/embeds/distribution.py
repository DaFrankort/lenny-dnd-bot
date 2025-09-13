import discord
from discord.utils import MISSING
from dice import DiceRollMode
from logic.distribution import DistributionResult
from user_colors import UserColor


class DistributionEmbed(discord.Embed):
    chart: discord.File

    def __init__(self, itr: discord.Interaction, result: DistributionResult):
        self.chart = result.chart or MISSING
        color = UserColor.get(itr)

        if result.error is not None:
            title = f"Error in '{result.expression}'!"
            desc = f"⚠️ {result.error}"
            super().__init__(color=color, title=title, description=desc)
            return

        if result.advantage == DiceRollMode.Advantage.value:
            title_suffix = " with advantage"
        elif result.advantage == DiceRollMode.Disadvantage.value:
            title_suffix = " with disadvantage"
        else:
            title_suffix = ""

        super().__init__(
            color=color,
            title=f"Distribution for {result.expression}{title_suffix}!",
            type="rich",
        )

        self.add_field(name="Mean", value=f"{result.mean:.2f}", inline=True)
        self.add_field(name="Stdev", value=f"{result.stdev:.2f}", inline=True)
        self.set_image(url=f"attachment://{self.chart.filename}")

        if result.min_to_beat is not None:
            min_to_beat, odds = result.min_to_beat
            self.add_field(
                name=f"Odds to beat {min_to_beat}",
                value=f"{100*odds:.2f}%",
                inline=True,
            )
