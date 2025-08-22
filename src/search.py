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


# class SearchSelectOption(discord.SelectOption):
#     def __init__(self, data: DNDObject):
#         label = f"{data.emoji} {data.name} ({data.source})"
#         super().__init__(label=label, description=data.select_description)


# class SearchSelect(ui.Select):
#     results: list[DNDObject]

#     def __init__(
#         self,
#         query: str,
#         results: list[DNDObject],
#     ) -> None:
#         self.results = results

#         options = []
#         for entry in self.results:
#             options.append(SearchSelectOption(entry))

#         options = sorted(options, key=lambda o: o.label)
#         super().__init__(
#             placeholder=f"Top results for '{query}'",
#             options=options,
#             min_values=1,
#             max_values=1,
#         )

#     async def callback(self, itr: discord.Interaction):
#         """Handles the selection of a spell from the select menu."""
#         value = self.values[0]
#         name_pattern = r"^([^ ]*?) (.+) \(([^\)]+)\)"  # "Emoji Name (Source)"
#         name_match = re.match(name_pattern, value)
#         name = name_match.group(2)
#         source = name_match.group(3)

#         user_name = itr.user.display_name
#         logging.debug(f"SearchEmbed: user {user_name} selected '{name}")

#         result = [r for r in self.results if r.name == name and r.source == source][0]
#         await send_dnd_embed(itr, result)


# class SearchActionView(ui.View):
#     embed: any
#     buttons: list[ui.Button]
#     select: SearchSelect
#     query: str

#     def __init__(self, query: str, embed: any, *, timeout=300):
#         super().__init__(timeout=timeout)

#         self.embed = embed
#         self.query = query
#         self.buttons = []
#         style = discord.ButtonStyle.primary

#         # Go back to first page button
#         button = ui.Button(label="↞", style=style)
#         button.callback = lambda i: self.embed.go_to_first_page(i)
#         self.buttons.append(button)
#         self.add_item(button)

#         # Go to previous page button
#         button = ui.Button(label="←", style=style)
#         button.callback = lambda i: self.embed.go_to_prev_page(i)
#         self.buttons.append(button)
#         self.add_item(button)

#         # Go to next page button
#         button = ui.Button(label="→", style=style)
#         button.callback = lambda i: self.embed.go_to_next_page(i)
#         self.buttons.append(button)
#         self.add_item(button)

#         # Go to last page button
#         button = ui.Button(label="↠", style=style)
#         button.callback = lambda i: self.embed.go_to_last_page(i)
#         self.buttons.append(button)
#         self.add_item(button)

#         self.select = None

#     def update(
#         self,
#         page: int,
#         max_pages: int,
#         results: list[DNDObject],
#     ) -> None:
#         if len(self.buttons) == 0:
#             return

#         self.remove_item(self.select)
#         self.select = SearchSelect(self.query, results)
#         self.add_item(self.select)

#         # Disable buttons based on which page we are on
#         for button in self.buttons:
#             button.disabled = False
#         if page == 0:
#             self.buttons[0].disabled = True
#             self.buttons[1].disabled = True
#         if page == max_pages - 1:
#             self.buttons[2].disabled = True
#             self.buttons[3].disabled = True


# class SearchEmbed(discord.Embed):
#     per_page: int = 10

#     page: int
#     results: DNDSearchResults

#     view: SearchActionView

#     def __init__(self, query: str, results: DNDSearchResults) -> None:
#         self.page = 0
#         self.results = results

#         title = f"Results for '{query}'"
#         url = f"https://5e.tools/search.html?q={query}"
#         url = url.replace(" ", "%20")

#         super().__init__(
#             color=discord.Color.dark_green(),
#             title=title,
#             type="rich",
#             url=url,
#             description=None,
#             timestamp=None,
#         )

#         self.view = SearchActionView(query, self)
#         self.build()

#     @property
#     def max_pages(self) -> int:
#         return int(math.ceil(len(self.results) / self.per_page))

#     def get_current_options(self):
#         start = self.page * self.per_page
#         end = (self.page + 1) * self.per_page
#         return self.results.get_all_sorted()[start:end]

#     def build(self):
#         self.clear_fields()

#         options = self.get_current_options()
#         for option in options:
#             self.add_field(
#                 name="", value=SearchSelectOption(option).label, inline=False
#             )

#         self.add_field(
#             name="",
#             value="~~-------------------------------------------------------------------------------------~~",
#             inline=False,
#         )

#         self.set_footer(text=f"Page {self.page + 1}/{self.max_pages}")
#         self.view.update(self.page, self.max_pages, options)

#     async def rebuild(self, itr: discord.Interaction):
#         self.build()
#         return await itr.response.edit_message(embed=self, view=self.view)

#     async def go_to_first_page(self, itr: discord.Interaction):
#         self.page = 0
#         return await self.rebuild(itr)

#     async def go_to_prev_page(self, itr: discord.Interaction):
#         self.page = self.page - 1
#         return await self.rebuild(itr)

#     async def go_to_next_page(self, itr: discord.Interaction):
#         self.page = self.page + 1
#         return await self.rebuild(itr)

#     async def go_to_last_page(self, itr: discord.Interaction):
#         self.page = self.max_pages - 1
#         return await self.rebuild(itr)


# NEW


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
    per_page: int = 10

    page: int
    results: DNDSearchResults

    container: ui.Container
    title_item: TitleTextDisplay

    def __init__(self, query: str, results: DNDSearchResults):
        self.page = 0
        self.results = results

        super().__init__(timeout=None)

        self.container = ui.Container(accent_color=discord.Color.dark_green())
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
        self.container.clear_items()

        # HEADER
        self.container.add_item(self.title_item)
        self.container.add_item(SimpleSeparator())

        # CONTENT
        options = self.get_current_options()
        for option in options:
            self.container.add_item(ui.ActionRow(SearchSelectButton(option)))

        # FOOTER
        self.container.add_item(SimpleSeparator())
        # TODO ADD PAGINATION
        self.container.add_item(
            ui.TextDisplay(f"-# Page {self.page + 1}/{self.max_pages}")
        )

        self.add_item(self.container)

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
