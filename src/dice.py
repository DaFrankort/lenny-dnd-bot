import json
import logging
import d20

from enum import Enum
from pathlib import Path
from rapidfuzz import fuzz
from discord import Interaction
from discord.app_commands import Choice


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


def d20_is_only_dice_modifiers_and_additions(node: d20.ast.Node):
    if isinstance(node, d20.ast.Dice):
        return True
    if isinstance(node, d20.ast.OperatedDice):
        return True
    if isinstance(node, d20.ast.Literal):
        return True
    if isinstance(node, d20.ast.AnnotatedNumber):
        return True
    if isinstance(node, d20.ast.Parenthetical):
        return d20_is_only_dice_modifiers_and_additions(node.children[0])
    if isinstance(node, d20.ast.UnOp):
        return d20_is_only_dice_modifiers_and_additions(node.children[0])
    if isinstance(node, d20.ast.BinOp):
        return (
            node.op in ["+", "-"]
            and d20_is_only_dice_modifiers_and_additions(node.left)
            and d20_is_only_dice_modifiers_and_additions(node.right)
        )
    if isinstance(node, d20.ast.Expression):
        return d20_is_only_dice_modifiers_and_additions(node.roll)

    logging.warning(
        f"d20_is_only_dice_modifiers_and_additions: Unsupported type '{type(node)}'"
    )
    return False


def d20_contains_dice(node: d20.ast.Node):
    if isinstance(node, d20.ast.Dice):
        return True
    if isinstance(node, d20.ast.OperatedDice):
        return True
    if isinstance(node, d20.ast.Literal):
        return False
    if isinstance(node, d20.ast.AnnotatedNumber):
        return False
    if isinstance(node, d20.ast.Parenthetical):
        return d20_contains_dice(node.children[0])
    if isinstance(node, d20.ast.UnOp):
        return d20_contains_dice(node.children[0])
    if isinstance(node, d20.ast.BinOp):
        return d20_contains_dice(node.left) or d20_contains_dice(node.right)
    if isinstance(node, d20.ast.Expression):
        return d20_contains_dice(node.roll)

    logging.warning(f"d20_contains_dice: Unsupported type '{type(node)}'")
    return False


class D20DiceRolled(object):
    count: int
    faces: int
    results: list[int]

    @property
    def total(self):
        sum = 0
        for result in self.results:
            if isinstance(result, d20.Literal):
                sum += result.total
            else:
                sum += result
        return sum

    @property
    def is_d20(self):
        return self.count == 1 and self.faces == 20

    @property
    def is_natural_twenty(self):
        if len(self.results) != 1:
            return False
        return self.is_d20 and self.total == 20

    @property
    def is_natural_one(self):
        if len(self.results) != 1:
            return False
        return self.is_d20 and self.total == 1


def d20_get_dice_rolled(roll: any) -> list[D20DiceRolled]:
    if isinstance(roll, d20.Dice):
        rolls = []
        for die in roll.values:
            if die.kept:
                rolled = D20DiceRolled()
                rolled.faces = die.size
                rolled.count = len(die.values)
                rolled.results = die.values
                rolls.append(rolled)
        return rolls
    else:
        rolls = []
        for child in roll.children:
            rolls.extend(d20_get_dice_rolled(child))
        return rolls


class DiceRoll(object):
    roll: d20.RollResult | None
    errors: set[str]
    expression: str

    def __init__(self, expression: str):
        self.expression = expression
        self.errors = set()
        self.roll = None

        try:
            self.roll = d20.roll(expression, stringifier=DiceStringifier())
        except d20.errors.RollSyntaxError:
            self.errors.add(f"Expression '{expression}' has an invalid syntax!")
        except d20.errors.TooManyRolls:
            self.errors.add(f"Expression '{expression}' has too many dice rolls!")
        except Exception as exception:
            self.errors.add(str(exception))

    @property
    def is_natural_one(self) -> bool:
        if self.roll is None:
            return False
        if not d20_is_only_dice_modifiers_and_additions(self.roll.ast):
            return False
        dice = d20_get_dice_rolled(self.roll.expr)
        if len(dice) != 1:
            return False

        dice = dice[0]
        return dice.is_natural_one

    @property
    def is_natural_twenty(self) -> bool:
        if self.roll is None:
            return False
        if not d20_is_only_dice_modifiers_and_additions(self.roll.ast):
            return False
        dice = d20_get_dice_rolled(self.roll.expr)
        if len(dice) != 1:
            return False

        dice = dice[0]
        return dice.is_natural_twenty

    @property
    def is_dirty_twenty(self) -> bool:
        if self.roll is None:
            return False
        if not d20_is_only_dice_modifiers_and_additions(self.roll.ast):
            return False

        dice = d20_get_dice_rolled(self.roll.expr)
        if len(dice) != 1:
            return False

        dice = dice[0]
        return not dice.is_natural_twenty and self.roll.total == 20

    @property
    def value(self) -> int:
        if self.roll is None:
            return 0
        return self.roll.total


class DiceRollMode(Enum):
    Normal = "normal"
    Advantage = "advantage"
    Disadvantage = "disadvantage"


