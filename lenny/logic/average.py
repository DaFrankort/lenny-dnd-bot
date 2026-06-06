import dataclasses
import io
import re
from abc import ABC, abstractmethod
from collections.abc import Callable

import discord
import matplotlib.pyplot as plt

from logic.distribution import dice_distribution
from logic.dnd.abstract import build_table_from_rows
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


def _calculate_hit_chances(
    hit: str, ac: int, advantage: Advantage, crit_min: int, ignore_crit: bool
) -> tuple[float, float, float]:
    d20_hit = dice_distribution("1d20", advantage)
    hit_bonus = dice_distribution(hit)

    # Calculate the hit chances
    crit_miss_values: set[int] = set([1])  # Always crit fail on a 1
    crit_hit_values: set[int] = set(range(crit_min, 21))
    if ignore_crit:
        crit_miss_values = set()
        crit_hit_values = set()
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

    miss_chance = normal_miss_chance + crit_miss_chance
    assert abs(normal_hit_chance + miss_chance + crit_hit_chance - 1) < 1e-6
    return normal_hit_chance, miss_chance, crit_hit_chance


def _average_damage_per_attack(
    hit: str,
    damage: str,
    ac: int,
    advantage: Advantage,
    crit_min: int,
    miss_damage_expr: str = "0",
    ignore_crit: bool = False,
) -> AverageDamageResult:
    hit_chance, miss_chance, crit_chance = _calculate_hit_chances(hit, ac, advantage, crit_min, ignore_crit)

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


class AverageDamageResultsBase(ABC):
    """Base class to handle data calculation and chart generation."""

    x_values: list[int]
    advantages: list[Advantage]
    data: dict[tuple[int, Advantage], float]

    chart: discord.File
    table: str

    damage: str
    miss_damage: str

    def __init__(
        self,
        x_values: list[int],
        damage: str,
        miss_damage: str,
        title: str,
        xlabel: str,
        ylabel: str,
        calc_func: Callable[[int, Advantage], AverageDamageResult],
    ):
        self.x_values = x_values
        self.advantages = Advantage.values()
        self.damage = damage.strip().replace(" ", "").lower()
        self.miss_damage = miss_damage.strip().replace(" ", "").lower()
        self.data = {}

        for x in self.x_values:
            for adv in self.advantages:
                self.data[(x, adv)] = calc_func(x, adv).avg_damage

        self.chart = self.generate_chart(title, xlabel, ylabel)
        self.table = self.generate_table()

    def get(self, x: int, adv: Advantage) -> str:
        return f"{self.data.get((x, adv), 0.0):.2f}"

    def generate_chart(self, title: str, xlabel: str, ylabel: str) -> discord.File:
        plt.style.use("dark_background")  # Looks better in Discord
        plt.figure(figsize=(10, 6))  # type: ignore

        for adv in self.advantages:
            y_values = [float(self.get(x, adv)) for x in self.x_values]
            plt.plot(self.x_values, y_values, label=adv, marker="o", markersize=4)  # type: ignore

        plt.title(title)  # type: ignore
        plt.xlabel(xlabel)  # type: ignore
        plt.ylabel(ylabel)  # type: ignore
        plt.grid(True, linestyle="--", alpha=0.6)  # type: ignore
        plt.legend(title="Advantage Type")  # type: ignore
        plt.xticks(self.x_values)  # type: ignore

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")  # type: ignore
        plt.close()
        buffer.seek(0)

        return discord.File(fp=buffer, filename="average_chart.png")

    def generate_table(self) -> str:
        headers = [self.label, *[str(adv).capitalize() for adv in self.advantages]]
        rows = [(str(x), *[self.get(x, adv) for adv in self.advantages]) for x in self.x_values]
        return build_table_from_rows(headers, rows, align_right=True)

    @property
    @abstractmethod
    def label(self) -> str:
        """The column-header for the X-axis values in the table"""

    @property
    @abstractmethod
    def title(self) -> str:
        """The embed-title shown to users"""

    @property
    @abstractmethod
    def details(self) -> str:
        """The formatted string showing the input of the user."""


class AverageDamageACResults(AverageDamageResultsBase):
    hit_expr: str
    crit_min: int

    def __init__(
        self,
        hit: str,
        damage: str,
        min_ac: int,
        max_ac: int,
        crit_min: int,
        miss_damage: str,
    ) -> None:
        self.hit_expr = f"1d20+{hit}" if not hit.startswith("-") else f"1d20{hit}"
        self.crit_min = crit_min
        acs = list(range(min(min_ac, max_ac), max(min_ac, max_ac) + 1))

        super().__init__(
            x_values=acs,
            damage=damage,
            miss_damage=miss_damage,
            title="Average Damage vs Armor Class",
            xlabel="Armor Class (AC)",
            ylabel=f"Avg. Damage ({self.hit_expr} -> {damage})",
            calc_func=lambda ac, adv: _average_damage_per_attack(hit, damage, ac, adv, crit_min, miss_damage),
        )

    @property
    def label(self) -> str:
        return "AC"

    @property
    def title(self) -> str:
        return "Average Damage per Attack"

    @property
    def details(self) -> str:
        details = f"**Hit**: {self.hit_expr}"
        details += f"\n**Damage**: {self.damage}"
        if self.miss_damage != "0":
            details += f"\n**Miss damage:** {self.miss_damage}"
        if self.crit_min < 20:
            details += f"\n**Critical range:** {self.crit_min}-20"
        return details


class AverageDamageDCResults(AverageDamageResultsBase):
    dc: int

    def __init__(
        self,
        dc: int,
        damage: str,
        miss_damage: str,
        min_mod: int,
        max_mod: int,
    ) -> None:
        self.dc = dc
        mods = list(range(min(min_mod, max_mod), max(min_mod, max_mod) + 1))

        super().__init__(
            x_values=mods,
            damage=damage,
            miss_damage=miss_damage,
            title=f"Average Damage using DC {self.dc}",
            xlabel="Saving Throw Modifier (1d20+x)",
            ylabel=f"Avg. Damage ({damage} or {miss_damage})",
            calc_func=lambda mod, adv: _average_damage_per_attack(
                str(mod), miss_damage, dc, adv, 20, damage, True
            ),  # Swap damage/miss_damage and use ignore_crit for Save DCs
        )

    @property
    def label(self) -> str:
        return "Mod"

    @property
    def title(self):
        return "Average Damage based on your DC"

    @property
    def details(self) -> str:
        details = f"**DC:** {self.dc}"
        details += f"\n**Damage:** {self.damage}"
        details += f"\n**Miss damage:** {self.miss_damage}"
        return details
