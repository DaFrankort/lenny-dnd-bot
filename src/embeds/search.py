import logging
from typing import Sequence
import discord
from discord import ui
from components.items import SimpleSeparator, TitleTextDisplay
from components.paginated_view import PaginatedLayoutView
from embeds.dnd.action import ActionEmbed
from embeds.dnd.background import BackgroundEmbed
from embeds.dnd.class_ import ClassEmbed
from embeds.dnd.condition import ConditionEmbed
from embeds.dnd.creature import CreatureEmbed
from embeds.dnd.feat import FeatEmbed
from embeds.dnd.item import ItemEmbed
from embeds.dnd.language import LanguageEmbed
from embeds.dnd.rule import RuleEmbed
from embeds.dnd.species import SpeciesEmbed
from embeds.dnd.spell import SpellEmbed
from embeds.dnd.table import DNDTableContainerView
from embeds.dnd.vehicle import VehicleEmbed
from logic.dnd.abstract import DNDObject
from logic.dnd.action import Action
from logic.dnd.background import Background
from logic.dnd.class_ import Class
from logic.dnd.condition import Condition
from logic.dnd.creature import Creature
from logic.dnd.data import DNDSearchResults
from logic.dnd.feat import Feat
from logic.dnd.item import Item
from logic.dnd.language import Language
from logic.dnd.rule import Rule
from logic.dnd.species import Species
from logic.dnd.spell import Spell
from logic.dnd.table import DNDTable
from logic.dnd.vehicle import Vehicle


def get_dnd_embed(itr: discord.Interaction, dnd_object: DNDObject):
    match dnd_object:
        case Spell():
            return SpellEmbed(itr, dnd_object)
        case Item():
            return ItemEmbed(dnd_object)
        case Condition():
            return ConditionEmbed(dnd_object)
        case Creature():
            return CreatureEmbed(dnd_object)
        case Class():
            return ClassEmbed(dnd_object)
        case Rule():
            return RuleEmbed(dnd_object)
        case Action():
            return ActionEmbed(dnd_object)
        case Feat():
            return FeatEmbed(dnd_object)
        case Language():
            return LanguageEmbed(dnd_object)
        case Background():
            return BackgroundEmbed(dnd_object)
        case DNDTable():
            return DNDTableContainerView(dnd_object)
        case Species():
            return SpeciesEmbed(dnd_object)
        case Vehicle():
            return VehicleEmbed(dnd_object)
    logging.error(f"Could not find embed for class {dnd_object.__class__.__name__}")
    return None


async def send_dnd_embed(itr: discord.Interaction, dnd_object: DNDObject):
    await itr.response.defer(thinking=False)
    embed = get_dnd_embed(itr, dnd_object)
    if embed is None:
        await itr.followup.send(f"Could not create an embed for {dnd_object.name}...")
        return

    file = embed.file or discord.interactions.MISSING

    if isinstance(embed, discord.ui.LayoutView):
        await itr.followup.send(view=embed, file=file)
        return

    view = embed.view or discord.interactions.MISSING
    await itr.followup.send(embed=embed, view=view, file=file)


class SearchSelectButton(ui.Button):
    object: DNDObject

    def __init__(self, object: DNDObject):
        self.object = object
        label = f"{object.name} ({object.source})"
        if len(label) > 80:
            label = label[:77] + "..."
        super().__init__(label=label, emoji=object.emoji, style=discord.ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        await send_dnd_embed(interaction, self.object)


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


class MultiDNDSelect(discord.ui.Select):
    name: str
    query: str
    entries: Sequence[DNDObject]

    def __init__(self, query: str, entries: Sequence[DNDObject]):
        self.name = entries[0].__class__.__name__.upper() if entries else "UNKNOWN"
        self.query = query
        self.entries = entries

        options = []
        for entry in entries:
            options.append(self.select_option(entry))

        super().__init__(
            placeholder=f"Results for '{query}'",
            options=options,
            min_values=1,
            max_values=1,
        )

        logging.debug(f"{self.name}: found {len(entries)} entries for '{query}'")

    def select_option(self, entry: DNDObject) -> discord.SelectOption:
        index = self.entries.index(entry)
        return discord.SelectOption(
            label=f"{entry.name} ({entry.source})",
            description=entry.select_description,
            value=str(index),
        )

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        entry = self.entries[index]

        logging.debug(f"{self.name}: user {interaction.user.display_name} selected option {index}: '{entry.name}`")
        await send_dnd_embed(interaction, entry)


class MultiDNDSelectView(discord.ui.View):
    """A class representing a Discord view for multiple DNDObject selection."""

    def __init__(self, query: str, entries: Sequence[DNDObject]):
        super().__init__()
        self.add_item(MultiDNDSelect(query, entries))
