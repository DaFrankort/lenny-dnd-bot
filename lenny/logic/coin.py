from __future__ import annotations

import re
from typing import TypeAlias

from lark import Lark, LarkError, Token, Transformer, Tree

COIN_GRAMMAR = r"""
    ?start: expr

    ?expr: term
         | expr "+" term   -> add
         | expr "-" term   -> sub

    ?term: factor
         | term "*" factor -> mul
         | term "/" factor -> div

    ?factor: NUMBER        -> number
           | COIN_UNIT     -> coin
           | "(" expr ")"

    COIN_UNIT.10: /[+-]?[\d.]+(pp|gp|ep|sp|cp)/

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""


COIN_PARSER: Lark = Lark(COIN_GRAMMAR, parser="lalr")
EvalResult: TypeAlias = "Coin | float"


class CoinTransformer(Transformer[EvalResult]):  # pyright: ignore[reportInvalidTypeArguments] - Conflict with pylint
    """Converts the Lark Tree into a Coin object or float."""

    def number(self, n: list[Token]) -> float:
        return float(n[0])

    def coin(self, items: list[Token]) -> Coin:
        return Coin.parse_unit(str(items[0]))

    def add(self, args: list[EvalResult]) -> EvalResult:
        left, right = args[0], args[1]
        if isinstance(left, float | int):
            return right + left
        return left + right

    def sub(self, args: list[EvalResult]) -> EvalResult:
        left, right = args[0], args[1]
        if isinstance(left, float | int):
            return right - left
        return left - right

    def mul(self, args: list[EvalResult]) -> EvalResult:
        left, right = args[0], args[1]
        if isinstance(left, Coin) and isinstance(right, float | int):
            return left * right
        if isinstance(right, Coin) and isinstance(left, float | int):
            return right * left
        if isinstance(left, float | int) and isinstance(right, float | int):
            return left * right
        if isinstance(left, Coin) and isinstance(right, Coin):
            raise ValueError("Cannot multiply coin with coin, use numerical values for the multiplier instead.")
        raise ValueError("Unexpected multiplication detected.")

    def div(self, args: list[EvalResult]) -> EvalResult:
        left, right = args[0], args[1]
        if isinstance(left, Coin) and isinstance(right, float | int):
            return left / right
        if isinstance(right, Coin) and isinstance(left, float | int):
            return right / left
        if isinstance(left, float | int) and isinstance(right, float | int):
            return left / right
        if isinstance(args[0], Coin) and isinstance(args[1], Coin):
            raise ValueError("Cannot divide coin by coin, use numerical values for divider instead.")
        raise ValueError("Unexpected division detected.")


class Coin:
    pp: float
    gp: float
    ep: float
    sp: float
    cp: float

    def __init__(self, cp: float = 0, sp: float = 0, ep: float = 0, gp: float = 0, pp: float = 0):
        self.pp, self.gp, self.ep, self.sp, self.cp = pp, gp, ep, sp, cp
        self.round_up()

    @property
    def total_cp(self) -> int:
        """Converts the entire wallet into a single Copper value."""
        return int((self.pp * 1000) + (self.gp * 100) + (self.ep * 50) + (self.sp * 10) + self.cp)

    @classmethod
    def from_string(cls, expression: str) -> Coin:
        try:
            raw_tree: Tree[Token] = COIN_PARSER.parse(  # type: ignore[reportInvalidTypeArguments]
                expression.lower()
            )  # pyright: ignore[reportUnknownMemberType]
            transformer = CoinTransformer()
            result = transformer.transform(raw_tree)  # pyright: ignore[reportUnknownVariableType, reportArgumentType]

            if isinstance(result, float | int):
                return cls(cp=float(result))
            return result  # pyright: ignore[reportUnknownVariableType]

        except LarkError as e:
            raise ValueError(
                f"Unsupported coin-syntax in ``{expression}``, supported:\n"
                "- coin units: ``cp``, ``sp``, ``ep``, ``gp``, ``pp``\n"
                "- operators: ``+``, ``-``, ``*``, ``/``"
            ) from e

    @classmethod
    def parse_unit(cls, block: str) -> Coin:
        match = re.match(r"([\d.]+)([a-z]+)", block)
        if not match:
            return cls()
        val, unit = match.groups()
        return cls(**{unit: float(val)})

    def round_up(self):
        """
        Converts all coins to the perfect amount, as if perfectly exchanged at a bank.
        """

        total = int(round(self.total_cp))
        sign = -1 if total < 0 else 1
        total = abs(total)

        pp, remainder = divmod(total, 1000)
        gp, remainder = divmod(remainder, 100)
        ep, remainder = divmod(remainder, 50)
        sp, cp = divmod(remainder, 10)

        self.pp = pp * sign
        self.gp = gp * sign
        self.ep = ep * sign
        self.sp = sp * sign
        self.cp = cp * sign

    def __add__(self, other: Coin | float) -> Coin:
        if isinstance(other, float | int):
            return Coin(cp=self.total_cp + other)
        return Coin(cp=self.total_cp + other.total_cp)

    def __sub__(self, other: Coin | float) -> Coin:
        if isinstance(other, float | int):
            return Coin(cp=self.total_cp - other)
        return Coin(cp=self.total_cp - other.total_cp)

    def __mul__(self, other: float) -> Coin:
        return Coin(cp=self.total_cp * other)

    def __truediv__(self, other: float) -> Coin:
        return Coin(cp=self.total_cp / other)

    def _get_denominations(self) -> list[tuple[float, str]]:
        def format_val(val: float):
            val = round(val, 2)
            return int(val) if val == int(val) else val

        denominations = [
            (self.cp, "cp"),
            (self.sp, "sp"),
            (self.ep, "ep"),
            (self.gp, "gp"),
            (self.pp, "pp"),
        ]

        return [(format_val(val), unit) for val, unit in denominations if val]

    @property
    def expr(self) -> str:
        """Returns the sum-expression that evaluates to the Coin result."""
        denominations = self._get_denominations()
        if not denominations:
            return "0cp"
        result: list[str] = []
        for i, (val, unit) in enumerate(denominations):
            term = f"{abs(val)}{unit}"
            if i == 0:
                result.append(f"-{term}" if val < 0 else term)
            else:
                result.append(f"- {term}" if val < 0 else f"+ {term}")
        return " ".join(result)

    def __str__(self) -> str:
        result = [f"``{val}`` {unit}" for val, unit in self._get_denominations()]
        return ", ".join(result) if result else "``0`` cp"

    def __repr__(self) -> str:
        parts: list[str] = []

        for name in ("cp", "sp", "ep", "gp", "pp"):
            value = getattr(self, name)
            if value:
                parts.append(f"{name}={value}")

        parts.append(f"total_cp={self.total_cp}")

        return f"Coin({', '.join(parts)})"
