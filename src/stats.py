import io
import random
import discord
import numpy as np
import matplotlib.pyplot as plt


class Stats:
    """Class for rolling character-stats in D&D 5e."""

    stats: list[tuple[list[int], int]]
    interaction: discord.Interaction

    def __init__(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction
        self.stats = [self.roll_stat() for _ in range(6)]

    def roll_stat(self) -> tuple[list[int], int]:
        """Rolls a single stat in D&D 5e."""
        rolls = [random.randint(1, 6) for _ in range(4)]
        rolls = sorted(rolls)
        result = sum(rolls[1:])
        return rolls, result

    def get_embed_title(self) -> str:
        return f"Rolling stats for {self.interaction.user.display_name}"

    def get_embed_description(self) -> str:
        message = ""
        total = 0

        for rolls, result in self.stats:
            r0, r1, r2, r3 = rolls
            message += f"`({r0}, {r1}, {r2}, {r3})` => **{result}**\n"
            total += result

        message += f"\n**Total**: {total}"
        return message

    def get_radar_chart(self) -> discord.File:
        results = [result for _, result in self.stats]
        N = len(results)
        values = results + results[:1]  # repeat first to close polygon

        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]

        # Create radar chart
        fig, ax = plt.subplots(subplot_kw=dict(polar=True))
        ax.set_xticks(angles[:-1])
        # ax.set_xticklabels(labels)
        ax.set_ylim(0, 18)

        ax.plot(angles, values, color="red", linewidth=2)
        ax.fill(angles, values, color="red", alpha=0.25)

        # Save to memory
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)
        buf.seek(0)
        plt.close(fig)

        return discord.File(fp=buf, filename="stats.png")
