import dataclasses
import io
import math

import d100
import discord
import matplotlib
from d100.distribution import Distribution
from matplotlib import pyplot as plt

from logic.color import UserColor
from logic.roll import Advantage, clean_expression, parse
import numpy as np

# Required to calculate the chart in a separate thread, https://stackoverflow.com/questions/27147300/matplotlib-tcl-asyncdelete-async-handler-deleted-by-the-wrong-thread
matplotlib.use("Agg")

"""
TODO:
- Use colors based on the user's color for multi-chart
- Create a separate function for overlap bars
  - Draw each layer at 10% (or something, depending on the amount of distributions)
  - Convert the colored graph parts to a separate image
  - Make this image fully opaque
  - Create a new chart with the exact same layout and axes, but completely empty
  - Past the opaque charts onto the empty layout
- Remove code duplication
"""


class SingleDistributionResult:
    distribution: Distribution
    advantage: Advantage
    expression: str
    min_to_beat: int | None

    def __init__(self, expr: str, advantage: Advantage, min_to_beat: int | None) -> None:
        self.expression = expr
        self.min_to_beat = min_to_beat
        self.advantage = advantage
        self.distribution = dice_distribution(expr, advantage=advantage)

    @property
    def min_to_beat_odds(self) -> float:
        if self.min_to_beat is None:
            return 0

        return self.distribution.get_at_least(self.min_to_beat)
    
    @property
    def min(self) -> int:
        return self.distribution.min()

    @property
    def max(self) -> int:
        return self.distribution.max()

@dataclasses.dataclass
class DistributionResult:
    distributions: list[SingleDistributionResult]
    chart: discord.File
    advantage: Advantage
    min_to_beat: int | None

    @property
    def min(self) -> int:
        return min(dist.distribution.min() for dist in self.distributions)

    @property
    def max(self) -> int:
        return max(dist.distribution.max() for dist in self.distributions)


def to_matplotlib_color(color: int) -> tuple[float, float, float]:
    r, g, b = UserColor.to_rgb(color)
    return (r / 255.0, g / 255.0, b / 255.0)


def _single_distribution_chart(
    dist: Distribution,
    color: int,
    min_to_beat: float,
) -> discord.File:
    keys = list(sorted(dist.keys()))
    values = [100 * dist.get(key) for key in keys]  # In percent

    white = UserColor.parse("#FFFFFF")

    colors: list[tuple[float, float, float]] = []
    for key in keys:
        if key >= min_to_beat:
            colors.append(to_matplotlib_color(color))
        else:
            colors.append(to_matplotlib_color(white))

    plt.rcParams["figure.dpi"] = 600
    fig, ax = plt.subplots(subplot_kw={})  # type: ignore

    keys = list(dist.keys())
    max_ticks = 20 / len(str(max(keys)))
    steps = int(math.ceil(len(keys) / max_ticks))
    ax.set_xticks(range(dist.min(), dist.max() + 1, steps))  # type: ignore
    ax.yaxis.set_major_formatter("{x:.2f}%")  # Add percent on y-axis

    ax.tick_params(colors="white")  # type: ignore
    ax.grid(color="white", alpha=0.3, linewidth=1)  # type: ignore
    ax.spines["top"].set_color("white")
    ax.spines["right"].set_color("white")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.bar(keys, values, color=colors)  # type: ignore
    ax.set_axisbelow(True)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)  # type: ignore
    buf.seek(0)
    plt.close(fig)

    return discord.File(fp=buf, filename="distribution.png")


def _multi_adjacent_distribution_chart(dists: list[SingleDistributionResult]) -> discord.File:
    min_key = min(dist.min  for dist in dists)
    max_key = max(dist.max for dist in dists)
    keys = list(range(min_key, max_key + 1))

    plt.rcParams["figure.dpi"] = 600
    fig, ax = plt.subplots(subplot_kw={})  # type: ignore

    max_ticks = 20 / len(str(max(keys)))
    steps = int(math.ceil(len(keys) / max_ticks))
    ax.set_xticks(range(min_key, max_key + 1, steps))  # type: ignore
    ax.yaxis.set_major_formatter("{x:.2f}%")  # Add percent on y-axis

    ax.tick_params(colors="white")  # type: ignore
    ax.grid(color="white", alpha=0.3, linewidth=1)  # type: ignore
    ax.spines["top"].set_color("white")
    ax.spines["right"].set_color("white")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.set_axisbelow(True)

    total_bar_width = 0.8
    single_bar_width = total_bar_width / len(dists)

    for i, dist in enumerate(dists):
        values = [100 * dist.distribution.get(key) for key in keys]  # In percent

        offset = i * single_bar_width - total_bar_width / 2 + single_bar_width / 2
        ax.bar(np.array(keys) + offset, values, width=single_bar_width, label = dist.expression)  # type: ignore

    ax.legend() #type: ignore

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)  # type: ignore
    buf.seek(0)
    plt.close(fig)

    return discord.File(fp=buf, filename="distribution.png")


def dice_distribution(expression: str, advantage: Advantage = Advantage.NORMAL):
    parsed, _ = parse(expression, advantage)
    return d100.distribution(parsed)


def distribution(
    expressions: str,
    advantage: Advantage,
    color: int,
    min_to_beat: int | None = None,
):
    split = expressions.split(",")
    cleaned = [clean_expression(expr) for expr in split if expr]
    results = [SingleDistributionResult(expr, advantage, min_to_beat) for expr in cleaned]

    if len(results) == 0:
        raise ValueError(f"Expected at least one dice expression in '{expressions}'!")
    elif len(results) == 1:
        chart = _single_distribution_chart(dist=results[0].distribution, color=color, min_to_beat=min_to_beat or 0)
    else:
        chart = _multi_adjacent_distribution_chart(results)
        ...

    return DistributionResult(
        distributions=results,
        chart=chart,
        advantage=advantage,
        min_to_beat=min_to_beat,
    )
