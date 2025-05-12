from dataclasses import dataclass
from enum import Enum
import math
import random
import re
from abc import ABC, abstractmethod

import discord

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
- Unfinished expressions result in a crash, e.g. 1d20+
- Does not have fancy messages yet 
- Does not add reasons yet in title

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


class ASTExpression(ABC):
    @abstractmethod
    def roll(self) -> tuple[str, int]: ...

    @abstractmethod
    def __str__(self) -> str: ...


@dataclass
class ASTDiceExpression(ASTExpression):
    dice: Token

    def roll(self) -> tuple[str, int]:
        # TODO clean this up
        dice = self.dice.literal
        if dice.startswith("d"):
            dice = f"1{dice}"

        params = dice.split("d")

        # Single modifier, no d
        if len(params) == 1:
            value = params[0]
            return str(value), int(value)
        elif len(params) == 2:
            count = int(params[0])
            faces = int(params[1])
            rolls = [random.randint(1, faces) for _ in range(count)]
            roll = sum(rolls)
            text = "[" + ", ".join(map(str, rolls)) + "]"
            return text, roll
        else:
            print("Invalid dice", self.dice.literal)
            exit(1)

    def __str__(self) -> str:
        return self.dice.literal


@dataclass
class ASTGroupExpression(ASTExpression):
    """
    An ASTGroupExpression is an wrapper around an ASTExpression that preserves
    parentheses. This is useful to maintain formatting.
    """

    expression: ASTExpression

    def roll(self) -> tuple[str, int]:
        text, roll = self.expression.roll()
        return f"({text})", roll

    def __str__(self) -> str:
        return f"({str(self.expression)})"


@dataclass
class ASTCompoundExpression(ASTExpression):
    operator: Token
    left: ASTExpression
    right: ASTExpression

    def roll(self) -> tuple[str, int]:
        ltext, lroll = self.left.roll()
        rtext, rroll = self.right.roll()

        text = f"{ltext} {self.operator.literal} {rtext}"
        if self.operator.type == TokenType.Plus:
            roll = lroll + rroll
        elif self.operator.type == TokenType.Minus:
            roll = lroll - rroll
        elif self.operator.type == TokenType.Multiply:
            roll = lroll * rroll
        elif self.operator.type == TokenType.Divide:
            roll = int(math.floor(lroll / rroll))

        return text, roll

    def __str__(self):
        return f"{str(self.left)} {self.operator.literal} {str(self.right)}"


def _tokenize(expression: str) -> tuple[list[Token], list[str]]:
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
                pattern = r"^(([0-9]*d[0-9]+)|([0-9]+)).*$"
                matched = re.match(pattern, expression)
                if matched is not None:
                    dice = matched.group(1)
                    tokens.append(Token(dice, TokenType.Dice))
                    expression = expression.lstrip(dice)
                else:
                    pattern = r"^(.*?)([\+\-\*\/\ \t].*$|$)"
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


def _build_ast(postfix: list[Token]) -> tuple[ASTExpression, list[str]]:
    errors = []

    def get_next_node():
        if postfix[-1].type == TokenType.Dice:
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
            errors.append(f"Invalid expression: '{postfix[-1].literal}'")
            postfix.pop()

    return get_next_node(), errors


class DiceRollMode(Enum):
    Normal = "normal"
    Advantage = "advantage"
    Disadvantage = "disadvantage"


@dataclass
class DiceRoll(object):
    expression: str
    text: str
    value: int


class DiceExpression(object):
    ast: ASTExpression
    rolls: list[DiceRoll]
    result: int
    errors: list[str]
    mode: DiceRollMode
    title: str

    def __init__(self, expression: str, mode=DiceRollMode.Normal):
        self.ast = None
        self.rolls = []
        self.result = 0
        self.errors = []
        self.mode = mode
        self.title = ""

        tokens, errors = _tokenize(expression)
        if len(errors) > 0:
            self.errors = errors
            self.title = f"Errors found for '{expression}'"
            return

        postfix = _tokens_to_postfix(tokens)
        ast, errors = _build_ast(postfix)

        if len(errors) > 0:
            self.errors = errors
            self.title = f"Errors found for '{expression}'"
            return

        self.ast = ast

        if mode == DiceRollMode.Normal:
            text, roll = ast.roll()
            self.rolls.append(DiceRoll(expression, text, roll))
            self.result = roll
            self.title = f"Rolling {str(ast)}!"

        if mode == DiceRollMode.Advantage:
            text1, roll1 = ast.roll()
            text2, roll2 = ast.roll()
            self.rolls.append(DiceRoll(expression, text1, roll1))
            self.rolls.append(DiceRoll(expression, text2, roll2))
            self.result = max(roll1, roll2)
            self.title = f"Rolling {str(ast)} with advantage!"

        if mode == DiceRollMode.Disadvantage:
            text1, roll1 = ast.roll()
            text2, roll2 = ast.roll()
            self.rolls.append(DiceRoll(expression, text1, roll1))
            self.rolls.append(DiceRoll(expression, text2, roll2))
            self.result = min(roll1, roll2)
            self.title = f"Rolling {str(ast)} with disadvantage!"


class DiceEmbed(discord.Embed):
    def __init__(self, expression: DiceExpression):
        title = expression.title
        super().__init__(
            colour=discord.Color.dark_blue(),
            title=title,
            type="rich",
        )
        # TODO move this logic to DiceExpression
        description = ""

        if len(expression.errors) > 0:
            for error in expression.errors:
                description += f"{error}\n"
        else:
            for roll in expression.rolls:
                description += f"`{roll.text}` -> {roll.value}\n"
            description += f"**Result: {expression.result}**"

        self.add_field(name="", value=description)
