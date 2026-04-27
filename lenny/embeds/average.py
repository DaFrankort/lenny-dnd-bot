import discord

from embeds.components import TitleTextDisplay
from logic.average import AverageDamageACResults, AverageDamageDCResults
from logic.color import UserColor
from logic.dnd.abstract import build_table_from_rows


class AverageDamageACLayoutView(discord.ui.LayoutView):
    results: AverageDamageACResults
    color: int
    show_table: bool

    def __init__(self, itr: discord.Interaction, results: AverageDamageACResults):
        self.results = results
        self.color = UserColor.get(itr)
        self.show_table = False
        super().__init__()

        self.build()

    def build(self):
        self.clear_items()
        container: discord.ui.Container[discord.ui.LayoutView] = discord.ui.Container(accent_color=self.color)

        container.add_item(TitleTextDisplay("Average Damage per Attack"))

        details = f"**Hit:** {self.results.hit}"
        details += f"\n**Damage:** {self.results.damage}"

        if self.results.miss_damage != "0":
            details += f"\n**Miss damage:** {self.results.miss_damage}"
        if self.results.crit_min < 20:
            details += f"\n**Critical range:** {self.results.crit_min}-20"
        container.add_item(discord.ui.TextDisplay(details))

        container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media="attachment://" + self.results.chart.filename))  # type: ignore
        )

        if self.show_table:
            container.add_item(discord.ui.TextDisplay(self._get_table()))

        btn_label = "Hide result table" if self.show_table else "Show result table"
        toggle_button = discord.ui.Button(label=btn_label, style=discord.ButtonStyle.secondary, custom_id="table_toggle_btn")  # type: ignore
        toggle_button.callback = self.toggle_table
        container.add_item(discord.ui.ActionRow(toggle_button))  # type: ignore

        self.add_item(container)

    def _get_table(self) -> str:
        acs = self.results.acs
        advantages = self.results.advantages

        headers = ["AC", *[str(adv).capitalize() for adv in advantages]]
        rows = [(str(ac), *[self.results.get(ac, adv) for adv in advantages]) for ac in acs]

        return build_table_from_rows(headers, rows, align_right=True)

    async def toggle_table(self, interaction: discord.Interaction):
        self.show_table = not self.show_table
        self.build()
        await interaction.response.edit_message(view=self)


# TODO create 'abstract' AverageDamageLayoutView due to similar behaviour.
class AverageDamageDCLayoutView(discord.ui.LayoutView):
    results: AverageDamageDCResults
    color: int
    show_table: bool

    def __init__(self, itr: discord.Interaction, results: AverageDamageDCResults):
        self.results = results
        self.color = UserColor.get(itr)
        self.show_table = False
        super().__init__()

        self.build()

    def build(self):
        self.clear_items()
        container: discord.ui.Container[discord.ui.LayoutView] = discord.ui.Container(accent_color=self.color)

        container.add_item(TitleTextDisplay("Average Damage per Attack"))

        details = f"**DC:** {self.results.dc}"
        details += f"\n**Damage:** {self.results.damage}"
        if self.results.miss_damage != "0":
            details += f"\n**Miss damage:** {self.results.miss_damage}"
        container.add_item(discord.ui.TextDisplay(details))

        container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media="attachment://" + self.results.chart.filename))  # type: ignore
        )

        if self.show_table:
            container.add_item(discord.ui.TextDisplay(self._get_table()))

        btn_label = "Hide result table" if self.show_table else "Show result table"
        toggle_button = discord.ui.Button(label=btn_label, style=discord.ButtonStyle.secondary, custom_id="table_toggle_btn")  # type: ignore
        toggle_button.callback = self.toggle_table
        container.add_item(discord.ui.ActionRow(toggle_button))  # type: ignore

        self.add_item(container)

    def _get_table(self) -> str:
        mods = self.results.mods
        advantages = self.results.advantages

        headers = ["Mod", *[str(adv).capitalize() for adv in advantages]]
        rows = [(str(mod), *[self.results.get(mod, adv) for adv in advantages]) for mod in mods]

        return build_table_from_rows(headers, rows, align_right=True)

    async def toggle_table(self, interaction: discord.Interaction):
        self.show_table = not self.show_table
        self.build()
        await interaction.response.edit_message(view=self)
