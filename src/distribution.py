from collections.abc import Iterable
import io
import math
import d20.diceast
import d20
import discord
import matplotlib.pyplot as plt
import numpy as np
from user_colors import UserColor


def to_matplotlib_color(color: int) -> tuple[float, float, float]:
    r, g, b = UserColor.to_rgb(color)
    return (r / 255.0, g / 255.0, b / 255.0)


class DiceDistributionBuilder(object):
    distribution: dict[int, float]
    warnings: set[str]

    def __init__(self):
        self.distribution = dict()
        self.warnings = set()

    def add(self, key: int, odds: float) -> None:
        self.distribution[key] = self.distribution.get(key, 0) + odds

    def add_warnings(self, warnings: set[str]) -> None:
        self.warnings.update(warnings)

    def build(self) -> "DiceDistribution":
        return DiceDistribution(self.distribution, self.warnings)


class DiceDistribution(object):
    distribution: dict[int, float]
    warnings: set[str]

    def __init__(self, distribution: dict[int, float], warnings: set[str]):
        # Ensure distribution contains at least one element
        assert len(distribution) > 0

        # Ensure total distribution is very close to 1.0
        assert abs(1.0 - sum(distribution.values())) < 1e-6

        self.distribution = distribution
        self.warnings = warnings

    @property
    def min(self) -> int:
        return min(self.keys())

    @property
    def max(self) -> int:
        return max(self.keys())

    @property
    def mean(self) -> float:
        return sum([value * odds for value, odds in self.distribution.items()])

    @property
    def stdev(self) -> float:
        # variance = E(X^2) - E(X)^2
        # stdev = sqrt(variance)
        e_x2 = sum([value * value * odds for value, odds in self.distribution.items()])
        ex_2 = self.mean * self.mean
        variance = e_x2 - ex_2
        return math.sqrt(variance)

    def keys(self) -> Iterable[int]:
        return self.distribution.keys()

    def get(self, key: int) -> float:
        return self.distribution.get(key, 0)

    def __add__(self, other: "DiceDistribution") -> "DiceDistribution":
        builder = DiceDistributionBuilder()
        builder.add_warnings(self.warnings)
        builder.add_warnings(other.warnings)

        for key_s in self.keys():
            for key_o in other.keys():
                builder.add(key_s + key_o, self.get(key_s) * other.get(key_o))

        return builder.build()

    def __sub__(self, other: "DiceDistribution") -> "DiceDistribution":
        builder = DiceDistributionBuilder()
        builder.add_warnings(self.warnings)
        builder.add_warnings(other.warnings)

        for key_s in self.keys():
            for key_o in other.keys():
                builder.add(key_s - key_o, self.get(key_s) * other.get(key_o))

        return builder.build()

    def __mul__(self, other: "DiceDistribution") -> "DiceDistribution":
        builder = DiceDistributionBuilder()
        builder.add_warnings(self.warnings)
        builder.add_warnings(other.warnings)

        for key_s in self.keys():
            for key_o in other.keys():
                builder.add(key_s * key_o, self.get(key_s) * other.get(key_o))

        return builder.build()

    def __floordiv__(self, other: "DiceDistribution") -> "DiceDistribution":
        builder = DiceDistributionBuilder()
        builder.add_warnings(self.warnings)
        builder.add_warnings(other.warnings)

        for key_s in self.keys():
            for key_o in other.keys():
                builder.add(key_s // key_o, self.get(key_s) * other.get(key_o))

        return builder.build()

    def __neg__(self) -> "DiceDistribution":
        distribution: dict[int, float] = dict()

        for value, odds in self.distribution.items():
            distribution[-value] = odds

        return DiceDistribution(distribution, self.warnings)

    def advantage(self) -> "DiceDistribution":
        builder = DiceDistributionBuilder()
        builder.add_warnings(self.warnings)

        for key_1 in self.keys():
            for key_2 in self.keys():
                builder.add(max(key_1, key_2), self.get(key_1) * self.get(key_2))

        return builder.build()

    def disadvantage(self) -> "DiceDistribution":
        builder = DiceDistributionBuilder()
        builder.add_warnings(self.warnings)

        for key_1 in self.keys():
            for key_2 in self.keys():
                builder.add(min(key_1, key_2), self.get(key_1) * self.get(key_2))

        return builder.build()

    def get_odds_higher_or_equal_than(self, value: int) -> float:
        odds = 0
        for key in self.keys():
            if key >= value:
                odds += self.get(key)
        return odds

    def chart(self, itr: discord.Interaction, min_to_beat: int) -> discord.File:
        keys = list(sorted(self.keys()))
        values = [100 * self.get(key) for key in keys]  # In percent

        white = UserColor.parse("#FFFFFF")  # TODO
        color = UserColor.get(itr)

        colors = []
        for key in keys:
            if key >= min_to_beat:
                colors.append(to_matplotlib_color(color))
            else:
                colors.append(to_matplotlib_color(white))

        plt.rcParams["figure.dpi"] = 600
        fig, ax = plt.subplots(subplot_kw=dict())

        max_ticks = 20 / len(str(self.max))
        steps = int(math.ceil(len(self.keys()) / max_ticks))
        ax.set_xticks(range(self.min, self.max + 1, steps))
        ax.yaxis.set_major_formatter("{x:.2f}%")  # Add percent on y-axis

        ax.tick_params(colors="white")
        ax.grid(color="white", alpha=0.3, linewidth=1)
        ax.spines["top"].set_color("white")
        ax.spines["right"].set_color("white")
        ax.spines["bottom"].set_color("white")
        ax.spines["left"].set_color("white")
        ax.bar(keys, values, color=colors)
        ax.set_axisbelow(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)
        buf.seek(0)
        plt.close(fig)

        return discord.File(fp=buf, filename="distribution.png")


def get_operated_dice_distribution(
    num: int, sides: int, operations: list[str]
) -> DiceDistribution:
    if num == 0 or sides == 0:
        return DiceDistribution({0: 1.0}, set())

    warnings = set()
    if len(operations) > 0:
        warnings.add(
            "Special dice are currently not supported. Dice modifiers are ignored."
        )

    distribution = DiceDistribution({0: 1.0}, warnings)

    for _ in range(num):
        distribution = distribution + DiceDistribution(
            {i + 1: 1 / sides for i in range(sides)}, set()
        )

    return distribution


def get_ast_distribution(ast: d20.ast.Node) -> DiceDistribution:
    if isinstance(ast, d20.diceast.Expression):
        return get_ast_distribution(ast.roll)

    if isinstance(ast, d20.diceast.Literal):
        return DiceDistribution({ast.value: 1.0}, set())

    if isinstance(ast, d20.diceast.UnOp):
        if ast.op == "-":
            return -get_ast_distribution(ast.value)
        if ast.op == "+":
            return get_ast_distribution(ast.value)
        return DiceDistribution(
            {0: 1.0}, set([f"Distribution: Unsupported UnOp operator '{ast.op}'!"])
        )

    if isinstance(ast, d20.diceast.BinOp):
        if ast.op == "+":
            return get_ast_distribution(ast.left) + get_ast_distribution(ast.right)
        if ast.op == "-":
            return get_ast_distribution(ast.left) - get_ast_distribution(ast.right)
        if ast.op == "*":
            return get_ast_distribution(ast.left) * get_ast_distribution(ast.right)
        if ast.op == "/":
            return get_ast_distribution(ast.left) // get_ast_distribution(ast.right)

        return DiceDistribution(
            {0: 1.0}, set([f"Distribution: Unsupported BinOp operator '{ast.op}'!"])
        )

    if isinstance(ast, d20.diceast.Dice):
        return get_operated_dice_distribution(ast.num, ast.size, [])

    if isinstance(ast, d20.diceast.OperatedDice):
        return get_operated_dice_distribution(
            ast.value.num, ast.value.size, ast.operations
        )

    if isinstance(ast, d20.diceast.Parenthetical):
        return get_ast_distribution(ast.value)

    return DiceDistribution(
        {0: 1.0}, set([f"Distribution: Unsupported dice type '{type(ast)}'!"])
    )


def get_dice_expression_distribution(expression: str) -> DiceDistribution:
    try:
        return get_ast_distribution(d20.parse(expression))
    except ZeroDivisionError:
        return DiceDistribution(
            {0: 1.0}, set(["Expression contains a possible division by zero!"])
        )
    except Exception:
        return DiceDistribution(
            {0: 1.0}, set(["There was an error parsing the expression!"])
        )


def get_distribution(expression: str, advantage: str) -> DiceDistribution:
    distribution = get_dice_expression_distribution(expression)

    if advantage == "advantage":
        distribution = distribution.advantage()
    elif advantage == "disadvantage":
        distribution = distribution.disadvantage()

    return distribution


class DiceDistributionEmbed(discord.Embed):
    image: discord.File

    def __init__(
        self,
        itr: discord.Interaction,
        expression: str,
        distribution: DiceDistribution,
        advantage: str,
        min_to_beat: int | None,
    ):
        color = UserColor.get(itr)

        if advantage == "advantage":
            title_suffix = " with advantage!"
        elif advantage == "disadvantage":
            title_suffix = " with disadvantage!"
        else:
            title_suffix = "!"

        super().__init__(
            color=color,
            title=f"Distribution for {expression}{title_suffix}",
            type="rich",
        )

        self.add_field(name="Mean", value=f"{distribution.mean:.2f}", inline=True)
        self.add_field(name="Stdev", value=f"{distribution.stdev:.2f}", inline=True)

        if min_to_beat is not None:
            odds = distribution.get_odds_higher_or_equal_than(min_to_beat)
            odds = f"{100*odds:.2f}%"
            self.add_field(name=f"Odds to beat {min_to_beat}", value=odds)

        warnings = sorted(list(distribution.warnings))
        for warning in warnings:
            self.add_field(name="", value=f"⚠️ {warning}", inline=False)
