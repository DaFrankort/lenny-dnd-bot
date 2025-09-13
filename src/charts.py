import io
import discord
from matplotlib import pyplot as plt
import numpy as np


def get_radar_chart(
    results: list[int] | list[tuple[int, str]],
    offset: int = 1,
    color: int = discord.Color.dark_green().value,
) -> discord.File:
    results = (
        results[-offset:] + results[:-offset]
    )  # Shift results, to show them in a different spot.

    if isinstance(results[0], tuple):
        values = [v for v, _ in results]
        labels = [f"{v}\n{label}" for v, label in results]
    else:
        values = results
        labels = [str(v) for v in results]

    N = len(values)
    values = values + values[:1]  # repeat first to close polygon

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    # Create radar chart
    fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi)  # Start on the left
    ax.set_theta_direction(-1)  # Move

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(18, max(values)))
    ax.set_yticklabels([])  # Remove numbers on radial rings

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
