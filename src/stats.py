import random
import discord

from user_colors import UserColor

class _StatRoll:
    """Class for rolling a single stat in D&D 5e."""
    rolls: list[int]
    result: int

    def __init__(self) -> None:
        self.rolls, self.result = self.roll()

    def roll(self) -> tuple[list[int], int]:
        rolls = [random.randint(1, 6) for _ in range(4)]
        rolls = sorted(rolls)
        result = sum(rolls[1:])
        return rolls, result

class Stats:
    """Class for rolling character-stats in D&D 5e."""
    stats: list[_StatRoll]
    interaction: discord.Interaction

    def __init__(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction
        self.stats = []
        for _ in range(6):
            self.stats.append(_StatRoll())

    def get_embed_title(self) -> str:
        return f"Rolling stats for {self.interaction.user.display_name}"
    
    def get_embed_description(self) -> str:
        message = ""
        total = 0

        for stat_roll in self.stats:
            r0, r1, r2, r3 = stat_roll.rolls
            result = stat_roll.result
            message += f"`({r0}, {r1}, {r2}, {r3})` => **{result}**\n"
            total += result

        message += f"**Total**: {total}"
        return message

class StatsEmbed(discord.Embed):
    """Embed for rolling character-stats in D&D 5e."""
    def __init__(self, stats: Stats) -> None:
        super().__init__(
            color=UserColor.get(stats.interaction),
            title=stats.get_embed_title(),
            type="rich",
            url=None,
            description=None,
            timestamp=None,
        )
        self.add_field(name="", value=stats.get_embed_description())
