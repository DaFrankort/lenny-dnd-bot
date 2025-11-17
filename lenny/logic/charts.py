import io
from typing import TypeVar

import discord
import numpy as np
from matplotlib import pyplot as plt

T = TypeVar("T")


def _shift_list(values: list[T]) -> list[T]:
    return values[-1:] + values[:-1]


def _repeat_first(values: list[T]) -> list[T]:
    return values + values[:1]


class RadarChart:
    values: list[int]
    labels: list[str] | None
    boosts: list[int] | None
    color: int

    def __init__(self, values: list[int], labels: list[str] | None, boosts: list[int] | None, color: int):
        self.values = values
        self.labels = labels
        self.boosts = boosts
        self.color = color

    def __len__(self) -> int:
        return len(self.values)

    def total_value(self, index: int) -> int:
        if self.boosts is not None:
            return self.boosts[index]
        return self.values[index]

    def label(self, index: int) -> str:
        if self.labels is None:
            return str(self.total_value(index))
        return f"{self.labels[index]}\n{self.total_value(index)}"

    def build(self) -> io.BytesIO:
        values = _shift_list(self.values)
        labels = _shift_list([self.label(i) for i in range(len(self))])
        boosts = _shift_list([self.total_value(i) for i in range(len(self))]) if self.boosts is not None else None
        angles = np.linspace(0, 2 * np.pi, len(self), endpoint=False).tolist()

        values = _repeat_first(values)  # Repeat to close polygon
        angles = _repeat_first(angles)

        y_limit = max(18, *values)
        if boosts is not None:
            y_limit = max(y_limit, *boosts)
            boosts = _repeat_first(boosts)

        fig, ax = plt.subplots(subplot_kw={"polar": True})  # type: ignore
        ax.set_theta_offset(np.pi)  # Start on the left        # type: ignore
        ax.set_theta_direction(-1)  # Shift one to the right   # type: ignore
        ax.set_ylim(0, y_limit)
        ax.set_xticks(angles[:-1])  # type: ignore
        ax.set_xticklabels(labels)  # type: ignore
        ax.set_yticklabels([])  # type: ignore # Remove labels on the chart
        ax.grid(color="white", alpha=0.3, linewidth=1)  # type: ignore
        ax.tick_params(colors="white")  # type: ignore
        ax.spines["polar"].set_color("white")

        # Draw underlying boost lines
        if boosts is not None:
            boosted_rgb = (1.0, 1.0, 1.0)
            ax.plot(angles, boosts, color=boosted_rgb, linewidth=1, linestyle="--")  # type: ignore
            ax.fill(angles, boosts, color=boosted_rgb, alpha=0.1)  # type: ignore

        # Draw the overlapping lines
        r, g, b = discord.Color(self.color).to_rgb()
        color = (r / 255.0, g / 255.0, b / 255.0)
        ax.plot(angles, values, color=color, linewidth=2)  # type: ignore
        ax.fill(angles, values, color=color, alpha=0.4)  # type: ignore

        # Save to memory
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)  # type: ignore
        buf.seek(0)
        plt.close(fig)

        return buf


def get_radar_chart(
    values: list[int],
    labels: list[str] | None = None,
    boosts: list[int] | None = None,
    color: int = discord.Color.dark_green().value,
) -> discord.File:
    chart = RadarChart(values, labels, boosts, color)
    data = chart.build()
    return discord.File(fp=data, filename="stats.png")
