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


POINT_BUY_COST = {
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 7,
    15: 9,
}


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
        return list(self.stats.values())

    def get_radar_chart(self, color: int = discord.Color.dark_green().value) -> discord.File:
        return get_radar_chart(values=self.values, labels=list(self.stats), color=color)

    def _cost_between(self, old: int, new: int) -> int:
        return POINT_BUY_COST[new] - POINT_BUY_COST[old]

    def can_add(self, key: str) -> bool:
        current = self.stats[key]
        if current >= 15:
            return False
        new = current + 1
        cost = self._cost_between(current, new)

        return self.points >= cost

    def can_take(self, key: str) -> bool:
        current = self.stats[key]
        if current <= 8:
            return False

        refund = -self._cost_between(current, current - 1)
        return (self.points + refund) <= self.max_points

    def add_score(self, key: str):
        if not self.can_add(key):
            return

        current = self.stats[key]
        new = current + 1
        cost = self._cost_between(current, new)

        self.points -= cost
        self.stats[key] = new

    def take_score(self, key: str):
        if not self.can_take(key):
            return

        current = self.stats[key]
        new = current - 1
        refund = -self._cost_between(current, new)

        self.points += refund
        self.stats[key] = new

    def viable_scores(self, key: str) -> list[int]:
        """All scores the user could set this stat to."""
        current = self.stats[key]
        current_cost = POINT_BUY_COST[current]

        valid: list[int] = []
        for score in range(8, 16):
            diff = POINT_BUY_COST[score] - current_cost
            if diff <= self.points:
                valid.append(score)
        return valid

    def is_owner(self, user: discord.User | discord.Member):
        return self.owner_id == user.id
