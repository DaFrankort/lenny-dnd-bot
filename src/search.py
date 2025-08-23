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
from modals import SimpleModal


def __search_matches(query: str, name: str, threshold: float) -> bool:
    query = query.lower()
    name = name.lower()

    return fuzz.partial_ratio(query, name) > threshold


def search_from_query(
    query: str,
    data: DNDData,
    allowed_sources: set[str],
    threshold=75.0,
):
    query = query.strip().lower()
    results = DNDSearchResults()

    for data_list in data:
        for entry in data_list.entries:
            if entry.source not in allowed_sources:
                continue
            if __search_matches(query, entry.name, threshold):
                results.add(entry)

    return results


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


class SearchPageJumpModal(SimpleModal):
    page: ui.TextInput
    view: ui.LayoutView

    def __init__(self, itr: discord.Interaction, view: ui.LayoutView):
        super().__init__(itr=itr, title="Jump pages")
        self.view = view
        current_page = str(self.view.page + 1)
        self.page = ui.TextInput(
            label=f"Jump to page (1 - {self.view.max_pages})",
            placeholder=current_page,
            min_length=1,
            max_length=len(str(self.view.max_pages)),
        )
        self.add_item(self.page)


class SearchLayoutView(ui.LayoutView):
    per_page: int = 10

    page: int
    results: DNDSearchResults

    container: ui.Container
    title_item: TitleTextDisplay
    modal: SearchPageJumpModal = None

    def __init__(self, query: str, results: DNDSearchResults):
        self.page = 0
        self.results = results

        super().__init__(timeout=None)

        title = f"{len(results.get_all())} Results for '{query}'"
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
        if self.max_pages > 1:
            container.add_item(SimpleSeparator())
            disable_back = self.page == 0
            disable_next = self.page >= self.max_pages - 1
            style = discord.ButtonStyle.primary

            button_first_page = ui.Button(label="↞", style=style)
            button_first_page.callback = lambda itr: self.go_to_first_page(itr)
            button_first_page.disabled = disable_back

            button_prev_page = ui.Button(label="←", style=style)
            button_prev_page.callback = lambda itr: self.go_to_prev_page(itr)
            button_prev_page.disabled = disable_back

            current_page = f"Page {self.page + 1} / {self.max_pages}"
            button_current_page = ui.Button(
                label=current_page, style=discord.ButtonStyle.gray
            )
            button_current_page.callback = lambda itr: self.jump_to_page_sendmodal(itr)

            button_next_page = ui.Button(label="→", style=style)
            button_next_page.callback = lambda itr: self.go_to_next_page(itr)
            button_next_page.disabled = disable_next

            button_last_page = ui.Button(label="↠", style=style)
            button_last_page.callback = lambda itr: self.go_to_last_page(itr)
            button_last_page.disabled = disable_next

            container.add_item(
                ui.ActionRow(
                    button_first_page,
                    button_prev_page,
                    button_current_page,
                    button_next_page,
                    button_last_page,
                )
            )

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

    async def jump_to_page_sendmodal(self, itr: discord.Interaction):
        self.modal = SearchPageJumpModal(itr, self)
        self.modal.on_submit = lambda i: self.jump_to_page(i)
        await itr.response.send_modal(self.modal)

    async def jump_to_page(self, itr: discord.Interaction):
        page = self.modal.get_int(self.modal.page)

        if page is None:
            error_message = "❌ Page must be a positive numerical value! ❌"
            await itr.response.send_message(error_message, ephemeral=True)
            return

        page -= 1  # First page === 0
        page = min(max(page, 0), self.max_pages - 1)
        self.page = page
        return await self.rebuild(itr)

    async def go_to_next_page(self, itr: discord.Interaction):
        self.page = self.page + 1
        return await self.rebuild(itr)

    async def go_to_last_page(self, itr: discord.Interaction):
        self.page = self.max_pages - 1
        return await self.rebuild(itr)
