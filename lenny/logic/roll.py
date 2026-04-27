import dataclasses

# The usage of d20 requires many type: ignore comments, as d20 does not use any form of typing internally
import d20  # type: ignore
from d20.enums import Advantage as D20Advantage  # type: ignore
from d20.roll import RollResult, SingleRollResult # type: ignore
from d20.roll import expression # type: ignore
from d20.roll.stringifier import SimpleStringifier  # type: ignore

from methods import ChoicedEnum


class Advantage(str, ChoicedEnum):
    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"
    ELVEN_ACCURACY = "elven accuracy"

    @property
    def title_suffix(self) -> str:
        suffixes = {
            self.ADVANTAGE: " with advantage",
            self.DISADVANTAGE: " with disadvantage",
            self.ELVEN_ACCURACY: " with elven accuracy",
        }
        return suffixes.get(self, "")

    @property
    def advantage(self) -> D20Advantage:
        match self:
            case self.NORMAL:
                return D20Advantage.NONE
            case self.ADVANTAGE:
                return D20Advantage.ADVANTAGE
            case self.DISADVANTAGE:
                return D20Advantage.DISADVANTAGE
            case self.ELVEN_ACCURACY:
                return D20Advantage.ELVEN_ACCURACY

    @classmethod
    def from_advantage(cls, advantage: D20Advantage) -> "Advantage":
        match advantage:
            case advantage.NONE:
                return Advantage.NORMAL
            case advantage.ADVANTAGE:
                return Advantage.ADVANTAGE
            case advantage.DISADVANTAGE:
                return Advantage.DISADVANTAGE
            case advantage.ELVEN_ACCURACY:
                return Advantage.ELVEN_ACCURACY


class DiceStringifier(SimpleStringifier):
    def _str_expression(self, node: expression.Expression):
        return f"{self._stringify(node.roll)}"

    def _str_dice(self, node: expression.Dice):
        dice = list(self._str_die(die, node.size) for die in node.keptset)
        return "[" + ",".join(dice) + "]"

    def _str_die(self, die: expression.Die, size: d20.ast.DiceSize) -> str:
        return str(die.value)


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


def _validate_expression(expr: str) -> RollResult:
    # Roll an expression once, to check for errors
    try:
        return d20.roll(expr)
    except d20.errors.RollSyntaxError as exception:
        raise SyntaxError(f"Expression '{expr}' has an invalid syntax!") from exception
    except d20.errors.TooManyRolls as exception:
        raise TimeoutError(f"Expression '{expr}' has too many dice rolls!") from exception
    except Exception as exception:
        raise exception


def roll(expr: str, advantage: Advantage = Advantage.NORMAL) -> RollResult:
    stringifier = DiceStringifier()
    return d20.roll(expr, stringifier, advantage.advantage)


def multi_roll(expr: str, amount: int, advantage: Advantage) -> MultiRollResult:
    stringifier = DiceStringifier()
    validation = _validate_expression(expr)
    expr = str(d20.parse(expr))

    rolls_win: list[SingleRollResult] = []
    rolls_lose_1: list[SingleRollResult] = []
    rolls_lose_2: list[SingleRollResult] = []

    for _ in range(amount):
        reverse = advantage == Advantage.DISADVANTAGE
        rolls = d20.roll(expr, stringifier, advantage.advantage).rolls
        rolls = list(sorted(rolls, key=lambda r: r.total, reverse=reverse))

        rolls_win.append(rolls[-1])
        if advantage.advantage.rolls >= 2:
            rolls_lose_1.append(rolls[0])
        if advantage.advantage.rolls >= 3:
            rolls_lose_2.append(rolls[1])

    return MultiRollResult(
        expr,
        advantage,
        warnings=validation.warnings,
        rolls=rolls_win,
        rolls_lose_1=rolls_lose_1,
        rolls_lose_2=rolls_lose_2,
    )