class DiceExpression(object):
    roll: DiceRoll
    rolls: list[DiceRoll]
    mode: DiceRollMode
    title: str
    description: str
    ephemeral: bool  # Ephemeral in case an error occurred

    def __init__(self, expression: str, mode=DiceRollMode.Normal, reason: str = None):
        self.rolls = []
        self.result = 0
        self.mode = mode
        self.title = ""
        self.description = ""
        self.ephemeral = False
        expression = expression.lower()  # d20 library requires lowercase expressions.

        if mode == DiceRollMode.Normal:
            roll = DiceRoll(expression)
            self.roll = roll
            self.rolls = [roll]

        elif mode == DiceRollMode.Advantage:
            roll1 = DiceRoll(expression)
            roll2 = DiceRoll(expression)
            self.roll = roll1 if roll1.value >= roll2.value else roll2
            self.rolls = [roll1, roll2]

        elif mode == DiceRollMode.Disadvantage:
            roll1 = DiceRoll(expression)
            roll2 = DiceRoll(expression)
            self.roll = roll1 if roll1.value <= roll2.value else roll2
            self.rolls = [roll1, roll2]

        if len(self.roll.errors) > 0:
            self.ephemeral = True
            for error in self.roll.errors:
                self.title = f"Error rolling expression '{expression}'!"
                self.description += f"❌ {error}"
            return

        if mode == DiceRollMode.Normal:
            self.title = f"Rolling {str(self.roll.roll.ast)}!"
        elif mode == DiceRollMode.Advantage:
            self.title = f"Rolling {str(self.roll.roll.ast)} with advantage!"
        elif mode == DiceRollMode.Disadvantage:
            self.title = f"Rolling {str(self.roll.roll.ast)} with disadvantage!"

        if not d20_contains_dice(self.roll.roll.ast):
            self.description += "⚠️ Expression contains no dice.\n"

        for roll in self.rolls:
            self.description += f"- `{str(roll.roll)}` -> {roll.value}\n"

        if reason is None:
            reason = "Result"

        self.description += f"\n🎲 **{reason.capitalize()}: {self.roll.value}**"

        extra_messages = []
        if self.roll.is_natural_twenty:
            extra_messages.append("🎯 **Critical Hit!**")
        if self.roll.is_natural_one:
            extra_messages.append("💀 **Critical Fail!**")
        if self.roll.is_dirty_twenty:
            extra_messages.append("⚔️  **Dirty 20!**")

        if len(extra_messages) > 0:
            self.description += "\n" + "\n".join(extra_messages)

        if len(self.description) > 1024:
            self.description = "⚠️ Message too long, try sending a shorter expression!"

    @property
    def is_valid(self) -> bool:
        return self.roll.roll is not None


class DiceExpressionCache:
    PATH = Path("./temp/dice_cache.json")
    _data = None  # cache in memory to avoid frequent file reads

    @classmethod
    def init(cls):
        if cls.PATH.exists():
            cls._load_data()
            return

        cls._data = {}
        cls._save_data()

    @classmethod
    def _load_data(cls):
        if cls._data is not None:
            return cls._data
        if cls.PATH.exists():
            with cls.PATH.open("r") as f:
                cls._data = json.load(f)
        else:
            cls._data = {}
        return cls._data

    @classmethod
    def _save_data(cls):
        if cls._data is None:
            return
        with cls.PATH.open("w") as f:
            json.dump(cls._data, f, indent=4)

    @classmethod
    def store(cls, itr: Interaction, expression: DiceExpression):
        """Stores a user's used expression to the cache, if it is without errors."""
        if len(expression.roll.errors) > 0:
            return

        user_id = str(itr.user.id)
        notation = expression.roll.expression
        data = cls._load_data()
        user_notations = data.get(user_id, [])

        if notation in user_notations:
            user_notations.remove(notation)

        user_notations.append(notation)
        user_notations = user_notations[-5:]  # Store max 5 expressions
        data[user_id] = user_notations
        cls._save_data()

    @classmethod
    def get_last(
        cls, itr: Interaction, query: str, fuzzy_threshold: float = 75
    ) -> list[Choice[str]]:
        """Returns auto-complete choices for the last roll expressions a user used."""
        user_id = str(itr.user.id)
        user_exprs = cls._load_data().get(user_id, [])  # Reversed, last should be shown first.

        if len(user_exprs) == 0:
            return []

        query = query.strip().lower().replace(" ", "")
        if query == "":
            choices = []
            for i, expr in enumerate(reversed(user_exprs)):
                if i == 0:
                    # Mark the last-used expression
                    choices.append(Choice(name=f"{expr} [Last Rolled]", value=expr))
                else:
                    choices.append(Choice(name=expr, value=expr))
            return choices

        choices = []
        for expr in reversed(user_exprs):
            expr_clean = expr.strip().lower().replace(" ", "")

            score = fuzz.partial_ratio(query, expr_clean)
            if score > fuzzy_threshold:
                choices.append(Choice(name=expr, value=expr))

        return choices
