import discord

from embeds.components import BaseSeparator, TitleTextDisplay
from embeds.embed import UserActionEmbed
from logic.color import UserColor
from logic.stats import BoughtStats, Stats


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


class PointBuyActionRow(discord.ui.ActionRow[discord.ui.LayoutView]):
    key: str
    stats: BoughtStats

    label_button: discord.ui.Button[discord.ui.LayoutView]
    minus_button: discord.ui.Button[discord.ui.LayoutView]
    plus_button: discord.ui.Button[discord.ui.LayoutView]

    def __init__(self, key: str, stats: BoughtStats):
        self.key = key
        self.stats = stats
        super().__init__()

        stat = stats.stats[key]
        mod = (stat - 10) // 2
        self.label_button = discord.ui.Button(style=discord.ButtonStyle.gray, label=f"{key} - {stat} ({mod})", disabled=True)

        self.minus_button = discord.ui.Button(style=discord.ButtonStyle.red, label="-")
        self.minus_button.callback = self.remove_point

        self.plus_button = discord.ui.Button(style=discord.ButtonStyle.green, label="+")
        self.plus_button.callback = self.add_point

        self.add_item(self.label_button)
        self.add_item(self.minus_button)
        self.add_item(self.plus_button)

    async def add_point(self, interaction: discord.Interaction):
        if self.stats.stats[self.key] >= 20:
            return
        self.stats.stats[self.key] += 1
        await self.update_message(interaction)

    async def remove_point(self, interaction: discord.Interaction):
        if self.stats.stats[self.key] <= 1:
            return
        self.stats.stats[self.key] -= 1
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        if self.stats.points_left <= 0:
            for child in self.children:
                if child.label == "+":  # type: ignore
                    child.disabled = True  # type: ignore

        view = BoughtStatsLayoutView(interaction, self.stats)
        await interaction.response.edit_message(view=view)


class BoughtStatsLayoutView(discord.ui.LayoutView):
    itr: discord.Interaction
    stats: BoughtStats
    chart: discord.File

    def __init__(self, itr: discord.Interaction, stats: BoughtStats):
        self.itr = itr
        self.stats = stats
        self.chart = stats.get_radar_chart(UserColor.get(itr))
        color = UserColor.get(itr)

        title = self.get_title()

        super().__init__(timeout=60 * 60)

        container: discord.ui.Container[discord.ui.LayoutView] = discord.ui.Container(accent_color=color)

        container.add_item(TitleTextDisplay(name=title))
        container.add_item(discord.ui.TextDisplay(f"{stats.points_left} Points left. ({stats.spent} / {stats.max_points})"))
        container.add_item(BaseSeparator())

        container.add_item(PointBuyActionRow("STR", stats))
        container.add_item(PointBuyActionRow("DEX", stats))
        container.add_item(PointBuyActionRow("CON", stats))
        container.add_item(PointBuyActionRow("INT", stats))
        container.add_item(PointBuyActionRow("WIS", stats))
        container.add_item(PointBuyActionRow("CHA", stats))

        self.add_item(container)

    def get_title(self) -> str:
        return f"Buying stats for {self.itr.user.display_name}"
