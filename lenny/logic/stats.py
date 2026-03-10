import random

import discord

from logic.charts import get_radar_chart


def get_stat_mod(stat: int) -> str:
    mod = (stat - 10) // 2
    return str(mod) if mod < 0 else f"+{mod}"


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
    stats: dict[str, int]
    points: int
    max_points: int = 27
    owner_id: int

    def __init__(self, itr: discord.Interaction):
        self.points = self.max_points
        self.owner_id = itr.user.id
        self.stats = {"STR": 8, "DEX": 8, "CON": 8, "INT": 8, "WIS": 8, "CHA": 8}

    @property
    def values(self) -> list[int]:
        return [val for _, val in self.stats.items()]  # Sorry about this, I forgot how to get the direct values

    def get_radar_chart(self, color: int = discord.Color.dark_green().value) -> discord.File:
        return get_radar_chart(values=self.values, labels=list(self.stats), color=color)

    def can_add(self, key: str) -> bool:
        if self.stats[key] >= 15:
            return False
        if self.points <= 0:
            return False
        if self.stats[key] >= 13 and self.points < 2:  # 14 & 15 cost 2 points
            return False
        return True

    def can_take(self, key: str) -> bool:
        if self.points >= self.max_points:
            return False
        return self.stats[key] > 8

    def add_score(self, key: str):
        if not self.can_add(key):
            return

        self.points -= 1
        self.stats[key] += 1
        if self.stats[key] >= 14:  # 14 & 15 cost 2 points
            self.points -= 1

    def take_score(self, key: str):
        if not self.can_take(key):
            return

        if self.stats[key] >= 14:  # 14 & 15 cost 2 points
            self.points += 1
        self.points += 1
        self.stats[key] -= 1

    def is_owner(self, user: discord.User | discord.Member):
        return self.owner_id == user.id
