from dataclasses import dataclass
from enum import Enum
import math
import random
import re
from abc import ABC, abstractmethod

"""
Parses a dice expression and builds an Abstract Syntax Tree (AST) to roll for it.
Based on the webpages:
- https://fenga.medium.com/how-to-build-a-calculator-bf558e6bd8eb
- https://en.wikipedia.org/wiki/Abstract_syntax_tree
"""


class DiceTokenType(Enum):
    Dice = 0
    Plus = 2
    Minus = 3
    Divide = 4
    Multiply = 5
    LParenthesis = 6
    RParenthesis = 7
    Invalid = 8


@dataclass
class DiceToken(object):
    literal: str
    type: DiceTokenType

    def __str__(self):
        match self.type:
            case DiceTokenType.Dice:
                return f"DICE({self.literal})"
            case DiceTokenType.Plus:
                return "PLUS"
            case DiceTokenType.Minus:
                return "MINUS"
            case DiceTokenType.Divide:
                return "DIVIDE"
            case DiceTokenType.Multiply:
                return "MULTIPLY"
            case DiceTokenType.LParenthesis:
                return "LPARENTHESIS"
            case DiceTokenType.RParenthesis:
                return "RPARENTHESIS"
            case DiceTokenType.Invalid:
                return f"INVALID({self.literal})"

    @property
    def precedence(self) -> int:
        if self.type in [DiceTokenType.Plus, DiceTokenType.Minus]:
            return 1
        if self.type in [DiceTokenType.Multiply, DiceTokenType.Divide]:
            return 2
        return 0

    @property
    def is_operator(self) -> bool:
        return self.type in [
            DiceTokenType.Plus,
            DiceTokenType.Minus,
            DiceTokenType.Multiply,
            DiceTokenType.Divide,
        ]


class DiceASTExpression(ABC):
    @abstractmethod
    def roll(self) -> tuple[str, int]: ...

    @abstractmethod
    def __str__(self) -> str: ...


@dataclass
class DiceASTDiceExpression(DiceASTExpression):
    dice: DiceToken

    def roll(self) -> tuple[str, int]:
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
class DiceASTGroupExpression(DiceASTExpression):
    expression: DiceASTExpression

    def roll(self) -> tuple[str, int]:
        text, roll = self.expression.roll()
        return f"({text})", roll

    def __str__(self) -> str:
        return f"({str(self.expression)})"


@dataclass
class DiceASTInfixExpression(DiceASTExpression):
    operator: DiceToken
    left: DiceASTExpression
    right: DiceASTExpression

    def roll(self) -> tuple[str, int]:
        ltext, lroll = self.left.roll()
        rtext, rroll = self.right.roll()

        text = f"{ltext} {self.operator.literal} {rtext}"
        if self.operator.type == DiceTokenType.Plus:
            roll = lroll + rroll
        elif self.operator.type == DiceTokenType.Minus:
            roll = lroll - rroll
        elif self.operator.type == DiceTokenType.Multiply:
            roll = lroll * rroll
        elif self.operator.type == DiceTokenType.Divide:
            roll = int(math.floor(lroll / rroll))

        return text, roll

    def __str__(self):
        return f"{str(self.left)} {self.operator.literal} {str(self.right)}"


def __tokenize(expression: str) -> list[DiceToken]:
    tokens = []

    while len(expression) > 0:
        match expression[0]:
            case "(":
                tokens.append(DiceToken("(", DiceTokenType.LParenthesis))
                expression = expression[1:]
            case ")":
                tokens.append(DiceToken(")", DiceTokenType.RParenthesis))
                expression = expression[1:]
            case "+":
                tokens.append(DiceToken("+", DiceTokenType.Plus))
                expression = expression[1:]
            case "-":
                tokens.append(DiceToken("-", DiceTokenType.Minus))
                expression = expression[1:]
            case "*":
                tokens.append(DiceToken("*", DiceTokenType.Multiply))
                expression = expression[1:]
            case "/":
                tokens.append(DiceToken("/", DiceTokenType.Divide))
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
                    tokens.append(DiceToken(dice, DiceTokenType.Dice))
                    expression = expression.lstrip(dice)
                else:
                    pattern = r"^(.*?)([\+\-\*\/\ \t].*$|$)"
                    matched = re.match(pattern, expression)
                    invalid = matched.group(1)
                    tokens.append(DiceToken(invalid, DiceTokenType.Invalid))
                    expression = expression.lstrip(invalid)
    return tokens


def __tokens_to_postfix(tokens: list[DiceToken]) -> list[DiceToken]:
    output: list[DiceToken] = []
    stack: list[DiceToken] = []

    for token in tokens:
        if token.type == DiceTokenType.Dice:
            output.append(token)
        elif token.is_operator:
            while stack and token.precedence <= stack[-1].precedence:
                output.append(stack.pop())
            stack.append(token)
        elif token.type == DiceTokenType.LParenthesis:
            stack.append(token)
            output.append(token)
        elif token.type == DiceTokenType.RParenthesis:
            while stack and stack[-1].type != DiceTokenType.LParenthesis:
                output.append(stack.pop())
            if stack and stack[-1].type == DiceTokenType.LParenthesis:
                stack.pop()  # Remove '('
            output.append(token)
    while stack:
        output.append(stack.pop())
    return output


def __build_ast(postfix: list[DiceToken]) -> DiceASTExpression:
    def get_next_node():
        if postfix[-1].type == DiceTokenType.Dice:
            return DiceASTDiceExpression(postfix.pop())
        elif postfix[-1].is_operator:
            operator = postfix.pop()
            right = get_next_node()
            left = get_next_node()
            return DiceASTInfixExpression(operator, left, right)
        elif postfix[-1].type == DiceTokenType.RParenthesis:
            _ = postfix.pop()
            group = get_next_node()
            assert postfix[-1].type == DiceTokenType.LParenthesis
            _ = postfix.pop()
            return DiceASTGroupExpression(group)
        else:
            print("Invalid expression")
            exit(1)

    return get_next_node()


class DiceExpression(object):
    def __init__(self, expression: str):
        pass

    def roll(self) -> tuple[str, int]:
        return "", 0


def dice_test():
    expressions = [
        "1d20+5*(3*4-5d9/2)",
        "1d20+(3*4+5d9*2)*5",
        "2d20+2d20+4",
        # ") 5 * x        yz - 3d3 + 1 (  "
    ]

    for expression in expressions:
        tokens = __tokenize(expression)
        postfix = __tokens_to_postfix(tokens)
        print(expression)
        for token in postfix:
            print(str(token), end=" ")
        print()
        ast = __build_ast(postfix)
        roll, result = ast.roll()
        print(str(ast))
        print(roll)
        print(result)
        print()
