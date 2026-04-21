from discord import Interaction

from commands.command import BaseCommand
from logic.average import AverageDamageResults
from logic.dnd.abstract import build_table_from_rows


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

        acs = results.acs
        advantages = results.advantages

        headers = ["AC", *[str(adv).capitalize() for adv in advantages]]
        rows = [(str(ac), *[results.get(ac, adv) for adv in advantages]) for ac in acs]

        table = build_table_from_rows(headers, rows, align_right=True)

        # TODO add a nice embed
        await itr.response.send_message(table)
