import math
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


def __search_matches(query: str, name: str, threshold: float) -> bool:
    query = query.lower()
    name = name.lower()

    return fuzz.partial_ratio(query, name) > threshold


def search_from_query(
    query: str,
    data: DNDData,
    threshold=75.0,
    ignore_phb2014=True,
):
    query = query.strip().lower()
    results = DNDSearchResults()

    for data_list in data:
        for entry in data_list.entries:
            if ignore_phb2014 and getattr(entry, "is_phb2014", False):
                continue
            if __search_matches(query, entry.name, threshold):
                results.add(entry)

    return results


class SearchSelectButton(ui.Button):
    object: DNDObject

    def __init__(self, object: DNDObject):
        self.object = object
        label = f"{object.name} ({object.source})"
        super().__init__(
            label=label, emoji=object.emoji, style=discord.ButtonStyle.gray
        )

    async def callback(self, itr: discord.Interaction):
        await send_dnd_embed(itr, self.object)


class SearchLayoutView(ui.LayoutView):
    per_page: int = 10  # TODO Fix per_page to be 10 again

    page: int
    results: DNDSearchResults

    container: ui.Container
    title_item: TitleTextDisplay

    def __init__(self, query: str, results: DNDSearchResults):
        self.page = 0
        self.results = results

        super().__init__(timeout=None)

        title = f"Results for '{query}'"
        url = f"https://5e.tools/search.html?q={query}"
        url = url.replace(" ", "%20")
        self.title_item = TitleTextDisplay(name=title, url=url)
        self.build()

    @property
    def max_pages(self) -> int:
        return int(math.ceil(len(self.results) / self.per_page))

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

        if self.max_pages > 1:
            disable_back = self.page == 0
            disable_next = self.page >= self.max_pages - 1

            button_first_page = ui.Button(label="↞", style=discord.ButtonStyle.primary)
            button_first_page.callback = lambda i: self.go_to_first_page(i)
            button_first_page.disabled = disable_back

            button_prev_page = ui.Button(label="←", style=discord.ButtonStyle.primary)
            button_prev_page.callback = lambda i: self.go_to_prev_page(i)
            button_prev_page.disabled = disable_back

            button_next_page = ui.Button(label="→", style=discord.ButtonStyle.primary)
            button_next_page.callback = lambda i: self.go_to_next_page(i)
            button_next_page.disabled = disable_next

            button_last_page = ui.Button(label="↠", style=discord.ButtonStyle.primary)
            button_last_page.callback = lambda i: self.go_to_last_page(i)
            button_last_page.disabled = disable_next

            container.add_item(
                ui.ActionRow(
                    button_first_page,
                    button_prev_page,
                    button_next_page,
                    button_last_page,
                )
            )

        container.add_item(ui.TextDisplay(f"-# Page {self.page + 1}/{self.max_pages}"))

        self.add_item(container)

    async def rebuild(self, itr: discord.Interaction):
        self.build()
        return await itr.response.edit_message(view=self)

    async def go_to_first_page(self, itr: discord.Interaction):
        self.page = 0
        return await self.rebuild(itr)

    async def go_to_prev_page(self, itr: discord.Interaction):
        self.page = self.page - 1
        return await self.rebuild(itr)

    async def go_to_next_page(self, itr: discord.Interaction):
        self.page = self.page + 1
        return await self.rebuild(itr)

    async def go_to_last_page(self, itr: discord.Interaction):
        self.page = self.max_pages - 1
        return await self.rebuild(itr)
