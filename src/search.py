import discord
from discord import ui
from rapidfuzz import fuzz
from components.items import SimpleSeparator, TitleTextDisplay
from dnd import (
    DNDData,
    DNDSearchResults,
    DNDObject,
    send_dnd_embed,
)
from ui.paginated_view import PaginatedLayoutView


class SearchSelectButton(ui.Button):
    object: DNDObject

    def __init__(self, object: DNDObject):
        self.object = object
        label = f"{object.name} ({object.source})"
        if len(label) > 80:
            label = label[:77] + "..."
        super().__init__(
            label=label, emoji=object.emoji, style=discord.ButtonStyle.gray
        )

    async def callback(self, itr: discord.Interaction):
        await send_dnd_embed(itr, self.object)


class SearchLayoutView(PaginatedLayoutView):
    results: DNDSearchResults

    container: ui.Container
    title_item: TitleTextDisplay

    def __init__(self, query: str, results: DNDSearchResults):
        self.page = 0
        self.results = results

        super().__init__()

        title = f"{len(results.get_all())} Results for '{query}'"
        url = f"https://5e.tools/search.html?q={query}"
        url = url.replace(" ", "%20")
        self.title_item = TitleTextDisplay(name=title, url=url)
        self.build()

    @property
    def entry_count(self) -> int:
        return len(self.results)

    def get_current_options(self):
        start = self.page * self.per_page
        end = (self.page + 1) * self.per_page
        return self.results.get_all_sorted()[start:end]

    def build(self):
        self.clear_items()
        container = ui.Container(accent_color=discord.Color.dark_green())

        # HEADER
        container.add_item(self.title_item)
        container.add_item(SimpleSeparator())

        # CONTENT
        options = self.get_current_options()
        for option in options:
            container.add_item(ui.ActionRow(SearchSelectButton(option)))

        # FOOTER
        container.add_item(SimpleSeparator())
        container.add_item(self.navigation_footer())

        self.add_item(container)
