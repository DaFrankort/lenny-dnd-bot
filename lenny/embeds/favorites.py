import discord

from components.items import BaseSeparator, TitleTextDisplay
from components.paginated_view import PaginatedLayoutView


class FavoritesLayoutView(PaginatedLayoutView):
    favorites: list[str]

    container: discord.ui.Container["FavoritesLayoutView"]
    title_item: TitleTextDisplay

    def __init__(self, favorites: list[str]):
        self.page = 0
        self.favorites = favorites

        super().__init__()

        title = "Your favorites!"
        self.title_item = TitleTextDisplay(name=title)
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
        for option in self.get_current_options():
            container.add_item(discord.ui.TextDisplay(f"- {option}"))

        # FOOTER
        if self.entry_count > self.per_page:
            container.add_item(BaseSeparator())
            container.add_item(self.navigation_footer())

        self.add_item(container)
