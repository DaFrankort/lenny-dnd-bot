from dataclasses import dataclass
from enum import Enum
import logging
import math
import random
import re
from abc import ABC, abstractmethod


"""
Parses a dice expression and builds an Abstract Syntax Tree (AST) to roll for it.
Based on the webpages:
- https://fenga.medium.com/how-to-build-a-calculator-bf558e6bd8eb
- https://en.wikipedia.org/wiki/Abstract_syntax_tree

This file functions through the DiceExpression class:
- First, the input expression is tokenized.
  For example, the expression '3*(1d4+1)' gets split up into ['3', '*', '(', '1d4', '+', '1', ')']

- Then, the tokenized list gets transformed from prefix notation (the math notation we normally use)
  to postfix notation. Postfix notation is useful for building the abstract syntax tree later. Note
  that postfix notation reads from *right* to *left*.
  For example, the previous tokenized list gets transformed to ['3', '(', '1d4', '1', +, ')', '*']

- Based on the postfix list, the abstract syntax tree is built. We won't go into to detail about them,
  but a nice visualization can be found here https://keleshev.com/abstract-syntax-tree-an-example-in-c/

- Finally, now that the abstract syntax tree is built, we can recursively iterate through it to get
  our roll result.

Some notes:
- The ASTDiceExpression class sees both dice (e.g. 1d4) and constants (e.g. 5) as dice.

Current limitations:
- Does not support expressions that start with '-', for example (-5) * (1d4) will crash

"""


class TokenType(Enum):
    Dice = 0
    Plus = 2
    Minus = 3
    Divide = 4
    Multiply = 5
    LParenthesis = 6
    RParenthesis = 7


@dataclass
class Token(object):
    literal: str
    type: TokenType

    def __str__(self):
        match self.type:
            case TokenType.Dice:
                return f"DICE({self.literal})"
            case TokenType.Plus:
                return "PLUS"
            case TokenType.Minus:
                return "MINUS"
            case TokenType.Divide:
                return "DIVIDE"
            case TokenType.Multiply:
                return "MULTIPLY"
            case TokenType.LParenthesis:
                return "LPARENTHESIS"
            case TokenType.RParenthesis:
                return "RPARENTHESIS"
            case TokenType.Invalid:
                return f"INVALID({self.literal})"

    @property
    def precedence(self) -> int:
        if self.type in [TokenType.Plus, TokenType.Minus]:
            return 1
        if self.type in [TokenType.Multiply, TokenType.Divide]:
            return 2
        return 0

    @property
    def is_operator(self) -> bool:
        return self.type in [
            TokenType.Plus,
            TokenType.Minus,
            TokenType.Multiply,
            TokenType.Divide,
        ]


@dataclass
class DiceRollDice(object):
    roll: int
    face: int

    @property
    def is_d20(self) -> bool:
        return self.face == 20


class DiceRoll(object):
    text: str
    value: int
    dice_rolled: list[DiceRollDice]
    is_only_dice_modifiers_and_additions: bool
    warnings: set[str]
    errors: set[str]

    def __init__(self):
        self.text = ""
        self.value = 0
        self.dice_rolled = []
        self.is_only_dice_modifiers_and_additions = True
        self.warnings = set()
        self.errors = set()

    @property
    def is_natural_one(self) -> bool:
        if not self.is_only_dice_modifiers_and_additions:
            return False
        if len(self.dice_rolled) != 1:
            return False

        dice = self.dice_rolled[0]
        return dice.is_d20 and dice.roll == 1

    @property
    def is_natural_twenty(self) -> bool:
        if not self.is_only_dice_modifiers_and_additions:
            return False
        if len(self.dice_rolled) != 1:
            return False

        dice = self.dice_rolled[0]
        return dice.is_d20 and dice.roll == 20

    @property
    def is_dirty_twenty(self) -> bool:
        if not self.is_only_dice_modifiers_and_additions:
            return False
        if len(self.dice_rolled) != 1:
            return False
        dice = self.dice_rolled[0]
        return dice.is_d20 and dice.roll != 20 and self.value == 20


class ASTExpression(ABC):
    @abstractmethod
    def roll(self) -> DiceRoll:
        pass

    @abstractmethod
    def contains_dice(self) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass
