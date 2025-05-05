import logging
import math
import re
import discord
from items import Item, ItemEmbed, ItemList
from spells import Spell, SpellEmbed, SpellList
from rapidfuzz import fuzz


def __search_matches(query: str, name: str, threshold: float) -> bool:
    query = query.lower()
    name = name.lower()

    return fuzz.partial_ratio(query, name) > threshold


def search_from_query_try_exact(
    query: str, options: list[Spell | Item], threshold=75.0, ignore_phb=False
):
    query = query.strip.lower()

    exact = []
    fuzzy = []

    for option in options:
        if ignore_phb and option.is_phb2014:
            continue

        name = option.name.strip().lower()
        if name == query:
            exact.append(option)
        elif fuzz.ratio(query, name) > threshold:
            fuzzy.append(option)

    if len(exact) > 0:
        return exact
    return fuzzy


def search_from_query(
    query: str,
    spell_list: SpellList,
    item_list: ItemList,
    threshold=75.0,
    ignore_phb2014=False,
):
    query = query.strip.lower()
    spells: list[Spell] = []
    items: list[Item] = []

    for spell in spell_list.spells:
        if ignore_phb2014 and spell.is_phb2014:
            continue
        if __search_matches(query, spell.name, threshold):
            spells.append(spell)

    for item in item_list.items:
        if ignore_phb2014 and item.is_phb2014:
            continue
        if __search_matches(query, item.name, threshold):
            items.append(item)

    return spells, items


class Emoji:
    fire = "🔥"
    dagger = "🗡️"


class SearchSelectOption(discord.SelectOption):
    def __init__(self, data: Item | Spell):
        label = ""
        description = None
        if isinstance(data, Spell):
            label = f"{Emoji.fire} {data.name} ({data.source})"
            description = f"{data.level} {data.school}"

        elif isinstance(data, Item):
            label = f"{Emoji.dagger} {data.name} ({data.source})"

        super().__init__(label=label, description=description)


