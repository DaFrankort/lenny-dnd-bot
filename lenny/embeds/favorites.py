import discord

from embeds.components import BaseSeparator, PaginatedLayoutView, TitleTextDisplay
from embeds.embed import BaseEmbed
from embeds.search import send_dnd_embed
from logic.dnd.abstract import DNDEntry
from logic.dnd.data import Data


class FavoriteSelectButton(discord.ui.Button["FavoritesLayoutView"]):
    entry: DNDEntry | None
    name: str
    source: str

    def __init__(self, name: str):
        self.name, self.source = name.rsplit("(", 1)
        self.name = self.name.strip()
        self.source = self.source.replace(")", "").strip()

        self.entry = None
        entries = Data.search(self.name, set([self.source]), 95).get_all()

        if len(entries) > 0:
            self.entry = entries[0]

        bracket_source = f"({self.source})"
        label = f"{self.name} {bracket_source}"
        if len(label) > 80:
            cutoff_symbol = "..."
            new_size = 80 - (len(cutoff_symbol) + len(bracket_source))
            label = label[:new_size] + cutoff_symbol

        emoji: str = "❓" if self.entry is None else self.entry.entry_type.emoji
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.gray, disabled=self.entry is None)

    async def callback(self, interaction: discord.Interaction):
        if self.entry is None:
            raise KeyError("Sorry! This entry is no longer available.")
        await send_dnd_embed(interaction, self.entry)


class FavoritesLayoutView(PaginatedLayoutView):
    favorites: list[str]

    container: discord.ui.Container["FavoritesLayoutView"]
    title_item: TitleTextDisplay

    def __init__(self, favorites: list[str]):
        self.page = 0
        self.favorites = favorites

        super().__init__()

        self.title_item = TitleTextDisplay(name="Favorites")
        self.build()

    @property
    def entry_count(self) -> int:
        return len(self.favorites)

    def get_current_options(self):
        start = self.page * self.per_page
        end = (self.page + 1) * self.per_page
        return self.favorites[start:end]

    def build(self):
        self.clear_items()
        container = discord.ui.Container[FavoritesLayoutView](accent_color=discord.Color.dark_green())

        # HEADER
        container.add_item(self.title_item)
        container.add_item(BaseSeparator())

        # CONTENT
        if len(self.favorites) == 0:
            container.add_item(discord.ui.TextDisplay("*No favorites found!*"))
        else:
            for option in self.get_current_options():
                container.add_item(discord.ui.ActionRow(FavoriteSelectButton(option)))

        # FOOTER
        if self.entry_count > self.per_page:
            container.add_item(BaseSeparator())
            container.add_item(self.navigation_footer())

        self.add_item(container)


class FavoriteAddedEmbed(BaseEmbed):
    def __init__(self, entry: DNDEntry):
        super().__init__(title="Added favorite", description=f"``{entry.title}`` was **added** to your favorites.")
