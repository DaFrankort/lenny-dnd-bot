import discord

from embeds.embed import UserActionEmbed
from logic.color import UserColor
from logic.stats import Stats


class StatsEmbed(UserActionEmbed):
    itr: discord.Interaction
    stats: Stats
    chart: discord.File

    def __init__(self, itr: discord.Interaction, stats: Stats):
        self.itr = itr
        self.stats = stats
        self.chart = stats.get_radar_chart(UserColor.get(itr))

        title = self.get_title()
        description = self.get_description()

        super().__init__(itr, title, description)

        if self.stats.min_total > 0:
            footer = f"Minimum Total: {self.stats.min_total}\nSucceeded after {self.stats.roll_count} reroll"
            if self.stats.roll_count != 1:
                footer += "s"
            self.set_footer(text=f"{footer}.")

    def get_title(self) -> str:
        return f"Rolling stats for {self.itr.user.display_name}"

    def get_description(self) -> str:
        description = ""
        for rolls, result in self.stats.stats:
            r0, r1, r2, r3 = rolls
            description += f"`({r0}, {r1}, {r2}, {r3})` => **{result}**\n"
        description += f"\n**Total**: {self.stats.total}"
        return description
