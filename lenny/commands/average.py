from discord import Interaction
from discord.app_commands import Range, describe

from commands.command import BaseCommand
from embeds.average import AverageDamageLayoutView
from logic.average import AverageDamageResults


class AverageDamageCommand(BaseCommand):
    name = "average"
    desc = "Calculate the average damage of an attack!"
    help = "Calculates the average damage of an attack against various armor classes, taking critical hits and critical misses into account."

    @describe(
        hit="Your hit modifier on your attack roll, (e.g. '8', '4+1d4').",
        damage="Your damage expression on a hit (e.g. '1d8+3', '8d6')",
        min_ac="The minimum AC to compare against, default = 8.",
        max_ac="The maximum AC to compare against, default = 30.",
        crit_min="The minimum roll required on the d20 to land a critical hit, default = 20",
        miss_damage="The damage rolled on a miss, default = 0.",
    )
    async def handle(
        self,
        itr: Interaction,
        hit: str,
        damage: str,
        min_ac: Range[int, 0, 30] = 8,
        max_ac: Range[int, 0, 30] = 30,
        crit_min: Range[int, 0, 20] = 20,
        miss_damage: str = "0",
    ) -> None:
        results = AverageDamageResults(hit, damage, min_ac, max_ac, crit_min, miss_damage)
        view = AverageDamageLayoutView(itr, results)
        await itr.response.send_message(view=view, file=results.chart)
