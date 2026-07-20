from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar, Literal, TypeAlias, TypeGuard, Union, cast, get_args

from lark import Lark, LarkError, Token, Transformer

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
        | "-" factor    -> neg
        | "+" factor    -> pos
        | "(" expr ")"

    COIN_UNIT.10: /[+-]?[\d.]+(pp|gp|ep|sp|cp)/

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""


CoinUnit = Literal["cp", "sp", "ep", "gp", "pp"]
Operators = Literal["+", "-", "*", "/"]


def is_coin_unit(val: str) -> TypeGuard[CoinUnit]:
    """Runtime check that narrows down a raw string to the CoinUnit Literal type."""
    return val in get_args(CoinUnit)


@dataclass(frozen=True)
class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""

    pass


@dataclass(frozen=True)
class NumberNode(ASTNode):
    value: float


@dataclass(frozen=True)
class CoinNode(ASTNode):
    value: float
    unit: CoinUnit


@dataclass(frozen=True)
class NegNode(ASTNode):
    """Represents a unary negative operation (e.g., -expr)."""

    operand: ASTNode


@dataclass(frozen=True)
class BinOpNode(ASTNode):
    op: Operators
    left: ASTNode
    right: ASTNode


@dataclass
class Coin:
    cp: float = 0.0
    sp: float = 0.0
    ep: float = 0.0
    gp: float = 0.0
    pp: float = 0.0

    DENOMINATIONS: ClassVar[list[CoinUnit]] = ["cp", "sp", "ep", "gp", "pp"]  # Always order from small to largest!
    CONVERSIONS: ClassVar[dict[CoinUnit, int]] = {
        "pp": 1000,
        "gp": 100,
        "ep": 50,
        "sp": 10,
        "cp": 1,
    }

    @classmethod
    def from_cp(cls, total_cp: float, limit_to_unit: CoinUnit = "pp") -> Coin:
        """
        Constructs a consolidated Coin instance from raw copper value,
        capping the bank exchange to the specified 'limit_to_unit'.

        Example: If limit_to_unit is "gp", any leftover value that would
        normally become "pp" is kept as "gp" instead.
        """
        total = int(round(total_cp))
        sign = -1 if total < 0 else 1
        total = abs(total)

        limit_idx = cls.DENOMINATIONS.index(limit_to_unit)
        allowed_denoms = cls.DENOMINATIONS[: limit_idx + 1]

        values = {denom: 0.0 for denom in cls.DENOMINATIONS}
        remainder = total

        for denom in reversed(allowed_denoms):
            unit_value = cls.CONVERSIONS[denom]
            if denom == allowed_denoms[0]:
                values[denom] = remainder
            else:
                amount, remainder = divmod(remainder, unit_value)
                values[denom] = amount

        return cls(
            pp=values["pp"] * sign,
            gp=values["gp"] * sign,
            ep=values["ep"] * sign,
            sp=values["sp"] * sign,
            cp=values["cp"] * sign,
        )

    @property
    def total_cp(self) -> float:
        return sum([(getattr(self, unit) * value) for unit, value in self.CONVERSIONS.items()])

    def __str__(self) -> str:
        denoms: list[str] = []
        for unit in self.DENOMINATIONS:
            val = getattr(self, unit)
            if val:
                formatted_val = int(val) if val == int(val) else round(val, 2)
                denoms.append(f"``{formatted_val}`` {unit}")
        return ", ".join(denoms) if denoms else "``0`` cp"

    def consolidate(self, limit_to_unit: CoinUnit = "pp") -> None:
        """Consolidates current sparse fields into the standard bank values."""
        raw_cp = self.total_cp
        consolidated = self.from_cp(raw_cp, limit_to_unit=limit_to_unit)
        self.pp = consolidated.pp
        self.gp = consolidated.gp
        self.ep = consolidated.ep
        self.sp = consolidated.sp
        self.cp = consolidated.cp


class ASTTransformer(Transformer[ASTNode]):
    """Transforms Lark Tree strictly into our clean, decoupled ASTNode objects."""

    def number(self, n: list[Token]) -> NumberNode:
        return NumberNode(float(n[0]))

    def coin(self, items: list[Token]) -> CoinNode:
        block = str(items[0])
        match = re.match(r"([\d.]+)([a-z]+)", block)
        if not match:
            raise ValueError(f"Failed to parse coin slice: {block}")
        val, unit = match.groups()
        if not is_coin_unit(unit):
            raise ValueError(f"Invalid coin unit: '{unit}'. Must be one of cp, sp, ep, gp, pp.")
        return CoinNode(float(val), unit)

    def neg(self, args: list[ASTNode]) -> NegNode:
        return NegNode(args[0])

    def pos(self, args: list[ASTNode]) -> ASTNode:
        return args[0]

    def add(self, args: list[ASTNode]) -> BinOpNode:
        return BinOpNode("+", args[0], args[1])

    def sub(self, args: list[ASTNode]) -> BinOpNode:
        return BinOpNode("-", args[0], args[1])

    def mul(self, args: list[ASTNode]) -> BinOpNode:
        return BinOpNode("*", args[0], args[1])

    def div(self, args: list[ASTNode]) -> BinOpNode:
        return BinOpNode("/", args[0], args[1])


