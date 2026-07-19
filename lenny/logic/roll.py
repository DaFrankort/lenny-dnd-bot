import dataclasses

import d100
import d100.utils
from d100.ast.dice import Dice
from d100.ast.die import DiceSize, Die
from d100.ast.expression import ASTExpression, Expression
from d100.errors import RollError
from d100.roll import RollResult as D20RollResult
from d100.roll import SingleRollResult
from d100.stringifier import SimpleStringifier

from methods import ChoicedEnum


class Advantage(str, ChoicedEnum):
    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"
    ELVEN_ACCURACY = "elven accuracy"
    SAVAGE_ATTACKER = "savage attacker"

    @property
    def title_suffix(self) -> str:
        suffixes = {
            self.ADVANTAGE: " with advantage",
            self.DISADVANTAGE: " with disadvantage",
            self.ELVEN_ACCURACY: " with elven accuracy",
            self.SAVAGE_ATTACKER: " with savage attacker",
        }
        return suffixes.get(self, "")

    @property
    def rolls(self) -> int:
        match self:
            case Advantage.ADVANTAGE | Advantage.DISADVANTAGE | Advantage.SAVAGE_ATTACKER:
                return 2
            case Advantage.ELVEN_ACCURACY:
                return 3
            case Advantage.NORMAL:
                return 1


class DiceStringifier(SimpleStringifier):
    def _str_expression(self, node: Expression):
        return f"{self._stringify(node.value)}"

    def _str_dice(self, node: Dice):
        dice = list(self._str_die(die, node.size) for die in node.keptset)
        return "[" + ",".join(dice) + "]"

    def _str_die(self, die: Die, size: DiceSize) -> str:
        return str(die.value)


@dataclasses.dataclass
class RollResult:
    """Wrapper class around d100.roll.RollResult, to store additional information."""

    expression: str  # The original expression of the roll. May not match the d20 roll's expression if advantage was used.
    advantage: Advantage
    result: D20RollResult

    @property
    def total(self) -> int:
        return self.result.total


@dataclasses.dataclass
class MultiRollResult:
    expression: str
    advantage: Advantage
    rolls: list[SingleRollResult]
    rolls_lose_1: list[SingleRollResult]
    rolls_lose_2: list[SingleRollResult]  # A second losing roll column is added to account for Elven Accuracy
    warnings: list[str]

    @property
    def total(self) -> int:
        return sum(r.total for r in self.rolls)


def parse(expr: str, advantage: Advantage) -> tuple[ASTExpression, set[str]]:
    parsed = d100.parse(expr)
    warnings: set[str] = set()

    try:
        match advantage:
            case Advantage.NORMAL:
                ...
            case Advantage.ADVANTAGE:
                parsed = d100.utils.add_advantage_to_d20_in_expression(parsed, "adv", 2)
            case Advantage.ELVEN_ACCURACY:
                parsed = d100.utils.add_advantage_to_d20_in_expression(parsed, "adv", 3)
            case Advantage.DISADVANTAGE:
                parsed = d100.utils.add_advantage_to_d20_in_expression(parsed, "dis", 2)
            case Advantage.SAVAGE_ATTACKER:
                parsed = d100.parse(f"({expr})adv2")
            case _:
                raise RollError(f"Unknown advantage type: {advantage.value}")

    except RollError as exception:
        warnings.add(str(exception))

    return parsed, warnings


def _validate_expression(expr: str) -> D20RollResult:
    # Roll an expression once, to check for errors
    try:
        return d100.roll(expr)
    except d100.errors.RollSyntaxError as exception:
        raise SyntaxError(f"Expression '{expr}' has an invalid syntax!") from exception
    except d100.errors.TooManyRolls as exception:
        raise TimeoutError(f"Expression '{expr}' has too many dice rolls!") from exception
    except Exception as exception:
        raise exception


def clean_expression(expr: str) -> str:
    return str(d100.parse(expr))


def roll(expr: str, advantage: Advantage = Advantage.NORMAL) -> RollResult:
    cleaned = clean_expression(expr)
    parsed, warnings = parse(expr, advantage)

    stringifier = DiceStringifier()
    result = d100.roll(parsed, stringifier)
    result.warnings.extend(warnings)
    return RollResult(expression=cleaned, advantage=advantage, result=result)


def multi_roll(expr: str, amount: int, advantage: Advantage) -> MultiRollResult:
    cleaned = clean_expression(expr)
    parsed, parsing_warnings = parse(expr, advantage)
    stringifier = DiceStringifier()
    validation = _validate_expression(expr)
    warnings = [*validation.warnings, *parsing_warnings]

    rolls_win: list[SingleRollResult] = []
    rolls_lose_1: list[SingleRollResult] = []
    rolls_lose_2: list[SingleRollResult] = []

    for _ in range(amount):
        reverse = advantage == Advantage.DISADVANTAGE
        rolls = d100.roll(parsed, stringifier).rolls
        rolls = list(sorted(rolls, key=lambda r: r.total, reverse=reverse))

        rolls_win.append(rolls[-1])
        if len(rolls) >= 2:
            rolls_lose_1.append(rolls[0])
        if len(rolls) >= 3:
            rolls_lose_2.append(rolls[1])

    return MultiRollResult(
        expression=cleaned,
        advantage=advantage,
        warnings=warnings,
        rolls=rolls_win,
        rolls_lose_1=rolls_lose_1,
        rolls_lose_2=rolls_lose_2,
    )
