import collections.abc
import logging

import discord
from discord.app_commands import autocomplete, describe

from commands.command import BaseCommand, BaseCommandGroup
from embeds.dnd.class_ import ClassEmbed
from embeds.embed import NoResultsFoundEmbed
from embeds.search import MultiDNDSelectView, SearchLayoutView, send_dnd_embed
from logic.config import Config
from logic.dnd.abstract import (
    TDND,
    DNDEntry,
    DNDEntryList,
    fuzzy_matches_list,
    get_command_option,
)
from logic.dnd.data import Data
from logic.searchcache import SearchCache


async def send_no_results_found_embed(itr: discord.Interaction, label: str, name: str):
    embed = NoResultsFoundEmbed(label, name)
    await itr.response.send_message(embed=embed, ephemeral=True)


async def send_multi_results_found_embed(itr: discord.Interaction, found: collections.abc.Sequence[DNDEntry], name: str):
    view = MultiDNDSelectView(name, found)
    await itr.response.send_message(view=view, ephemeral=True)


async def send_dnd_entry_lookup_result(
    itr: discord.Interaction,
    label: str,
    found: collections.abc.Sequence[DNDEntry],
    name: str,
):
    """Helper function to send generic D&D lookup embeds and views."""
    logging.debug("%s: Found %d for '%s'", label.upper(), len(found), len(found))

    if len(found) == 0:
        await send_no_results_found_embed(itr, label, name)

    elif len(found) > 1:
        await send_multi_results_found_embed(itr, found, name)

    else:
        SearchCache.get(itr).store(found[0])
        await send_dnd_embed(itr, found[0])


def _generic_name_autocomplete(
    itr: discord.Interaction, current: str, data: DNDEntryList[TDND], name: str
) -> list[discord.app_commands.Choice[str]]:
    sources = Config.get(itr).allowed_sources
    if not current.strip():
        return SearchCache.get(itr).get_choices(name)
    return data.get_autocomplete_suggestions(current, sources)


async def spell_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.spells, "spell")


class SearchSpellCommand(BaseCommand):
    name = "spell"
    desc = "Get the details for a spell."
    help = "Looks up a spell by name."

    @autocomplete(name=spell_name_autocomplete)
    @describe(name="Name of the spell to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.spells.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "spells", found, name)


async def item_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.items, "item")


class SearchItemCommand(BaseCommand):
    name = "item"
    desc = "Get the details for an item."
    help = "Looks up an item by name."

    @autocomplete(name=item_name_autocomplete)
    @describe(name="Name of the item to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.items.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "items", found, name)


async def condition_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.conditions, "condition")


class SearchConditionCommand(BaseCommand):
    name = "condition"
    desc = "Get the details of a condition or status effect."
    help = "Looks up a condition or status effect by name."

    @autocomplete(name=condition_name_autocomplete)
    @describe(name="Name of the condition to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.conditions.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "conditions", found, name)


async def creature_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.creatures, "creature")


class SearchCreatureCommand(BaseCommand):
    name = "creature"
    desc = "Get the details of a creature."
    help = "Looks up a creature by name."

    @autocomplete(name=creature_name_autocomplete)
    @describe(name="Name of the creature to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.creatures.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "creatures", found, name)


async def class_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.classes, "class")


def subclass_name_lookup(class_name: str, query: str, sources: set[str]) -> list[discord.app_commands.Choice[str]]:
    classes = Data.classes.get(class_name, sources, 100)  # require exact match

    # Need exactly one class to match, otherwise things might get confusing
    if len(classes) != 1:
        return []

    subclasses = classes[0].subclasses
    filtered = fuzzy_matches_list(query, subclasses, match_if_empty=True)
    return [subclass.choice for subclass in filtered]


async def subclass_name_autocomplete(itr: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    class_name = get_command_option(itr, "name")

    if not isinstance(class_name, str):
        raise TypeError(f"Subclass' parent class needs to be a string, received '{class_name}' ({type(class_name)}) instead.")

    sources = Config.get(itr).allowed_sources
    return subclass_name_lookup(class_name, current, sources)


class SearchClassCommand(BaseCommand):
    name = "class"
    desc = "Get the details for a character class."
    help = "Looks up a D&D class by name."

    @autocomplete(
        name=class_name_autocomplete,
        subclass=subclass_name_autocomplete,
    )
    @describe(
        name="Name of the class to look up.",
        subclass="The subclass of the class.",
        level="The level of the class.",
    )
    async def handle(
        self,
        itr: discord.Interaction,
        name: str,
        subclass: str | None = None,
        level: discord.app_commands.Range[int, 0, 20] = 0,
    ):
        sources = Config.get(itr).allowed_sources
        found = Data.classes.get(name, sources)

        # Code based on send_dnd_entry_lookup_result
        if len(found) == 0:
            await send_no_results_found_embed(itr, "classes", name)

        elif len(found) > 1:
            await send_multi_results_found_embed(itr, found, name)

        else:
            await itr.response.defer(thinking=False)
            SearchCache.get(itr).store(found[0])
            embed = ClassEmbed(found[0], sources, level, subclass)
            view = embed.view or discord.interactions.MISSING
            await itr.followup.send(embed=embed, view=view)


async def rule_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.rules, "rule")


class SearchRuleCommand(BaseCommand):
    name = "rule"
    desc = "Get the details of a D&D rule."
    help = "Looks up a D&D rule by name."

    @autocomplete(name=rule_name_autocomplete)
    @describe(name="Name of the rule to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.rules.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "rules", found, name)


async def action_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.actions, "action")