EvalValue: TypeAlias = Union[Coin, float]


class CoinEvaluator:
    """Evaluates an AST containing Coin and Numeric nodes."""

    limit_to_unit: CoinUnit

    def __init__(self, limit_to_unit: CoinUnit = "pp"):
        self.limit_to_unit = limit_to_unit

    def _float_to_coin(self, value: float | int) -> Coin:
        return Coin(gp=value)

    def evaluate(self, node: ASTNode) -> EvalValue:
        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, CoinNode):
            kwargs = {node.unit: node.value}
            return Coin(**kwargs)

        if isinstance(node, NegNode):
            inner = self.evaluate(node.operand)
            if isinstance(inner, Coin):
                return Coin.from_cp(-inner.total_cp, self.limit_to_unit)
            return -inner

        if isinstance(node, BinOpNode):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            return self._apply_operator(node.op, left, right)

        raise TypeError(f"Unknown AST node type: {type(node)}")

    def _apply_operator(self, op: str, left: EvalValue, right: EvalValue) -> EvalValue:
        if op == "+":
            return self._add(left, right)
        elif op == "-":
            return self._sub(left, right)
        elif op == "*":
            return self._mul(left, right)
        elif op == "/":
            return self._div(left, right)
        raise ValueError(f"Unsupported operator: {op}")

    def _add(self, left: EvalValue, right: EvalValue) -> EvalValue:
        left = self._float_to_coin(left) if isinstance(left, float | int) else left
        right = self._float_to_coin(right) if isinstance(right, float | int) else right
        return Coin.from_cp(left.total_cp + right.total_cp, self.limit_to_unit)

    def _sub(self, left: EvalValue, right: EvalValue) -> EvalValue:
        left = self._float_to_coin(left) if isinstance(left, float | int) else left
        right = self._float_to_coin(right) if isinstance(right, float | int) else right
        return Coin.from_cp(left.total_cp - right.total_cp, self.limit_to_unit)

    def _mul(self, left: EvalValue, right: EvalValue) -> EvalValue:
        if isinstance(left, Coin) and isinstance(right, Coin):
            raise ValueError("Cannot multiply coin by coin.")
        if isinstance(left, Coin) and isinstance(right, float | int):
            return Coin.from_cp(left.total_cp * right, self.limit_to_unit)
        if isinstance(left, float | int) and isinstance(right, Coin):
            return Coin.from_cp(left * right.total_cp, self.limit_to_unit)
        return float(left * right)  # pyright: ignore

    def _div(self, left: EvalValue, right: EvalValue) -> EvalValue:
        if isinstance(left, Coin) and isinstance(right, Coin):
            raise ValueError("Cannot divide coin by coin.")
        if isinstance(left, Coin) and isinstance(right, float | int):
            return Coin.from_cp(left.total_cp / right, self.limit_to_unit)
        if isinstance(left, float | int) and isinstance(right, Coin):
            return Coin.from_cp(left / right.total_cp, self.limit_to_unit)
        return float(left / right)  # pyright: ignore


@dataclass
class CoinResult:
    expression: str
    ast: ASTNode
    value: EvalValue
    used_units: set[CoinUnit]
    limit_to_unit: CoinUnit = "pp"

    @property
    def coin(self) -> Coin:
        """Returns result as a clean consolidated Coin object, converting floats to cp."""
        if isinstance(self.value, Coin):
            return self.value
        return Coin.from_cp(self.value)


LARK_PARSER = Lark(COIN_GRAMMAR, parser="lalr")
AST_BUILDER = ASTTransformer()


def collect_used_units(node: ASTNode) -> set[CoinUnit]:
    """
    Recursively traverses the AST to find all coin units
    explicitly typed by the user.
    """
    if isinstance(node, CoinNode):
        return {node.unit}
    elif isinstance(node, NumberNode):
        return {"gp"}
    elif isinstance(node, BinOpNode):
        return collect_used_units(node.left) | collect_used_units(node.right)
    return set()


def parse_coin(expression: str) -> CoinResult:
    """Parses, builds the AST, and evaluates the expression into a CoinResult."""
    try:
        raw_tree = LARK_PARSER.parse(expression.lower())
        ast: ASTNode = AST_BUILDER.transform(raw_tree)

        used_units = collect_used_units(ast)
        highest_unit: CoinUnit = "cp"
        if used_units:
            highest_unit = cast(CoinUnit, max(used_units, key=lambda u: Coin.DENOMINATIONS.index(u)))  # type: ignore
        evaluator = CoinEvaluator(limit_to_unit=highest_unit)
        value = evaluator.evaluate(ast)
        return CoinResult(expression=expression, ast=ast, value=value, used_units=used_units, limit_to_unit=highest_unit)
    except LarkError as e:
        allowed_units = ", ".join(f"``{u}``" for u in get_args(CoinUnit))
        operators = ", ".join(f"``{op}``" for op in get_args(Operators))
        raise ValueError(
            f"Unsupported coin-syntax in ``{expression}``, supported:\n"
            f"- coin units: {allowed_units}\n"
            f"- operators: {operators}"
        ) from e