class ASTDiceExpression(ASTExpression):
    dice: Token

    DICE_LIMIT = 8192

    def roll(self) -> DiceRoll:
        dice = self.dice.literal
        if dice.startswith("d"):
            dice = f"1{dice}"

        params = dice.split("d")

        # Modifier, no "d" found in dice
        if len(params) == 1:
            value = params[0]
            roll = DiceRoll()
            roll.text = str(value)
            roll.value = int(value)
            roll.is_only_dice_modifiers_and_additions = True
            roll.dice_rolled = []
            return roll
        # Dice
        elif len(params) == 2:
            roll = DiceRoll()

            count = int(params[0])
            if count > self.DICE_LIMIT:
                roll.warnings.add(
                    f"Dice count exceeded, limiting dice to {self.DICE_LIMIT}"
                )
                count = self.DICE_LIMIT
            faces = int(params[1])
            values = [random.randint(1, faces) for _ in range(count)]

            roll.text = "[" + ",".join(map(str, values)) + "]"
            roll.value = sum(values)
            roll.is_only_dice_modifiers_and_additions = True
            roll.dice_rolled = [DiceRollDice(value, faces) for value in values]
            return roll
        else:
            logging.error("Invalid dice", self.dice.literal)
            exit(1)  # TODO don't exit

    def contains_dice(self):
        return "d" in self.dice.literal

    def __str__(self) -> str:
        return self.dice.literal


@dataclass
class ASTGroupExpression(ASTExpression):
    """
    An ASTGroupExpression is an wrapper around an ASTExpression that preserves
    parentheses. This is useful to maintain formatting.
    """

    expression: ASTExpression

    def roll(self) -> DiceRoll:
        roll = self.expression.roll()
        roll.text = f"({roll.text})"
        return roll

    def contains_dice(self):
        return self.expression.contains_dice()

    def __str__(self) -> str:
        return f"({str(self.expression)})"


@dataclass
class ASTCompoundExpression(ASTExpression):
    operator: Token
    left: ASTExpression
    right: ASTExpression

    def roll(self) -> DiceRoll:
        roll = DiceRoll()
        lroll = self.left.roll()
        rroll = self.right.roll()

        roll.text = f"{lroll.text} {self.operator.literal} {rroll.text}"
        roll.is_only_dice_modifiers_and_additions = (
            self.operator.type in [TokenType.Plus, TokenType.Minus]
            and lroll.is_only_dice_modifiers_and_additions
            and rroll.is_only_dice_modifiers_and_additions
        )
        roll.dice_rolled.extend(lroll.dice_rolled)
        roll.dice_rolled.extend(rroll.dice_rolled)
        roll.warnings = lroll.warnings | rroll.warnings
        roll.errors = lroll.errors | rroll.errors

        if self.operator.type == TokenType.Plus:
            roll.value = lroll.value + rroll.value
        elif self.operator.type == TokenType.Minus:
            roll.value = lroll.value - rroll.value
        elif self.operator.type == TokenType.Multiply:
            roll.value = lroll.value * rroll.value
        elif self.operator.type == TokenType.Divide:
            if rroll.value == 0:
                roll.errors.add("Expression had a division by zero!")
                roll.value = 0
            else:
                roll.value = int(math.floor(lroll.value / rroll.value))

        return roll

    def contains_dice(self):
        return self.left.contains_dice() or self.right.contains_dice()

    def __str__(self):
        return f"{str(self.left)} {self.operator.literal} {str(self.right)}"


def _expression_to_tokens(expression: str) -> tuple[list[Token], list[str]]:
    expression = expression.lower().strip()
    valid_symbols = "0123456789+-*/()d"
    expression = "".join([c for c in expression if c in valid_symbols])

    tokens = []
    errors = []

    while len(expression) > 0:
        match expression[0]:
            case "(":
                tokens.append(Token("(", TokenType.LParenthesis))
                expression = expression[1:]
            case ")":
                tokens.append(Token(")", TokenType.RParenthesis))
                expression = expression[1:]
            case "+":
                tokens.append(Token("+", TokenType.Plus))
                expression = expression[1:]
            case "-":
                tokens.append(Token("-", TokenType.Minus))
                expression = expression[1:]
            case "*":
                tokens.append(Token("*", TokenType.Multiply))
                expression = expression[1:]
            case "/":
                tokens.append(Token("/", TokenType.Divide))
                expression = expression[1:]
            # Ignore whitespace
            case " " | "\t":
                expression = expression[1:]
            case _:
                # Check if it starts with a valid dice expression
                pattern = r"^(([0-9]*d[0-9]+)|([0-9]+))([\+\-\*\/\ \t\(\)].*$|$)"
                matched = re.match(pattern, expression)
                if matched is not None:
                    dice = matched.group(1)
                    tokens.append(Token(dice, TokenType.Dice))
                    expression = expression.lstrip(dice)
                else:
                    pattern = r"^(.*?)([\+\-\*\/\ \t\(\)].*$|$)"
                    matched = re.match(pattern, expression)
                    invalid = matched.group(1)
                    errors.append(f"Invalid symbol: '{invalid}'")
                    expression = expression.lstrip(invalid)

    return tokens, errors