class SearchSelect(discord.ui.Select):
    spells: list[Spell]
    items: list[Item]

    def __init__(self, query: str, spells: list[Spell], items: list[Item]) -> None:
        self.spells = spells
        self.items = items

        options = []
        for spell in spells:
            options.append(SearchSelectOption(spell))

        for item in items:
            options.append(SearchSelectOption(item))

        options = sorted(options, key=lambda o: o.label)
        super().__init__(
            placeholder=f"Top results for '{query}'",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        """Handles the selection of a spell from the select menu."""
        value = self.values[0]
        name_pattern = r"^([^ ]*?) (.+) \(([^\)]+)\)"  # "Emoji Name (Source)"
        name_match = re.match(name_pattern, value)
        type = name_match.group(1)
        name = name_match.group(2)
        source = name_match.group(3)

        user_name = interaction.user.display_name
        logging.debug(f"SearchEmbed: user {user_name} selected '{name}")

        if type == Emoji.fire:
            spell = [
                spell
                for spell in self.spells
                if spell.name == name and spell.source == source
            ][0]
            await interaction.response.send_message(embed=SpellEmbed(spell))

        elif type == Emoji.dagger:
            item = [
                item
                for item in self.items
                if item.name == name and item.source == source
            ][0]
            await interaction.response.send_message(embed=ItemEmbed(item))


class SearchSelectView(discord.ui.View):
    """A class representing a Discord view for multiple spell selection."""

    def __init__(self, query: str, spells: list[Spell], items: list[Item]):
        super().__init__()
        self.add_item(SearchSelect(query, spells, items))


class SearchActionView(discord.ui.View):
    embed: any
    buttons: list[discord.ui.Button]
    select: SearchSelect
    query: str

    def __init__(self, query: str, embed: any, *, timeout=300):
        super().__init__(timeout=timeout)

        self.embed = embed
        self.query = query
        self.buttons = []
        style = discord.ButtonStyle.primary

        # Go back to first page button
        button = discord.ui.Button(label="↞", style=style)
        button.callback = lambda i: self.embed.go_to_first_page(i)
        self.buttons.append(button)
        self.add_item(button)

        # Go to previous page button
        button = discord.ui.Button(label="←", style=style)
        button.callback = lambda i: self.embed.go_to_prev_page(i)
        self.buttons.append(button)
        self.add_item(button)

        # Go to next page button
        button = discord.ui.Button(label="→", style=style)
        button.callback = lambda i: self.embed.go_to_next_page(i)
        self.buttons.append(button)
        self.add_item(button)

        # Go to last page button
        button = discord.ui.Button(label="↠", style=style)
        button.callback = lambda i: self.embed.go_to_last_page(i)
        self.buttons.append(button)
        self.add_item(button)

        self.select = None

    def update(
        self, page: int, max_pages: int, spells: list[Spell], items: list[Item]
    ) -> None:
        if len(self.buttons) == 0:
            return

        self.remove_item(self.select)
        self.select = SearchSelect(self.query, spells, items)
        self.add_item(self.select)

        # Disable buttons based on which page we are on
        for button in self.buttons:
            button.disabled = False
        if page == 0:
            self.buttons[0].disabled = True
            self.buttons[1].disabled = True
        if page == max_pages - 1:
            self.buttons[2].disabled = True
            self.buttons[3].disabled = True


class SearchEmbed(discord.Embed):
    per_page: int = 10

    page: int
    items: list[Item]
    spells: list[Spell]

    view: SearchActionView

    def __init__(self, query: str, spells: list[Spell], items: list[Item]) -> None:
        self.page = 0
        self.items = sorted(items, key=lambda i: (i.name, i.source))
        self.spells = sorted(spells, key=lambda s: (s.name, s.source))

        title = f"Results for '{query}'"
        url = f"https://5e.tools/search.html?q={query}"
        url = url.replace(" ", "%20")

        super().__init__(
            color=discord.Color.dark_green(),
            title=title,
            type="rich",
            url=url,
            description=None,
            timestamp=None,
        )

        self.view = SearchActionView(query, self)
        self.build()

    @property
    def max_pages(self) -> int:
        return int(math.ceil((len(self.spells) + len(self.items)) / self.per_page))

    def get_current_options(self) -> tuple[list[Item], list[Spell]]:
        # Could be cleaner
        options = self.items + self.spells
        start = self.page * self.per_page
        end = (self.page + 1) * self.per_page
        options = options[start:end]
        items = [i for i in options if isinstance(i, Item)]
        spells = [s for s in options if isinstance(s, Spell)]
        return items, spells

    def build(self):
        self.clear_fields()
        items, spells = self.get_current_options()

        for item in items:
            option = SearchSelectOption(item)
            self.add_field(name="", value=option.label, inline=False)

        for spell in spells:
            option = SearchSelectOption(spell)
            self.add_field(name="", value=option.label, inline=False)

        self.add_field(
            name="",
            value="~~-------------------------------------------------------------------------------------~~",
            inline=False,
        )

        self.set_footer(text=f"Page {self.page + 1}/{self.max_pages}")
        self.view.update(self.page, self.max_pages, spells, items)

    async def rebuild(self, interaction: discord.Interaction):
        self.build()
        return await interaction.response.edit_message(embed=self, view=self.view)

    async def go_to_first_page(self, interaction: discord.Interaction):
        self.page = 0
        return await self.rebuild(interaction)

    async def go_to_prev_page(self, interaction: discord.Interaction):
        self.page = self.page - 1
        return await self.rebuild(interaction)

    async def go_to_next_page(self, interaction: discord.Interaction):
        self.page = self.page + 1
        return await self.rebuild(interaction)

    async def go_to_last_page(self, interaction: discord.Interaction):
        self.page = self.max_pages - 1
        return await self.rebuild(interaction)


class NoSearchResultsFoundEmbed(discord.Embed):
    """A class representing a Discord embed for when no results are found."""

    def __init__(self, query: str):
        super().__init__(
            color=discord.Color.dark_green(),
            title="No results found.",
            type="rich",
            url=None,
            description=None,
            timestamp=None,
        )
        self.add_field(name="", value=f"No results found for '{query}'.")
