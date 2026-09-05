import io
import math

import matplotlib
import matplotlib.axes
import matplotlib.figure
import matplotlib.legend
from matplotlib import pyplot as plt

from logic.color import UserColor

# Required to calculate charts in a separate thread.
matplotlib.use("Agg")


def to_matplotlib_color(color: int) -> tuple[float, float, float]:
    r, g, b = UserColor.to_rgb(color)
    return (r / 255.0, g / 255.0, b / 255.0)


def empty_distribution_chart(keys: list[int]) -> tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    plt.rcParams["figure.dpi"] = 600
    fig, ax = plt.subplots(subplot_kw={})  # type: ignore

    max_ticks = 20 / len(str(max(keys)))
    steps = int(math.ceil(len(keys) / max_ticks))
    ax.set_xticks(range(min(keys), max(keys) + 1, steps))  # type: ignore
    ax.yaxis.set_major_formatter("{x:.2f}%")
    ax.tick_params(colors="white")  # type: ignore
    ax.grid(color="white", alpha=0.3, linewidth=1)  # type: ignore
    for spine in ("top", "right", "bottom", "left"):
        ax.spines[spine].set_color("white")
    ax.set_axisbelow(True)

    return fig, ax


def style_legend(legend: matplotlib.legend.Legend) -> None:
    frame = legend.get_frame()
    frame.set_alpha(None)
    frame.set_facecolor((1, 1, 1, 0.25))
    frame.set_edgecolor("white")
    frame.set_linewidth(1)

    for text in legend.texts:
        text.set_color("white")

    for handle in legend.legend_handles:
        if not handle:
            continue
        if hasattr(handle, "set_markeredgecolor"):
            handle.set_markeredgecolor("white")  # type: ignore
        if hasattr(handle, "set_markeredgewidth"):
            handle.set_markeredgewidth(0.5)  # type: ignore
        if hasattr(handle, "set_edgecolor"):
            handle.set_edgecolor("white")  # type: ignore


def convert_and_close_fig(fig: matplotlib.figure.Figure) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", transparent=True)  # type: ignore
    buf.seek(0)
    plt.close(fig)

    return buf
