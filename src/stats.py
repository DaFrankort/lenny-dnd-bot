import random
import discord
from charts import get_radar_chart


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

    def get_radar_chart(self, color: int = discord.Color.dark_green()) -> discord.File:
        results = [result for _, result in self.stats]
        return get_radar_chart(results=results, color=color)
