from discord import Interaction

from commands.command import BaseCommand
from embeds.average import AverageDamageEmbed
from logic.average import AverageDamageResults


class AverageDamageCommand(BaseCommand):
    name = "average"
    desc = "Calculate the average damage of an attack!"
    help = "Calculates the average damage of an attack against various armor classes, taking critical hits and critical misses into account."

    async def handle(
        self,
        itr: Interaction,
        hit: str,
        damage: str,
        min_ac: int = 8,
        max_ac: int = 30,
        crit_min: int = 20,
        miss_damage: str = "0",
    ) -> None:
        results = AverageDamageResults(hit, damage, min_ac, max_ac, crit_min, miss_damage)
        embed = AverageDamageEmbed(itr, results)
        await itr.response.send_message(embed=embed)
