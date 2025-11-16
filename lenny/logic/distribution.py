import dataclasses
import io
import math

import d20  # type: ignore # Ignore missing stubs
import d20distribution  # type: ignore
import discord
from d20distribution.distribution import DiceDistribution  # type: ignore
from matplotlib import pyplot as plt

from logic.color import UserColor
from logic.roll import Advantage


@dataclasses.dataclass
class DistributionResult:
    expression: str
    chart: discord.File
    advantage: Advantage
    mean: float
    stdev: float
    min_to_beat: tuple[float, float] | None


def to_matplotlib_color(color: int) -> tuple[float, float, float]:
    r, g, b = UserColor.to_rgb(color)
    return (r / 255.0, g / 255.0, b / 255.0)


def _distribution_chart(
    dist: DiceDistribution,
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


def distribution(
    expression: str,
    advantage: Advantage,
    color: int,
    min_to_beat: float | None = None,
):
    try:
        dist = d20distribution.parse(expression)
        expression = str(d20.parse(expr=expression))

        if advantage == Advantage.ADVANTAGE:
            dist = dist.advantage()
        elif advantage == Advantage.DISADVANTAGE:
            dist = dist.disadvantage()

        if min_to_beat is None:
            min_to_beat = 0
            min_to_beat_and_odds = None
        else:
            min_to_beat = float(min_to_beat or 0)
            odds = 0
            for key in dist.keys():
                odds += dist.get(key) if key >= min_to_beat else 0
            min_to_beat_and_odds = (min_to_beat, odds)

        mean = dist.mean()
        stdev = dist.stdev()
        chart = _distribution_chart(dist, color, min_to_beat)

        return DistributionResult(expression, chart, advantage, mean, stdev, min_to_beat_and_odds)
    except Exception as exception:
        raise exception
