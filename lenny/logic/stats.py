import random

import discord

from logic.charts import get_radar_chart


class Stats:
    """Class for rolling character-stats in D&D 5e."""

    stats: list[tuple[list[int], int]]
    min_total: int
    roll_count: int

    def __init__(self, min_total: int = -1) -> None:
        self.min_total = min_total
        for i in range(256):
            self.stats = [self.roll_stat() for _ in range(6)]
            if self.total >= min_total:
                self.roll_count = i
                return
        raise TimeoutError(
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


class BoughtStats:
    stats: dict[str, int] = {"STR": 8, "DEX": 8, "CON": 8, "INT": 8, "WIS": 8, "CHA": 8}
    max_points: int

    def __init__(self):
        self.max_points = 27

    @property
    def spent(self) -> int:
        return sum(self.values) - (8 * 6)

    @property
    def points_left(self) -> int:
        return self.max_points - self.spent

    @property
    def values(self) -> list[int]:
        return [self.stats[key] for key in self.stats]  # Sorry about this, I forgot how to get the direct values

    def get_radar_chart(self, color: int = discord.Color.dark_green().value) -> discord.File:
        return get_radar_chart(values=self.values, color=color)
