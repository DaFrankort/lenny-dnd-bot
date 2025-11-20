import dataclasses
from enum import Enum
from typing import Any

# The usage of d20 requires many type: ignore comments, as d20 does not use any form of typing internally
import d20  # type: ignore

from methods import ChoicedEnum


class Advantage(str, ChoicedEnum):
    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"

    @property
    def title_suffix(self) -> str:
        suffixes = {self.ADVANTAGE: " with advantage", self.DISADVANTAGE: " with disadvantage"}
        return suffixes.get(self, "")


class DiceSpecial(str, Enum):
    NATURAL20 = "nat20"
    NATURAL1 = "nat1"
    DIRTY20 = "dirty20"


class DiceStringifier(d20.Stringifier):
    def _stringify(self, node: d20.expression.Number | Any) -> str:
        if not node.kept:  # type: ignore
            return ""
        return super()._stringify(node)  # type: ignore

    def _extract_values(self, values: Any) -> list[str]:
        results: list[str] = []
        for result in [self._stringify(value) for value in values]:
            if result:
                results.append(result)
        return results

    def _str_expression(self, node: d20.expression.Expression):
        return self._stringify(node.roll)  # type: ignore

    def _str_literal(self, node: d20.expression.Literal):
        # See d20 stringifiers.py:122 SimpleStringifier
        # A literal can have multiple values, and the last value in the list is the final value
        return str(node.values[-1])  # type: ignore

    def _str_unop(self, node: d20.expression.UnOp):
        return f"{node.op}{self._stringify(node.value)}"  # type: ignore

    def _str_binop(self, node: d20.expression.BinOp):
        return f"{self._stringify(node.left)} {node.op} {self._stringify(node.right)}"  # type: ignore

    def _str_parenthetical(self, node: d20.expression.Parenthetical):
        return f"({self._stringify(node.value)}){self._str_ops(node.operations)}"  # type: ignore

    def _str_set(self, node: d20.expression.Set):
        values = self._extract_values(node.values)  # type: ignore
        return "{" + ",".join(values) + "}"

    def _str_dice(self, node: d20.expression.Dice):
        values = self._extract_values(node.values)  # type: ignore
        return "[" + ",".join(values) + "]"

    def _str_die(self, node: d20.expression.Die):
        values = self._extract_values(node.values)  # type: ignore
        return ",".join(values)


def _is_only_dice_modifiers_and_additions(node: d20.Number | None) -> bool:
    if node is None:
        return False
    if isinstance(node, (d20.Literal, d20.Dice, d20.Die)):
        return True
    if isinstance(node, (d20.Parenthetical, d20.UnOp)):
        return _is_only_dice_modifiers_and_additions(node.children[0])  # type: ignore
    if isinstance(node, d20.BinOp):
        additions = set(["+", "-"])
        return (
            node.op in additions  # type: ignore
            and _is_only_dice_modifiers_and_additions(node.left)  # type: ignore
            and _is_only_dice_modifiers_and_additions(node.right)  # type: ignore
        )
    if isinstance(node, d20.Expression):
        return _is_only_dice_modifiers_and_additions(node.roll)  # type: ignore

    raise NotImplementedError(f"Unsupported type '{type(node)}'")


def _extract_dice(node: d20.Number | None) -> list[d20.Dice | d20.Die]:
    if node is None or isinstance(node, d20.Literal):
        return []
    if isinstance(node, (d20.Die, d20.Dice)):
        return node.keptset  # type: ignore
    if isinstance(node, d20.Parenthetical):
        return _extract_dice(node.children[0])  # type: ignore
    if isinstance(node, d20.UnOp):
        return _extract_dice(node.children[0])  # type: ignore
    if isinstance(node, d20.BinOp):
        return _extract_dice(node.left) + _extract_dice(node.right)  # type: ignore
    if isinstance(node, d20.Expression):
        return _extract_dice(node.roll)  # type: ignore

    raise NotImplementedError(f"Unsupported type '{type(node)}'")


def _contains_dice(node: d20.Number) -> bool:
    return len(_extract_dice(node)) > 0


def _has_comparison_result(expr: d20.Expression) -> bool:
    if not isinstance(expr.roll, d20.BinOp):  # type: ignore
        return False
    return expr.roll.op in {">", "<", ">=", "<=", "==", "!="}  # type: ignore


def _is_d20(dice: d20.Die | d20.Dice | Any) -> bool:
    if isinstance(dice, d20.Die):
        return dice.size == 20  # type: ignore
    if isinstance(dice, d20.Dice):
        return dice.num == 1 and dice.size == 20  # type: ignore
    return False


