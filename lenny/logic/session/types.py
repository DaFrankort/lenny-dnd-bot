from dataclasses import dataclass

import discord
from d100 import Critical

from logic.roll import Advantage, RollResult, SingleRollResult


@dataclass
class UserSessionResult:
    user: discord.Member
    color: discord.Color
    title: str
    description: str


@dataclass
class SessionResult:
    base_info: str
    users_stats: list[UserSessionResult]


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

    def add(self, result: RollResult):
        if len(result.result.warnings) > 0:
            # Rolls with warnings are not considered valid dice-rolls.
            # But often appear when users want to quickly calculate something.
            return

        self._add_advantage(result)
        for roll in result.result.rolls:
            # TODO -> maybe use different separation? Possibly 1d10red support?
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

    def _add_advantage(self, result: RollResult):
        if result.advantage is Advantage.ADVANTAGE or result.advantage is Advantage.ELVEN_ACCURACY:
            self.adv_count += 1
            return
        if result.advantage is Advantage.DISADVANTAGE:
            self.dis_count += 1
            return

        if "2d20kh1" in result.expression or "2d20dl1" in result.expression or "1d20adv" in result.expression:
            self.adv_count += 1
        if "2d20kl1" in result.expression or "2d20dh1" in result.expression or "1d20dis" in result.expression:
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
