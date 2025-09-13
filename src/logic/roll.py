from enum import Enum
import logging

import d20

# region Utility functions for parsing d20 expressions


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


def _is_only_dice_modifiers_and_additions(node: d20.Number):
    if isinstance(node, d20.Dice):
        return True
    if isinstance(node, d20.Die):
        return True
    if isinstance(node, d20.Literal):
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

    logging.warning(
        f"_is_only_dice_modifiers_and_additions: Unsupported type '{type(node)}'"
    )
    return False


def _extract_dice(node: d20.Number) -> list[d20.Dice]:
    if isinstance(node, d20.Die):
        # Normally, this should not occur with a roll result as it is a helper class
        return []
    if isinstance(node, d20.Dice):
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

    logging.warning(f"_extract_dice: Unsupported type '{type(node)}'")
    return False


def _contains_dice(node: d20.Number):
    return len(_extract_dice(node)) > 0


def _is_nat_20(node: d20.Number) -> bool:
    if not _is_only_dice_modifiers_and_additions(node):
        return False

    dice = _extract_dice(node)
    if len(dice) != 1:
        return False

    return dice[0].num == 1 and dice[0].size == 20 and dice[0].total == 20


def _is_nat_1(node: d20.Number) -> bool:
    if not _is_only_dice_modifiers_and_additions(node):
        return False

    dice = _extract_dice(node)
    if len(dice) != 1:
        return False

    return dice[0].num == 1 and dice[0].size == 20 and dice[0].total == 1


def _is_dirty_20(node: d20.Number) -> bool:
    if not _is_only_dice_modifiers_and_additions(node):
        return False

    dice = _extract_dice(node)
    if len(dice) != 1:
        return False

    return (
        node.total == 20
        and dice[0].num == 1
        and dice[0].size == 20
        and dice[0].total != 20
    )


# endregion

# region Roll results


class Advantage(object):
    Normal = "normal"
    Advantage = "advantage"
    Disadvantage = "disadvantage"


class ResultSpecific(object):
    Nat20 = "nat20"
    Nat1 = "nat1"
    Dirty20 = "dirty20"


class RollResult(object):
    expression: str
    rolls: list[d20.RollResult]
    total: int
    advantage: Advantage
    specific: ResultSpecific | None
    contains_dice: bool
    error: str | None

    def __init__(self):
        self.expression = ""
        self.rolls = []
        self.total = 0
        self.advantage = Advantage.Normal
        self.specific = None
        self.contains_dice = False
        self.error = None

    @property
    def is_natural_twenty(self):
        return self.specific == ResultSpecific.Nat20

    @property
    def is_natural_one(self):
        return self.specific == ResultSpecific.Nat1

    @property
    def is_dirty_twenty(self):
        return self.specific == ResultSpecific.Dirty20


def roll(expression: str, advantage: Advantage) -> RollResult:
    expression = str(d20.parse(expr=expression.lower()))  # Clean expression
    stringifier = DiceStringifier()

    result = RollResult()
    result.advantage = advantage
    result.expression = expression

    try:
        if advantage == Advantage.Advantage:
            rolls = [
                d20.roll(expr=expression, stringifier=stringifier),
                d20.roll(expr=expression, stringifier=stringifier),
            ]
            rolled = rolls[0] if rolls[0].total > rolls[1].total else rolls[1]
        elif advantage == Advantage.Disadvantage:
            rolls = [
                d20.roll(expr=expression, stringifier=stringifier),
                d20.roll(expr=expression, stringifier=stringifier),
            ]
            rolled = rolls[0] if rolls[0].total < rolls[1].total else rolls[1]
        else:
            rolls = [d20.roll(expr=expression, stringifier=stringifier)]
            rolled = rolls[0]

    except d20.errors.RollSyntaxError:
        result.error = f"Expression '{expression}' has an invalid syntax!"
    except d20.errors.TooManyRolls:
        result.error = f"Expression '{expression}' has too many dice rolls!"
    except Exception as exception:
        result.error = str(exception)

    # If succeeded, handle results
    if result.error is None:
        result.rolls = rolls
        result.total = rolled.total
        result.contains_dice = _contains_dice(rolled.expr)

        if _is_nat_20(rolled.expr):
            result.specific = ResultSpecific.Nat20
        elif _is_nat_1(rolled.expr):
            result.specific = ResultSpecific.Nat1
        elif _is_dirty_20(rolled.expr):
            result.specific = ResultSpecific.Dirty20

    return result


# endregion