def _is_natural_20(node: d20.Number) -> bool:
    if not _is_only_dice_modifiers_and_additions(node):
        return False

    dice = _extract_dice(node)
    if len(dice) != 1:
        return False

    return _is_d20(dice[0]) and dice[0].total == 20  # type: ignore


def _is_natural_1(node: d20.Number) -> bool:
    if not _is_only_dice_modifiers_and_additions(node):
        return False

    dice = _extract_dice(node)
    if len(dice) != 1:
        return False
    return _is_d20(dice[0]) and dice[0].total == 1  # type: ignore


def _is_dirty_20(node: d20.Number) -> bool:
    if not _is_only_dice_modifiers_and_additions(node):
        return False

    dice = _extract_dice(node)
    if len(dice) != 1:
        return False
    return _is_d20(dice[0]) and node.total == 20  # type: ignore


@dataclasses.dataclass
class SingleRollResult:
    expression: str
    total: int
    special: DiceSpecial | None
    contains_dice: bool
    has_comparison_result: bool

    @property
    def is_natural_twenty(self) -> bool:
        return self.special == DiceSpecial.NATURAL20

    @property
    def is_natural_one(self) -> bool:
        return self.special == DiceSpecial.NATURAL1

    @property
    def is_dirty_twenty(self) -> bool:
        return self.special == DiceSpecial.DIRTY20


@dataclasses.dataclass
class RollResult:
    expression: str
    advantage: Advantage
    rolls: list[SingleRollResult]

    @property
    def roll(self) -> SingleRollResult:
        totals = [roll.total for roll in self.rolls]
        match self.advantage:
            case Advantage.ADVANTAGE:
                total = max(totals)
            case Advantage.DISADVANTAGE:
                total = min(totals)
            case _:
                total = sum(totals)

        for r in self.rolls:
            if r.total == total:
                return r

        # Fallback: return the last result
        return self.rolls[-1]


@dataclasses.dataclass
class MultiRollResult:
    expression: str
    advantage: Advantage
    rolls: list[SingleRollResult]
    rolls_lose: list[SingleRollResult]

    @property
    def total(self) -> int:
        return sum(r.total for r in self.rolls)


def _roll_single(expression: str) -> SingleRollResult:
    result = d20.roll(expression, stringifier=DiceStringifier())

    special = None
    if _is_natural_20(result.expr):
        special = DiceSpecial.NATURAL20
    elif _is_natural_1(result.expr):
        special = DiceSpecial.NATURAL1
    elif _is_dirty_20(result.expr):
        special = DiceSpecial.DIRTY20

    contains_dice = _contains_dice(result.expr)
    has_comparison_result = _has_comparison_result(result.expr)

    return SingleRollResult(str(result), result.total, special, contains_dice, has_comparison_result)


def _validate_expression(expression: str) -> None:
    # Roll an expression once, to check for errors
    try:
        expression = str(d20.parse(expression, allow_comments=False))
        _roll_single(expression)
    except d20.errors.RollSyntaxError as exception:
        raise ValueError(f"Expression '{expression}' has an invalid syntax!") from exception
    except d20.errors.TooManyRolls as exception:
        raise ValueError(f"Expression '{expression}' has too many dice rolls!") from exception
    except Exception as exception:
        raise exception


def roll(expression: str, advantage: Advantage = Advantage.NORMAL) -> RollResult:
    _validate_expression(expression)
    expression = str(d20.parse(expression, allow_comments=False))

    rolls: list[SingleRollResult] = []
    if advantage in [Advantage.ADVANTAGE, Advantage.DISADVANTAGE]:
        rolls.append(_roll_single(expression))
        rolls.append(_roll_single(expression))
    else:
        rolls.append(_roll_single(expression))

    return RollResult(expression, advantage, rolls)


def multi_roll(expression: str, amount: int, advantage: Advantage) -> MultiRollResult:
    _validate_expression(expression)
    expression = str(d20.parse(expression, allow_comments=False))
    rolls = [_roll_single(expression) for _ in range(amount)]

    if advantage == Advantage.NORMAL:
        return MultiRollResult(expression, advantage, rolls, rolls_lose=[])

    extra_rolls = [_roll_single(expression) for _ in range(amount)]
    lower_rolls: list[SingleRollResult] = []
    higher_rolls: list[SingleRollResult] = []

    for i in range(amount):
        if rolls[i].total > extra_rolls[i].total:
            higher_rolls.append(rolls[i])
            lower_rolls.append(extra_rolls[i])
        else:
            higher_rolls.append(extra_rolls[i])
            lower_rolls.append(rolls[i])

    if advantage == Advantage.ADVANTAGE:
        return MultiRollResult(expression, advantage, higher_rolls, rolls_lose=lower_rolls)
    return MultiRollResult(expression, advantage, lower_rolls, rolls_lose=higher_rolls)
