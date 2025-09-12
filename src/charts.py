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
    results: list[int] | list[tuple[int, str]],
    boosted_results: list[int] | list[tuple[int, str]] = None,
    offset: int = 1,
    color: int = discord.Color.dark_green().value,
) -> discord.File:
    # Shift results, to show them in a different spot.
    results = results[-offset:] + results[:-offset]
    if boosted_results:
        boosted_results = boosted_results[-offset:] + boosted_results[:-offset]

    if isinstance(results[0], tuple):
        values = [v for v, _ in results]
        labels = [f"{v}\n{label}" for v, label in results]
        if boosted_results:
            boosted_values = [v for v, _ in boosted_results]
            labels = [f"{v}\n{label}" for v, label in boosted_results]
    else:
        values = results
        labels = [str(v) for v in results]
        if boosted_results:
            boosted_values = boosted_results

    N = len(values)
    # repeat first to close polygon
    values = values + values[:1]
    if boosted_results:
        boosted_values = boosted_values + boosted_values[:1]

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    # Create radar chart
    fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi)  # Start on the left
    ax.set_theta_direction(-1)  # Move

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    if boosted_results:
        ax.set_ylim(0, max(18, max(max(values), max(boosted_values))))
    else:
        ax.set_ylim(0, max(18, max(values)))
    ax.set_yticklabels([])  # Remove numbers on radial rings

    if boosted_results:
        boosted_rgb = (1.0, 1.0, 1.0)
        ax.plot(
            angles,
            boosted_values,
            color=boosted_rgb,
            linewidth=1,
            linestyle="--",
            label="Boosted",
        )
        ax.fill(angles, boosted_values, color=boosted_rgb, alpha=0.1)

    r, g, b = discord.Color(color).to_rgb()
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
