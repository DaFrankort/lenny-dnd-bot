from dataclasses import dataclass
from enum import Enum
import re
from abc import ABC, ABCMeta, abstractmethod


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


class DiceASTExpression(ABC):
    @abstractmethod
    def roll(self) -> tuple[str, int]: ...

    @abstractmethod
    def __str__(self) -> str: ...


@dataclass
class DiceASTDiceExpression(DiceASTExpression):
    dice: DiceToken

    def __str__(self) -> str:
        return self.dice.literal


class DiceExpression(object):
    def __init__(self, expression: str):
        pass

    @staticmethod
    def tokenize(expression: str) -> list[DiceToken]:
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

    @staticmethod
    def build_ast(tokens: list[DiceToken]) -> tuple[list, list[str]]: ...

    def roll(self) -> tuple[str, int]:
        return "", 0
