import random
import discord

from user_colors import UserColor


class StatsEmbed(discord.Embed):
    def _roll(self) -> tuple[list[int], int]:
        rolls = [random.randint(1, 6) for _ in range(4)]
        rolls = sorted(rolls)
        result = sum(rolls[1:])
        return rolls, result

    def __init__(self, interaction: discord.Interaction) -> None:
        super().__init__(
            color=UserColor.get(interaction),
            title=f"Rolling stats for {interaction.user.display_name}",
            type="rich",
            url=None,
            description=None,
            timestamp=None,
        )

        message = ""
        total = 0
        for _ in range(6):
            [r0, r1, r2, r3], result = self._roll()
            message += f"`({r0}, {r1}, {r2}, {r3})` => **{result}**\n"
            total += result
        message += f"**Total**: {total}"

        self.add_field(name="", value=message)
