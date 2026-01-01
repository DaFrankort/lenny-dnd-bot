import logging
from collections.abc import Sequence

import discord
from discord import ui

from components.items import SimpleSeparator, TitleTextDisplay
from components.paginated_view import PaginatedLayoutView
from embeds.dnd.action import ActionEmbed
from embeds.dnd.background import BackgroundEmbed
from embeds.dnd.boons import BoonEmbed
from embeds.dnd.class_ import ClassEmbed
from embeds.dnd.condition import ConditionEmbed
from embeds.dnd.creature import CreatureEmbed
from embeds.dnd.cult import CultEmbed
from embeds.dnd.deities import DeityEmbed
from embeds.dnd.feat import FeatEmbed
from embeds.dnd.hazard import HazardEmbed
from embeds.dnd.item import ItemEmbed
from embeds.dnd.language import LanguageEmbed
from embeds.dnd.object import DNDObjectEmbed
from embeds.dnd.rule import RuleEmbed
from embeds.dnd.species import SpeciesEmbed
from embeds.dnd.spell import SpellEmbed
from embeds.dnd.table import DNDTableContainerView
from embeds.dnd.vehicle import VehicleEmbed
from logic.config import Config
from logic.dnd.abstract import DNDEntry
from logic.dnd.action import Action
from logic.dnd.background import Background
from logic.dnd.boon import Boon
from logic.dnd.class_ import Class
from logic.dnd.condition import Condition
from logic.dnd.creature import Creature
from logic.dnd.cults import Cult
from logic.dnd.data import DNDSearchResults
from logic.dnd.deities import Deity
from logic.dnd.feat import Feat
from logic.dnd.hazard import Hazard
from logic.dnd.item import Item
from logic.dnd.language import Language
from logic.dnd.object import DNDObject
from logic.dnd.rule import Rule
from logic.dnd.species import Species
from logic.dnd.spell import Spell
from logic.dnd.table import DNDTable
from logic.dnd.vehicle import Vehicle
from logic.searchcache import SearchCache


def get_dnd_embed(itr: discord.Interaction, dnd_entry: DNDEntry):  # pylint: disable=too-many-return-statements
    match dnd_entry:
        case Spell():
            return SpellEmbed(itr, dnd_entry)
        case Item():
            return ItemEmbed(dnd_entry)
        case Condition():
            return ConditionEmbed(dnd_entry)
        case Creature():
            return CreatureEmbed(dnd_entry)
        case Class():
            sources = Config.get(itr).allowed_sources
            return ClassEmbed(dnd_entry, allowed_sources=sources)
        case Rule():
            return RuleEmbed(dnd_entry)
        case Action():
            return ActionEmbed(dnd_entry)
        case Feat():
            return FeatEmbed(dnd_entry)
        case Language():
            return LanguageEmbed(dnd_entry)
        case Background():
            return BackgroundEmbed(dnd_entry)
        case DNDTable():
            return DNDTableContainerView(dnd_entry)
        case Species():
            return SpeciesEmbed(dnd_entry)
        case Vehicle():
            return VehicleEmbed(dnd_entry)
        case DNDObject():
            return DNDObjectEmbed(dnd_entry)
        case Hazard():
            return HazardEmbed(dnd_entry)
        case Deity():
            return DeityEmbed(dnd_entry)
        case Cult():
            return CultEmbed(dnd_entry)
        case Boon():
            return BoonEmbed(dnd_entry)
        case _:
            raise LookupError(f"D&D entry '{type(DNDEntry).__name__}' not supported")


async def send_dnd_embed(itr: discord.Interaction, dnd_entry: DNDEntry):
    await itr.response.defer(thinking=False)
    embed = get_dnd_embed(itr, dnd_entry)
    file = embed.file or discord.interactions.MISSING

    if isinstance(embed, discord.ui.LayoutView):
        await itr.followup.send(view=embed, file=file)
        return

    view = embed.view or discord.interactions.MISSING
    await itr.followup.send(embed=embed, view=view, file=file)


class SearchSelectButton(ui.Button["SearchLayoutView"]):
    entry: DNDEntry

    def __init__(self, entry: DNDEntry):
        self.entry = entry
        label = f"{entry.name} ({entry.source})"
        if len(label) > 80:
            label = label[:77] + "..."
        super().__init__(label=label, emoji=entry.emoji, style=discord.ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        await send_dnd_embed(interaction, self.entry)


class SearchLayoutView(PaginatedLayoutView):
    results: DNDSearchResults

    container: ui.Container["SearchLayoutView"]
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
        container = ui.Container[SearchLayoutView](accent_color=discord.Color.dark_green())

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


class MultiDNDSelect(discord.ui.Select["MultiDNDSelectView"]):
    name: str
    query: str
    entries: Sequence[DNDEntry]

    def __init__(self, query: str, entries: Sequence[DNDEntry]):
        self.name = entries[0].__class__.__name__.upper() if entries else "UNKNOWN"
        self.query = query
        self.entries = entries

        options: list[discord.SelectOption] = []
        for entry in entries:
            options.append(self.select_option(entry))

        super().__init__(
            placeholder=f"Results for '{query}'",
            options=options,
            min_values=1,
            max_values=1,
        )

        logging.debug("%s: found %d entries for '%s'", self.name, len(entries), query)

    def select_option(self, entry: DNDEntry) -> discord.SelectOption:
        index = self.entries.index(entry)
        return discord.SelectOption(
            label=f"{entry.name} ({entry.source})",
            description=entry.select_description,
            value=str(index),
        )

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        entry = self.entries[index]

        logging.debug("%s: user %s selected option %d: '%s`", self.name, interaction.user.display_name, index, entry.name)
        SearchCache.get(interaction).store(entry)
        await send_dnd_embed(interaction, entry)


class MultiDNDSelectView(discord.ui.View):
    """A class representing a Discord view for multiple DNDObject selection."""

    def __init__(self, query: str, entries: Sequence[DNDEntry]):
        super().__init__()
        self.add_item(MultiDNDSelect(query, entries))
