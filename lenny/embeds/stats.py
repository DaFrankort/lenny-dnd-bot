import discord

from embeds.components import (
    BaseLabelTextInput,
    BaseModal,
    BaseSeparator,
    TitleTextDisplay,
)
from embeds.embed import UserActionEmbed
from logic.color import UserColor
from logic.stats import BoughtStats, Stats, get_stat_mod


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
        self.label_button = discord.ui.Button(
            style=discord.ButtonStyle.gray, custom_id=f"{self.key}_btn", label=f"{key} | {stat} ({get_stat_mod(stat)})"
        )
        self.label_button.callback = self.open_modal
        self.label_button.disabled = not stats.can_add(key) and not stats.can_take(key)

        self.minus_button = discord.ui.Button(
            style=discord.ButtonStyle.red, label="-", custom_id=f"{self.key}_min_btn", disabled=not self.stats.can_take(key)
        )
        self.minus_button.callback = self.take_point

        self.plus_button = discord.ui.Button(
            style=discord.ButtonStyle.green,
            label="+",
            custom_id=f"{key}_plus_btn",
            disabled=not self.stats.can_add(key),
        )
        self.plus_button.callback = self.add_point

        self.add_item(self.minus_button)
        self.add_item(self.plus_button)
        self.add_item(self.label_button)

    async def add_point(self, interaction: discord.Interaction):
        if not self.stats.is_owner(interaction.user):
            await interaction.response.send_message("These stats don't belong to you!", ephemeral=True)
            return

        self.stats.add_score(self.key)
        await self.update_message(interaction)

    async def take_point(self, interaction: discord.Interaction):
        if not self.stats.is_owner(interaction.user):
            await interaction.response.send_message("These stats don't belong to you!", ephemeral=True)
            return

        self.stats.take_score(self.key)
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        view = BoughtStatsLayoutView(interaction, self.stats)
        await interaction.response.edit_message(view=view, attachments=[view.chart])

    async def open_modal(self, interaction: discord.Interaction):
        if not self.stats.is_owner(interaction.user):
            await interaction.response.send_message("These stats don't belong to you!", ephemeral=True)
            return
        await interaction.response.send_modal(PointBuyModal(interaction, self.key, self.stats))


class PointBuyModal(BaseModal):
    score = BaseLabelTextInput(label="Stat")

    def __init__(self, itr: discord.Interaction, key: str, stats: BoughtStats):
        self.stats = stats
        self.key = key

        super().__init__(itr=itr, title=f"Adjusting Ability score - {key}")
        current_score = stats.stats[key]
        self.score.default = str(current_score)

        valid = stats.viable_scores(key)
        self.min_score = min(valid)
        self.max_score = max(valid)

        self.score.placeholder = f"{self.min_score} - {self.max_score}"

    async def on_submit(self, interaction: discord.Interaction):
        score = self.get_int(self.score)
        if not score:
            raise ValueError("Score must be a numerical input!")

        score = max(self.min_score, min(score, self.max_score))
        current = self.stats.stats[self.key]

        while current < score:
            self.stats.add_score(self.key)
            current += 1

        while current > score:
            self.stats.take_score(self.key)
            current -= 1

        view = BoughtStatsLayoutView(interaction, self.stats)
        await interaction.response.edit_message(view=view, attachments=[view.chart])


class BoughtStatsLayoutView(discord.ui.LayoutView):
    itr: discord.Interaction
    stats: BoughtStats
    chart: discord.File

    def __init__(self, itr: discord.Interaction, stats: BoughtStats):
        self.itr = itr
        self.stats = stats
        color = UserColor.get(itr)
        self.chart = stats.get_radar_chart(color)

        title = self.get_title()

        super().__init__(timeout=60 * 60)

        container: discord.ui.Container[discord.ui.LayoutView] = discord.ui.Container(accent_color=color)

        container.add_item(TitleTextDisplay(name=title))
        container.add_item(discord.ui.TextDisplay(f"{stats.points} / {stats.max_points} Points left."))
        container.add_item(BaseSeparator())

        container.add_item(PointBuyActionRow("STR", stats))
        container.add_item(PointBuyActionRow("DEX", stats))
        container.add_item(PointBuyActionRow("CON", stats))
        container.add_item(PointBuyActionRow("INT", stats))
        container.add_item(PointBuyActionRow("WIS", stats))
        container.add_item(PointBuyActionRow("CHA", stats))
        container.add_item(discord.ui.TextDisplay("-# *Scores 14 and 15 cost two points"))

        container.add_item(BaseSeparator())
        container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(self.chart)))

        self.add_item(container)

    def get_title(self) -> str:
        return f"Buying stats for {self.itr.user.display_name}"