class SearchActionCommand(BaseCommand):
    name = "action"
    desc = "Get the details of a D&D action."
    help = "Looks up a D&D action by name."

    @autocomplete(name=action_name_autocomplete)
    @describe(name="Name of the action to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.actions.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "actions", found, name)


async def feat_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.feats, "feat")


class SearchFeatCommand(BaseCommand):
    name = "feat"
    desc = "Get the details of a character feat."
    help = "Looks up a character feat by name."

    @autocomplete(name=feat_name_autocomplete)
    @describe(name="Name of the feat to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.feats.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "feats", found, name)


async def language_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.languages, "language")


class SearchLanguageCommand(BaseCommand):
    name = "language"
    desc = "Get the details of a language."
    help = "Looks up a D&D Language by name."

    @autocomplete(name=language_name_autocomplete)
    @describe(name="Name of the language to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.languages.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "languages", found, name)


async def background_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.backgrounds, "background")


class SearchBackgroundCommand(BaseCommand):
    name = "background"
    desc = "Get the details of a background."
    help = "Looks up a D&D Background by name."

    @autocomplete(name=background_name_autocomplete)
    @describe(name="Name of the background to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.backgrounds.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "background", found, name)


async def table_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.tables, "table")


class SearchTableCommand(BaseCommand):
    name = "table"
    desc = "Get the details of a table."
    help = "Looks up a D&D Table by name."

    @autocomplete(name=table_name_autocomplete)
    @describe(name="Name of the table to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.tables.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "table", found, name)


async def species_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.species, "species")


class SearchSpeciesCommand(BaseCommand):
    name = "species"
    desc = "Get the details of a species."
    help = "Looks up a D&D Species by name."

    @autocomplete(name=species_name_autocomplete)
    @describe(name="Name of the species to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.species.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "species", found, name)


async def vehicle_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.vehicles, "vehicle")


class SearchVehicleCommand(BaseCommand):
    name = "vehicle"
    desc = "Get the details of a vehicle."
    help = "Looks up a D&D Vehicle by name."

    @autocomplete(name=vehicle_name_autocomplete)
    @describe(name="Name of the vehicle to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.vehicles.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "vehicle", found, name)


async def object_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.objects, "object")


class SearchObjectCommand(BaseCommand):
    name = "object"
    desc = "Get the details of an object."
    help = "Looks up a D&D Object by name."

    @autocomplete(name=object_name_autocomplete)
    @describe(name="Name of the object to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.objects.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "object", found, name)


async def hazard_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.hazards, "hazard")


class SearchHazardCommand(BaseCommand):
    name = "hazard"
    desc = "Get the details of a trap or hazard."
    help = "Looks up a D&D Trap or Hazard by name."

    @autocomplete(name=hazard_name_autocomplete)
    @describe(name="Name of the trap or hazard to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.hazards.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "hazard", found, name)


async def deity_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.deities, "deity")


class SearchDeityCommand(BaseCommand):
    name = "deity"
    desc = "Get the details of a deity."
    help = "Looks up a D&D Deity by name."

    @autocomplete(name=deity_name_autocomplete)
    @describe(name="Name of the deity to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.deities.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "deity", found, name)


async def cult_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.cults, "cult")


class SearchCultCommand(BaseCommand):
    name = "cult"
    desc = "Get the details of a cult."
    help = "Looks up a D&D cult by name."

    @autocomplete(name=cult_name_autocomplete)
    @describe(name="Name of the cult to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.cults.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "cult", found, name)


async def boon_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.boons, "boon")


class SearchBoonCommand(BaseCommand):
    name = "boon"
    desc = "Get the details of a boon."
    help = "Looks up a D&D boon by name."

    @autocomplete(name=boon_name_autocomplete)
    @describe(name="Name of the boon to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        sources = Config.get(itr).allowed_sources
        found = Data.boons.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "boon", found, name)


class SearchAnyCommand(BaseCommand):
    name = "all"
    desc = "Search for all matching D&D entries."
    help = "Looks up all possible D&D entries for a query."

    @describe(query="Search for results matching this query.")
    async def handle(self, itr: discord.Interaction, query: str):
        sources = Config.get(itr).allowed_sources
        results = Data.search(query, sources)
        logging.debug("Found %d results for '%s'", len(results.get_all()), query)

        if len(results.get_all()) == 0:
            embed = NoResultsFoundEmbed("results", query)
            await itr.response.send_message(embed=embed, ephemeral=True)
        else:
            view = SearchLayoutView(query, results)
            await itr.response.send_message(view=view, ephemeral=True)


class SearchCommandGroup(BaseCommandGroup):
    name = "search"
    desc = "Search for a D&D entry."

    def __init__(self):
        super().__init__()
        self.add_command(SearchSpellCommand())
        self.add_command(SearchItemCommand())
        self.add_command(SearchConditionCommand())
        self.add_command(SearchCreatureCommand())
        self.add_command(SearchClassCommand())
        self.add_command(SearchRuleCommand())
        self.add_command(SearchActionCommand())
        self.add_command(SearchFeatCommand())
        self.add_command(SearchLanguageCommand())
        self.add_command(SearchBackgroundCommand())
        self.add_command(SearchTableCommand())
        self.add_command(SearchSpeciesCommand())
        self.add_command(SearchVehicleCommand())
        self.add_command(SearchObjectCommand())
        self.add_command(SearchHazardCommand())
        self.add_command(SearchDeityCommand())
        self.add_command(SearchCultCommand())
        self.add_command(SearchBoonCommand())
        self.add_command(SearchAnyCommand())
