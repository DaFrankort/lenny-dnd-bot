import discord

from embeds.components import TitleTextDisplay
from logic.average import AverageDamageResultsBase
from logic.color import UserColor
from logic.roll import Advantage


class AverageDamageLayoutView(discord.ui.LayoutView):
    results: AverageDamageResultsBase
    color: int
    show_table: bool
    advantages_select: discord.ui.Select[discord.ui.LayoutView]

    def __init__(self, itr: discord.Interaction, results: AverageDamageResultsBase):
        self.results = results
        self.color = UserColor.get(itr)
        self.show_table = False
        super().__init__()
        self.build()

    def build(self):
        self.clear_items()
        container: discord.ui.Container[discord.ui.LayoutView] = discord.ui.Container(accent_color=self.color)

        container.add_item(TitleTextDisplay(self.results.title))
        container.add_item(discord.ui.TextDisplay(self.results.details))
        container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"attachment://{self.results.chart.filename}"))
        )

        options: list[discord.SelectOption] = []
        for option in Advantage.options():
            option.default = option.value in self.results.advantages
            options.append(option)
        self.advantages_select = discord.ui.Select(placeholder="Advantages", max_values=len(options), options=options)
        self.advantages_select.callback = self.on_advantage_change
        container.add_item(discord.ui.ActionRow(self.advantages_select))

        if self.show_table:
            container.add_item(discord.ui.TextDisplay(self.results.table))
            container.add_item(discord.ui.File(f"attachment://{self.results.csv.filename}"))

        btn_label = "Hide result table" if self.show_table else "Show result table"
        toggle_button = discord.ui.Button(label=btn_label, style=discord.ButtonStyle.secondary)  # type: ignore
        toggle_button.callback = self.toggle_table
        container.add_item(discord.ui.ActionRow(toggle_button))  # type: ignore
        self.add_item(container)

    async def toggle_table(self, interaction: discord.Interaction):
        self.show_table = not self.show_table
        self.build()
        await interaction.response.edit_message(view=self)

    async def on_advantage_change(self, interaction: discord.Interaction):
        self.results.advantages = [Advantage(val) for val in self.advantages_select.values]
        await interaction.response.defer()
        self.results.chart = self.results.generate_chart()
        self.results.csv = self.results.generate_csv()
        self.results.table = self.results.generate_table()
        self.build()
        await interaction.edit_original_response(view=self, attachments=[self.results.chart, self.results.csv])
