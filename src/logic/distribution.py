import dataclasses
import io
import math
import d20
import d20distribution
from d20distribution.distribution import DiceDistribution
import discord
from matplotlib import pyplot as plt

from logic.color import UserColor
from logic.roll import Advantage


@dataclasses.dataclass
class DistributionResult(object):
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
    distribution: DiceDistribution,
    color: int,
    min_to_beat: float,
) -> discord.File:
    keys = list(sorted(distribution.keys()))
    values = [100 * distribution.get(key) for key in keys]  # In percent

    white = UserColor.parse("#FFFFFF")

    colors = []
    for key in keys:
        if key >= min_to_beat:
            colors.append(to_matplotlib_color(color))
        else:
            colors.append(to_matplotlib_color(white))

    plt.rcParams["figure.dpi"] = 600
    fig, ax = plt.subplots(subplot_kw=dict())

    keys = list(distribution.keys())
    max_ticks = 20 / len(str(max(keys)))
    steps = int(math.ceil(len(keys) / max_ticks))
    ax.set_xticks(range(distribution.min(), distribution.max() + 1, steps))
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


def distribution(
    expression: str,
    advantage: Advantage,
    color: int,
    min_to_beat: float | None = None,
):
    try:
        dist = d20distribution.parse(expression)
        expression = str(d20.parse(expr=expression))

        if advantage == Advantage.Advantage:
            dist = dist.advantage()
        elif advantage == Advantage.Disadvantage:
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
