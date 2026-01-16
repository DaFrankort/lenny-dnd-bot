import random

import discord

from logic.charts import get_radar_chart


class Stats:
    """Class for rolling character-stats in D&D 5e."""

    stats: list[tuple[list[int], int]]

    def __init__(self, min_total: int = -1) -> None:
        for _ in range(256):
            self.stats = [self.roll_stat() for _ in range(6)]
            if self.total >= min_total:
                return
        raise ValueError(
            f"Could not generate stats with a minimum total of {min_total}.\n"
            f"Try again or use a more reasonable ``min_total``."
        )

    def roll_stat(self) -> tuple[list[int], int]:
        """Rolls a single stat in D&D 5e."""
        rolls = [random.randint(1, 6) for _ in range(4)]
        rolls = sorted(rolls)
        result = sum(rolls[1:])
        return rolls, result

    @property
    def total(self) -> int:
        return sum(result for _, result in self.stats)

    def get_radar_chart(self, color: int = discord.Color.dark_green().value) -> discord.File:
        values = [value for _, value in self.stats]
        return get_radar_chart(values=values, color=color)
