import discord

from embeds.components import TitleTextDisplay
from logic.average import AverageDamageResultsBase
from logic.color import UserColor


class AverageDamageLayoutView(discord.ui.LayoutView):
    results: AverageDamageResultsBase
    color: int
    show_table: bool

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

        if self.show_table:
            container.add_item(discord.ui.TextDisplay(self.results.table))

        btn_label = "Hide result table" if self.show_table else "Show result table"
        toggle_button = discord.ui.Button(label=btn_label, style=discord.ButtonStyle.secondary)  # type: ignore
        toggle_button.callback = self.toggle_table
        container.add_item(discord.ui.ActionRow(toggle_button))  # type: ignore
        self.add_item(container)

    async def toggle_table(self, interaction: discord.Interaction):
        self.show_table = not self.show_table
        self.build()
        await interaction.response.edit_message(view=self)
