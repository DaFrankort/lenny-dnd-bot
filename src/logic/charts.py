import io
import discord
from matplotlib import pyplot as plt
import numpy as np


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
    ax.set_theta_direction(-1)  # Shift one to the right

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(18, max(values)))
    if boosted_results:
        ax.set_ylim(0, max(18, max(boosted_values)))
    ax.set_yticklabels([])  # Remove numbers on radial rings

    if boosted_results:
        boosted_rgb = (1.0, 1.0, 1.0)
        ax.plot(angles, boosted_values, color=boosted_rgb, linewidth=1, linestyle="--")
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
