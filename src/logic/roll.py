import dataclasses
from enum import Enum
import d20


class DiceRollMode(Enum):
    Normal = "normal"
    Advantage = "advantage"
    Disadvantage = "disadvantage"


class DiceSpecial(Enum):
    Natural20 = "nat20"
    Natural1 = "nat1"
    Dirty20 = "dirty20"


class DiceStringifier(d20.Stringifier):
    def _stringify(self, node):
        if not node.kept:
            return None
        return super()._stringify(node)

    def _extract_values(self, values: any):
        results = []
        for result in [self._stringify(value) for value in values]:
            if result is not None:
                results.append(result)
        return results

    def _str_expression(self, node):
        return self._stringify(node.roll)

    def _str_literal(self, node):
        # See d20 stringifiers.py:122 SimpleStringifier
        # A literal can have multiple values, and the last value in the list is the final value
        return str(node.values[-1])

    def _str_unop(self, node):
        return f"{node.op}{self._stringify(node.value)}"

    def _str_binop(self, node):
        return f"{self._stringify(node.left)} {node.op} {self._stringify(node.right)}"

    def _str_parenthetical(self, node):
        return f"({self._stringify(node.value)}){self._str_ops(node.operations)}"

    def _str_set(self, node):
        values = self._extract_values(node.values)
        return "{" + ",".join(values) + "}"

    def _str_dice(self, node):
        values = self._extract_values(node.values)
        return "[" + ",".join(values) + "]"

    def _str_die(self, node):
        values = self._extract_values(node.values)
        return ",".join(values)


def _is_only_dice_modifiers_and_additions(node: d20.Number) -> bool:
    if isinstance(node, d20.Literal):
        return True
    if isinstance(node, d20.Dice):
        return True
    if isinstance(node, d20.Die):
        return True
    if isinstance(node, d20.Parenthetical):
        return _is_only_dice_modifiers_and_additions(node.children[0])
    if isinstance(node, d20.UnOp):
        return _is_only_dice_modifiers_and_additions(node.children[0])
    if isinstance(node, d20.BinOp):
        return (
            node.op in ["+", "-"]
            and _is_only_dice_modifiers_and_additions(node.left)
            and _is_only_dice_modifiers_and_additions(node.right)
        )
    if isinstance(node, d20.Expression):
        return _is_only_dice_modifiers_and_additions(node.roll)

    raise NotImplementedError(f"Unsupported type '{type(node)}'")


def _extract_dice(node: d20.Number) -> list[d20.Dice | d20.Die]:
    if isinstance(node, d20.Dice):
        return [node]
    if isinstance(node, d20.Die):
        return [node]
    if isinstance(node, d20.Literal):
        return []
    if isinstance(node, d20.Parenthetical):
        return _extract_dice(node.children[0])
    if isinstance(node, d20.UnOp):
        return _extract_dice(node.children[0])
    if isinstance(node, d20.BinOp):
        return _extract_dice(node.left) + _extract_dice(node.right)
    if isinstance(node, d20.Expression):
        return _extract_dice(node.roll)

    raise NotImplementedError(f"Unsupported type '{type(node)}'")


def _contains_dice(node: d20.Number) -> bool:
    return len(_extract_dice(node)) > 0


def _is_d20(dice: d20.Die | d20.Dice) -> bool:
    if isinstance(dice, d20.Die):
        return dice.size == 20
    if isinstance(dice, d20.Dice):
        return dice.num == 1 and dice.size == 20
    return False


def _is_natural_20(node: d20.Number) -> bool:
    if not _is_only_dice_modifiers_and_additions(node):
        return False

    dice = _extract_dice(node)
    if len(dice) != 1:
        return False

    return _is_d20(dice[0]) and dice[0].total == 20


def _is_natural_1(node: d20.Number) -> bool:
    if not _is_only_dice_modifiers_and_additions(node):
        return False

    dice = _extract_dice(node)
    if len(dice) != 1:
        return False
    return _is_d20(dice[0]) and dice[0].total == 1


def _is_dirty_20(node: d20.Number) -> bool:
    if not _is_only_dice_modifiers_and_additions(node):
        return False

    dice = _extract_dice(node)
    if len(dice) != 1:
        return False
    return _is_d20(dice[0]) and node.total == 20


@dataclasses.dataclass
class SingleRollResult(object):
    expression: str
    total: int
    special: DiceSpecial | None
    contains_dice: bool

    @property
    def is_natural_twenty(self) -> bool:
        return self.special == DiceSpecial.Natural20

    @property
    def is_natural_one(self) -> bool:
        return self.special == DiceSpecial.Natural1

    @property
    def is_dirty_twenty(self) -> bool:
        return self.special == DiceSpecial.Dirty20


class RollResult(object):
    expression: str
    mode: DiceRollMode
    rolls: list[SingleRollResult]
    error: str | None

    def __init__(self):
        self.expression = ""
        self.mode = DiceRollMode.Normal
        self.error = None
        self.rolls = []

    @property
    def roll(self) -> SingleRollResult:
        totals = [roll.total for roll in self.rolls]
        match self.mode:
            case DiceRollMode.Advantage:
                total = max(totals)
            case DiceRollMode.Disadvantage:
                total = min(totals)
            case _:
                total = totals[0]

        for r in self.rolls:
            if r.total == total:
                return r
        return None


def _roll_single(expression: str) -> SingleRollResult:
    roll = d20.roll(expression, stringifier=DiceStringifier())

    special = None
    if _is_natural_20(roll.expr):
        special = DiceSpecial.Natural20
    elif _is_natural_1(roll.expr):
        special = DiceSpecial.Natural1
    elif _is_dirty_20(roll.expr):
        special = DiceSpecial.Dirty20

    contains_dice = _contains_dice(roll.expr)

    return SingleRollResult(str(roll.expr), roll.total, special, contains_dice)


def roll(expression: str, mode: DiceRollMode = DiceRollMode.Normal) -> RollResult:
    result = RollResult()

    try:
        # Clean expression
        expression = str(d20.parse(expression, allow_comments=False))

        result.expression = expression
        result.mode = mode
        if mode in [DiceRollMode.Advantage, DiceRollMode.Disadvantage]:
            result.rolls.append(_roll_single(expression))
            result.rolls.append(_roll_single(expression))
        else:
            result.rolls.append(_roll_single(expression))

    except d20.errors.RollSyntaxError:
        result.error = f"Expression '{expression}' has an invalid syntax!"
    except d20.errors.TooManyRolls:
        result.error = f"Expression '{expression}' has too many dice rolls!"
    except Exception as exception:
        result.error = str(exception)

    return result
