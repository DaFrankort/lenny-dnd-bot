import io
import math
import discord
import d20distribution.distribution
from matplotlib import pyplot as plt

from user_colors import UserColor


def to_matplotlib_color(color: int) -> tuple[float, float, float]:
    r, g, b = UserColor.to_rgb(color)
    return (r / 255.0, g / 255.0, b / 255.0)


def get_distribution_chart(
    itr: discord.Interaction,
    distribution: d20distribution.distribution.DiceDistribution,
    min_to_beat: int,
) -> discord.File:
    keys = list(sorted(distribution.keys()))
    values = [100 * distribution.get(key) for key in keys]  # In percent

    white = UserColor.parse("#FFFFFF")
    color = UserColor.get(itr)

    colors = []
    for key in keys:
        if key >= min_to_beat:
            colors.append(to_matplotlib_color(color))
        else:
            colors.append(to_matplotlib_color(white))

    plt.rcParams["figure.dpi"] = 600
    fig, ax = plt.subplots(subplot_kw=dict())

    max_ticks = 20 / len(str(max(distribution.keys())))
    steps = int(math.ceil(len(distribution.keys()) / max_ticks))
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
