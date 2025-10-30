import random
import discord
from logic.charts import get_radar_chart


class Stats:
    """Class for rolling character-stats in D&D 5e."""

    stats: list[tuple[list[int], int]]

    def __init__(self) -> None:
        self.stats = [self.roll_stat() for _ in range(6)]

    def roll_stat(self) -> tuple[list[int], int]:
        """Rolls a single stat in D&D 5e."""
        rolls = [random.randint(1, 6) for _ in range(4)]
        rolls = sorted(rolls)
        result = sum(rolls[1:])
        return rolls, result

    @property
    def total(self) -> int:
        return sum([result for _, result in self.stats])

    def get_radar_chart(self, color: discord.Color = discord.Color.dark_green()) -> discord.File:
        results = [result for _, result in self.stats]
        return get_radar_chart(results=results, color=int(color))
