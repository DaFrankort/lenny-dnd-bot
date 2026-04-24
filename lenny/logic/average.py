import dataclasses
import io
import re

import discord
import matplotlib.pyplot as plt

from logic.distribution import dice_distribution
from logic.roll import Advantage


@dataclasses.dataclass
class AverageDamageResult:
    hit: str
    damage: str
    ac: int
    advantage: Advantage

    hit_chance: float
    miss_chance: float
    crit_chance: float

    hit_avg_damage: float
    miss_avg_damage: float
    crit_avg_damage: float

    avg_damage: float


def double_dice_in_expression(expression: str) -> str:
    """Doubles the dice-count of a dice-expression, e.g. 1d6+5 -> 2d6+5"""

    def double(match: re.Match[str]):
        count = int(match.group(1))
        return f"{count * 2}d{match.group(2)}"

    return re.sub(r"(\d+)d(\d+)", double, expression)


def _average_damage_per_attack(
    hit: str,
    damage: str,
    ac: int,
    advantage: Advantage,
    crit_min: int,
    miss_damage_expr: str = "0",
) -> AverageDamageResult:
    d20_hit = dice_distribution("1d20", advantage)
    hit_bonus = dice_distribution(hit)

    # Calculate the hit chances
    crit_miss_values = set([1])  # Always crit fail on a 1
    crit_hit_values = set(range(crit_min, 21))
    other_roll_values = set(range(1, 21)) - crit_miss_values - crit_hit_values

    crit_miss_chance = sum(d20_hit.get(r) for r in crit_miss_values)
    crit_hit_chance = sum(d20_hit.get(r) for r in crit_hit_values)

    normal_hit_chance = 0
    normal_miss_chance = 0

    for value in other_roll_values:
        for bonus in hit_bonus.keys():
            odds = d20_hit.get(value) * hit_bonus.get(bonus)
            total = value + bonus
            if total >= ac:
                normal_hit_chance += odds
            else:
                normal_miss_chance += odds

    hit_chance = normal_hit_chance
    miss_chance = normal_miss_chance + crit_miss_chance
    crit_chance = crit_hit_chance

    # Ensure hit, miss, and crit have a 100% total chance
    assert abs(hit_chance + miss_chance + crit_chance - 1) < 1e-6

    hit_damage = dice_distribution(damage)
    miss_damage = dice_distribution(miss_damage_expr)
    crit_damage = dice_distribution(double_dice_in_expression(damage))

    hit_avg = hit_damage.mean()
    miss_avg = miss_damage.mean()
    crit_avg = crit_damage.mean()

    avg = (hit_chance * hit_avg) + (miss_chance * miss_avg) + (crit_chance * crit_avg)

    return AverageDamageResult(
        hit=hit,
        damage=damage,
        ac=ac,
        advantage=advantage,
        hit_chance=hit_chance,
        miss_chance=miss_chance,
        crit_chance=crit_chance,
        hit_avg_damage=hit_avg,
        miss_avg_damage=miss_avg,
        crit_avg_damage=crit_avg,
        avg_damage=avg,
    )


class AverageDamageResults:
    acs: list[int]
    advantages: list[Advantage]
    data: dict[tuple[int, Advantage], str]
    chart: discord.File
    hit: str
    damage: str
    crit_min: int
    miss_damage: str

    def __init__(
        self,
        hit: str,
        damage: str,
        min_ac: int,
        max_ac: int,
        crit_min: int,
        miss_damage: str,
    ) -> None:
        if min_ac > max_ac:
            min_ac, max_ac = max_ac, min_ac

        self.acs = list(range(min_ac, max_ac + 1))
        self.advantages = Advantage.values()
        self.data = {}

        self.hit = hit.strip().replace(" ", "").lower()
        self.hit = f"1d20+{hit}" if not hit.startswith("-") else f"1d20{hit}"
        self.damage = damage.strip().replace(" ", "").lower()
        self.crit_min = crit_min
        self.miss_damage = miss_damage.strip().replace(" ", "").lower()

        for ac in self.acs:
            for advantage in self.advantages:
                result = _average_damage_per_attack(hit, damage, ac, advantage, crit_min, miss_damage)
                self.data[(ac, advantage)] = f"{result.avg_damage:.2f}"

        self.chart = self.generate_chart()

    def get(self, ac: int, advantage: Advantage) -> str:
        if (ac, advantage) in self.data:
            return self.data[(ac, advantage)]
        return "0.00"

    def generate_chart(self) -> discord.File:
        plt.style.use("dark_background")  # Looks better in Discord
        plt.figure(figsize=(10, 6))  # type: ignore

        for adv in self.advantages:
            y_values = [float(self.get(ac, adv)) for ac in self.acs]
            plt.plot(self.acs, y_values, label=adv, marker="o", markersize=4)  # type: ignore

        plt.title("Average Damage vs Armor Class")  # type: ignore
        plt.xlabel("Armor Class (AC)")  # type: ignore
        plt.ylabel(f"Avg. Damage ({self.hit} -> {self.damage})")  # type: ignore
        plt.grid(True, linestyle="--", alpha=0.6)  # type: ignore
        plt.legend(title="Advantage Type")  # type: ignore

        plt.xticks(self.acs)  # type: ignore

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")  # type: ignore
        plt.close()
        buffer.seek(0)

        return discord.File(fp=buffer, filename="damage_chart.png")
