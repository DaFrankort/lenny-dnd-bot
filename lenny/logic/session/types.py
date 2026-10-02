from dataclasses import dataclass

import discord
from d100 import Critical
from d100.ast.die import Die

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
    adv_count: int
    dis_count: int

    rolled_d20_totals: list[int]
    resolved_d20_totals: list[int]
    dmg_expressions: dict[str, list[int]]
    rolled_dice: dict[int, int]

    def __init__(self):
        self.nat20_count = 0
        self.nat1_count = 0
        self.dirty20_count = 0
        self.adv_count = 0
        self.dis_count = 0

        self.rolled_d20_totals = []
        self.resolved_d20_totals = []
        self.dmg_expressions = {}
        self.rolled_dice = {}

    def add(self, result: RollResult | MultiRollResult):
        if isinstance(result, MultiRollResult):
            warnings = result.warnings
            all_rolls = [*result.rolls, *result.rolls_lose_1, *result.rolls_lose_2]
            resolved_rolls = result.rolls
            count = len(result.rolls)
        else:
            warnings = result.result.warnings
            all_rolls = result.result.rolls
            resolved_roll = next((roll for roll in all_rolls if roll.total == result.result.total), None)
            resolved_rolls = [resolved_roll] if resolved_roll else []
            count = 1

        if len(warnings) > 0:
            # Rolls with warnings are not considered valid dice-rolls.
            # But often appear when users want to quickly calculate something.
            return

        self._add_dice_count(all_rolls)
        self._add_advantage(result.expression, result.advantage, count)

        resolved_roll_ids = {id(roll) for roll in resolved_rolls}
        for roll in all_rolls:
            if "d100" in result.expression or "d%" in result.expression:
                return  # We don't want to track d100's, they're not used for skill-checks or damage.

            if "d20" in result.expression:
                self._add_d20(roll, resolved=id(roll) in resolved_roll_ids)
            elif not isinstance(result, MultiRollResult) or id(roll) in resolved_roll_ids:
                self._add_damage_roll(roll)

    def _add_dice_count(self, rolls: list[SingleRollResult]):
        def add_die(node: Die):
            size = node.size if node.size != "%" else 100  # % die is the same as a d100.
            if size not in self.rolled_dice:
                self.rolled_dice[size] = 0
            self.rolled_dice[size] += 1

        for roll in rolls:
            for die in roll.roll.extract_dice():
                add_die(die)

    def _add_d20(self, roll: SingleRollResult, resolved: bool):
        d20 = roll.ast.find_d20()
        if d20 is None:
            return

        value = roll.roll.find_from_ast(d20)
        if value is None:
            return

        self.rolled_d20_totals.append(value.total)
        if resolved:
            self.resolved_d20_totals.append(value.total)

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

    def _add_advantage(self, expression: str, advantage: Advantage, count: int = 1):
        if advantage is Advantage.ADVANTAGE or advantage is Advantage.ELVEN_ACCURACY:
            self.adv_count += count
            return
        if advantage is Advantage.DISADVANTAGE:
            self.dis_count += count
            return

        if "2d20kh1" in expression or "2d20dl1" in expression or "1d20adv" in expression:
            self.adv_count += count
        if "2d20kl1" in expression or "2d20dh1" in expression or "1d20dis" in expression:
            self.dis_count += count

    @property
    def average_rolled_d20(self) -> int:
        if len(self.rolled_d20_totals) == 0:
            return 0
        return sum(self.rolled_d20_totals) // len(self.rolled_d20_totals)

    @property
    def average_resolved_d20(self) -> int:
        if len(self.resolved_d20_totals) == 0:
            return 0
        return sum(self.resolved_d20_totals) // len(self.resolved_d20_totals)

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
    def total_dice_rolled(self) -> int:
        return sum(v for v in self.rolled_dice.values())

    @property
    def most_used_die_type(self) -> tuple[int, int]:
        most_used: tuple[int, int] = (-1, -1)
        for sides, uses in self.rolled_dice.items():
            if uses > most_used[1]:
                most_used = (sides, uses)
        return most_used

    @property
    def advantage_percentage(self) -> float:
        if len(self.resolved_d20_totals) == 0:
            return 0
        return self.adv_count / len(self.resolved_d20_totals)

    @property
    def disadvantage_percentage(self) -> float:
        if len(self.resolved_d20_totals) == 0:
            return 0
        return self.dis_count / len(self.resolved_d20_totals)


class UserSessionStats:
    dice: UserSessionDiceStats

    def __init__(self):
        self.dice = UserSessionDiceStats()
