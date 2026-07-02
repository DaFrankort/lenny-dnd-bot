from dataclasses import dataclass

import discord
from d100 import Critical

from logic.roll import Advantage, MultiRollResult, RollResult, SingleRollResult


@dataclass
class UserSessionResult:
    user: discord.Member
    color: discord.Color
    title: str
    description: str
    graph: discord.File | None


@dataclass
class SessionResult:
    base_info: str
    users_stats: list[UserSessionResult]

    def files(self) -> list[discord.File]:
        return [stats.graph for stats in self.users_stats if stats.graph]


class UserSessionDiceStats:
    nat20_count: int
    nat1_count: int
    dirty20_count: int
    d20_totals: list[int]

    dmg_expressions: dict[str, list[int]]

    adv_count: int
    dis_count: int

    def __init__(self):
        self.nat20_count = 0
        self.nat1_count = 0
        self.dirty20_count = 0
        self.d20_totals = []

        self.dmg_expressions = {}

        self.adv_count = 0
        self.dis_count = 0

    def add(self, result: RollResult | MultiRollResult):
        if isinstance(result, MultiRollResult):
            warnings = result.warnings
            rolls = result.rolls
        else:
            warnings = result.result.warnings
            rolls = result.result.rolls

        if len(warnings) > 0:
            # Rolls with warnings are not considered valid dice-rolls.
            # But often appear when users want to quickly calculate something.
            return

        if "d100" in result.expression:
            return  # We don't want to track d100's, they're not used for skill-checks or damage.

        self._add_advantage(result.expression, result.advantage)

        for roll in rolls:
            if "d20" in result.expression:
                self._add_d20(roll)
            else:
                self._add_damage_roll(roll)

    def _add_d20(self, roll: SingleRollResult):
        self.d20_totals.append(roll.total)
        if roll.crit is Critical.CRIT:
            self.nat20_count += 1
        elif roll.crit is Critical.FAIL:
            self.nat1_count += 1
        elif roll.crit is Critical.DIRTY:
            self.dirty20_count += 1

    def _add_damage_roll(self, roll: SingleRollResult):
        if roll.expr not in self.dmg_expressions:
            self.dmg_expressions[roll.expr] = []
        self.dmg_expressions[roll.expr].append(roll.total)

    def _add_advantage(self, expression: str, advantage: Advantage):
        if advantage is Advantage.ADVANTAGE or advantage is Advantage.ELVEN_ACCURACY:
            self.adv_count += 1
            return
        if advantage is Advantage.DISADVANTAGE:
            self.dis_count += 1
            return

        if "2d20kh1" in expression or "2d20dl1" in expression or "1d20adv" in expression:
            self.adv_count += 1
        if "2d20kl1" in expression or "2d20dh1" in expression or "1d20dis" in expression:
            self.dis_count += 1

    @property
    def average_d20(self) -> int:
        if len(self.d20_totals) == 0:
            return 0
        return sum(self.d20_totals) // len(self.d20_totals)

    @property
    def damage_totals(self) -> list[int]:
        values: list[int] = []
        for _, totals in self.dmg_expressions.items():
            values.extend(totals)
        return values

    @property
    def average_dmg(self) -> int:
        totals = self.damage_totals
        if len(totals) == 0:
            return 0
        return sum(totals) // len(totals)

    @property
    def dice_rolled(self) -> int:
        return len(self.d20_totals) + len(self.dmg_expressions)


class UserSessionStats:
    dice: UserSessionDiceStats

    def __init__(self):
        self.dice = UserSessionDiceStats()