def _tokens_to_postfix(tokens: list[Token]) -> list[Token]:
    output: list[Token] = []
    stack: list[Token] = []

    for token in tokens:
        if token.type == TokenType.Dice:
            output.append(token)
        elif token.is_operator:
            while stack and token.precedence <= stack[-1].precedence:
                output.append(stack.pop())
            stack.append(token)
        elif token.type == TokenType.LParenthesis:
            stack.append(token)
            output.append(token)
        elif token.type == TokenType.RParenthesis:
            while stack and stack[-1].type != TokenType.LParenthesis:
                output.append(stack.pop())
            if stack and stack[-1].type == TokenType.LParenthesis:
                stack.pop()  # Remove '('
            output.append(token)
    while stack:
        output.append(stack.pop())
    return output


def _postfix_to_ast(postfix: list[Token]) -> tuple[ASTExpression, list[str]]:
    if len(postfix) == 0:
        return None, ["Expression is empty."]

    errors = []

    def get_next_node():
        if len(postfix) == 0:
            errors.append("Expected operand but received nothing!")
            return None
        elif postfix[-1].type == TokenType.Dice:
            return ASTDiceExpression(postfix.pop())
        elif postfix[-1].is_operator:
            operator = postfix.pop()
            right = get_next_node()
            left = get_next_node()
            return ASTCompoundExpression(operator, left, right)

        # Specific situation: ()
        # This gets interpreted as (0)
        elif (
            len(postfix) >= 2
            and postfix[-1].type == TokenType.RParenthesis
            and postfix[-2].type == TokenType.LParenthesis
        ):
            postfix.pop()
            postfix.pop()
            return ASTGroupExpression(ASTDiceExpression(Token("0", TokenType.Dice)))

        elif postfix[-1].type == TokenType.RParenthesis:
            _ = postfix.pop()
            group = get_next_node()
            assert postfix[-1].type == TokenType.LParenthesis
            _ = postfix.pop()
            return ASTGroupExpression(group)
        else:
            errors.append(f"Invalid expression: '{postfix[-1].literal}'!")
            postfix.pop()

    return get_next_node(), errors


def _expression_to_ast(expression: str) -> tuple[ASTExpression, list[str]]:
    tokens, errors = _expression_to_tokens(expression)
    if len(errors) > 0:
        return None, errors

    postfix = _tokens_to_postfix(tokens)
    ast, errors = _postfix_to_ast(postfix)

    if len(errors) > 0:
        return None, errors

    return ast, []


class DiceRollMode(Enum):
    Normal = "normal"
    Advantage = "advantage"
    Disadvantage = "disadvantage"


class DiceExpression(object):
    ast: ASTExpression
    roll: DiceRoll
    rolls: list[DiceRoll]
    errors: list[str]
    mode: DiceRollMode
    title: str
    description: str
    ephemeral: bool  # Ephemeral in case an error occurred

    def __init__(self, expression: str, mode=DiceRollMode.Normal, reason: str = None):
        self.ast = None
        self.rolls = []
        self.result = 0
        self.errors = []
        self.mode = mode
        self.title = ""
        self.description = ""
        self.ephemeral = False

        ast, errors = _expression_to_ast(expression)

        if len(errors) > 0:
            self.ephemeral = True
            self.errors = errors
            self.title = f"Errors found for '{expression}'!"
            for error in errors:
                self.description += f"⚠️ {error}\n"
            return

        self.ast = ast

        if mode == DiceRollMode.Normal:
            roll = ast.roll()
            self.roll = roll
            self.rolls = [roll]
            self.title = f"Rolling {str(ast)}!"

        if mode == DiceRollMode.Advantage:
            roll1 = ast.roll()
            roll2 = ast.roll()
            self.roll = roll1 if roll1.value >= roll2.value else roll2
            self.rolls = [roll1, roll2]
            self.title = f"Rolling {str(ast)} with advantage!"

        if mode == DiceRollMode.Disadvantage:
            roll1 = ast.roll()
            roll2 = ast.roll()
            self.roll = roll1 if roll1.value <= roll2.value else roll2
            self.rolls = [roll1, roll2]
            self.title = f"Rolling {str(ast)} with disadvantage!"

        if len(self.roll.errors) > 0:
            self.ephemeral = True
            for error in self.roll.errors:
                self.description += f"❌ {error}"
            return

        if not ast.contains_dice():
            self.description += "⚠️ Expression contains no dice.\n"

        for warning in sorted(list(self.roll.warnings)):
            self.description += f"⚠️ {warning}\n"

        for roll in self.rolls:
            self.description += f"- `{roll.text}` -> {roll.value}\n"

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
        return self.ast is not None
