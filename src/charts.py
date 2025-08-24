import io
import math
import discord
import d20distribution.distribution
from matplotlib import pyplot as plt
import numpy as np

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


def get_radar_chart(
    itr: discord.Interaction, results: list[str], labels: list[str] = None
) -> discord.File:
    # Shift results so result[0] goes to the end
    results = results[-1:] + results[:-1]
    if labels is not None:
        labels = labels[-1:] + labels[:-1]

    N = len(results)
    values = results + results[:1]  # repeat first to close polygon

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    # Create radar chart
    fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi)  # Start on the left
    ax.set_theta_direction(-1)  # Move

    ax.set_xticks(angles[:-1])
    if labels is None:
        ax.set_xticklabels([str(r) for r in results])
    else:
        for i, label in enumerate(labels):
            labels[i] = f"{results[i]}\n{label}"
        ax.set_xticklabels(labels)
    ax.set_ylim(0, max(18, max(values)))

    ax.set_yticklabels([])  # Remove numbers on radial rings

    r, g, b = discord.Color(UserColor.get(itr)).to_rgb()
    color = (r / 255.0, g / 255.0, b / 255.0)
    ax.plot(angles, values, color=color, linewidth=2)
    ax.fill(angles, values, color=color, alpha=0.4)

    ax.spines["polar"].set_color("white")
    ax.tick_params(colors="white")
    ax.grid(color="white", alpha=0.3, linewidth=1)

    # Save to memory
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)
    buf.seek(0)
    plt.close(fig)

    return discord.File(fp=buf, filename="stats.png")
