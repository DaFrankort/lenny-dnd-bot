import collections.abc
import logging

import discord
from discord.app_commands import autocomplete, describe

from commands.command import SimpleCommand, SimpleCommandGroup
from embeds.embed import NoResultsFoundEmbed
from embeds.search import MultiDNDSelectView, SearchLayoutView, send_dnd_embed
from logic.config import Config
from logic.dnd.abstract import TDND, DNDEntry, DNDEntryList
from logic.dnd.data import Data
from logic.searchcache import SearchCache


async def send_dnd_entry_lookup_result(
    itr: discord.Interaction,
    label: str,
    found: collections.abc.Sequence[DNDEntry],
    name: str,
):
    """Helper function to send generic D&D lookup embeds and views."""
    logging.debug("%s: Found %d for '%s'", label.upper(), len(found), len(found))

    if len(found) == 0:
        embed = NoResultsFoundEmbed(label, name)
        await itr.response.send_message(embed=embed, ephemeral=True)

    elif len(found) > 1:
        view = MultiDNDSelectView(name, found)
        await itr.response.send_message(view=view, ephemeral=True)

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


class SearchSpellCommand(SimpleCommand):
    name = "spell"
    desc = "Get the details for a spell."
    help = "Looks up a spell by name."

    @autocomplete(name=spell_name_autocomplete)
    @describe(name="Name of the spell to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.spells.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "spells", found, name)


async def item_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.items, "item")


class SearchItemCommand(SimpleCommand):
    name = "item"
    desc = "Get the details for an item."
    help = "Looks up an item by name."

    @autocomplete(name=item_name_autocomplete)
    @describe(name="Name of the item to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.items.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "items", found, name)


async def condition_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.conditions, "condition")


class SearchConditionCommand(SimpleCommand):
    name = "condition"
    desc = "Get the details of a condition or status effect."
    help = "Looks up a condition or status effect by name."

    @autocomplete(name=condition_name_autocomplete)
    @describe(name="Name of the condition to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.conditions.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "conditions", found, name)


async def creature_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.creatures, "creature")


class SearchCreatureCommand(SimpleCommand):
    name = "creature"
    desc = "Get the details of a creature."
    help = "Looks up a creature by name."

    @autocomplete(name=creature_name_autocomplete)
    @describe(name="Name of the creature to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.creatures.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "creatures", found, name)


async def class_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.classes, "class")


class SearchClassCommand(SimpleCommand):
    name = "class"
    desc = "Get the details for a character class."
    help = "Looks up a D&D class by name."

    @autocomplete(name=class_name_autocomplete)
    @describe(name="Name of the class to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.classes.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "classes", found, name)


async def rule_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.rules, "rule")


class SearchRuleCommand(SimpleCommand):
    name = "rule"
    desc = "Get the details of a D&D rule."
    help = "Looks up a D&D rule by name."

    @autocomplete(name=rule_name_autocomplete)
    @describe(name="Name of the rule to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.rules.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "rules", found, name)


async def action_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.actions, "action")


class SearchActionCommand(SimpleCommand):
    name = "action"
    desc = "Get the details of a D&D action."
    help = "Looks up a D&D action by name."

    @autocomplete(name=action_name_autocomplete)
    @describe(name="Name of the action to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.actions.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "actions", found, name)


async def feat_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.feats, "feat")


class SearchFeatCommand(SimpleCommand):
    name = "feat"
    desc = "Get the details of a character feat."
    help = "Looks up a character feat by name."

    @autocomplete(name=feat_name_autocomplete)
    @describe(name="Name of the feat to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.feats.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "feats", found, name)


async def language_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.languages, "language")


class SearchLanguageCommand(SimpleCommand):
    name = "language"
    desc = "Get the details of a language."
    help = "Looks up a D&D Language by name."

    @autocomplete(name=language_name_autocomplete)
    @describe(name="Name of the language to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.languages.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "languages", found, name)


async def background_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.backgrounds, "background")


class SearchBackgroundCommand(SimpleCommand):
    name = "background"
    desc = "Get the details of a background."
    help = "Looks up a D&D Background by name."

    @autocomplete(name=background_name_autocomplete)
    @describe(name="Name of the background to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.backgrounds.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "background", found, name)


async def table_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.tables, "table")


class SearchTableCommand(SimpleCommand):
    name = "table"
    desc = "Get the details of a table."
    help = "Looks up a D&D Table by name."

    @autocomplete(name=table_name_autocomplete)
    @describe(name="Name of the table to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.tables.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "table", found, name)


async def species_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.species, "species")


class SearchSpeciesCommand(SimpleCommand):
    name = "species"
    desc = "Get the details of a species."
    help = "Looks up a D&D Species by name."

    @autocomplete(name=species_name_autocomplete)
    @describe(name="Name of the species to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.species.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "species", found, name)


async def vehicle_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.vehicles, "vehicle")


class SearchVehicleCommand(SimpleCommand):
    name = "vehicle"
    desc = "Get the details of a vehicle."
    help = "Looks up a D&D Vehicle by name."

    @autocomplete(name=vehicle_name_autocomplete)
    @describe(name="Name of the vehicle to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.vehicles.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "vehicle", found, name)


async def object_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.objects, "object")


class SearchObjectCommand(SimpleCommand):
    name = "object"
    desc = "Get the details of an object."
    help = "Looks up a D&D Object by name."

    @autocomplete(name=object_name_autocomplete)
    @describe(name="Name of the object to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.objects.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "object", found, name)


async def hazard_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.hazards, "hazard")


class SearchHazardCommand(SimpleCommand):
    name = "hazard"
    desc = "Get the details of a trap or hazard."
    help = "Looks up a D&D Trap or Hazard by name."

    @autocomplete(name=hazard_name_autocomplete)
    @describe(name="Name of the trap or hazard to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.hazards.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "hazard", found, name)


async def deity_name_autocomplete(itr: discord.Interaction, current: str):
    return _generic_name_autocomplete(itr, current, Data.deities, "deity")


class SearchDeityCommand(SimpleCommand):
    name = "deity"
    desc = "Get the details of a deity."
    help = "Looks up a D&D Deity by name."

    @autocomplete(name=deity_name_autocomplete)
    @describe(name="Name of the deity to look up.")
    async def handle(self, itr: discord.Interaction, name: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        found = Data.deities.get(name, sources)
        await send_dnd_entry_lookup_result(itr, "deity", found, name)


class SearchAnyCommand(SimpleCommand):
    name = "all"
    desc = "Search for all matching D&D entries."
    help = "Looks up all possible D&D entries for a query."

    @describe(query="Search for results matching this query.")
    async def handle(self, itr: discord.Interaction, query: str):
        self.log(itr)
        sources = Config.get(itr).allowed_sources
        results = Data.search(query, sources)
        logging.debug("Found %d results for '%s'", len(results.get_all()), query)

        if len(results.get_all()) == 0:
            embed = NoResultsFoundEmbed("results", query)
            await itr.response.send_message(embed=embed, ephemeral=True)
        else:
            view = SearchLayoutView(query, results)
            await itr.response.send_message(view=view, ephemeral=True)


class SearchCommandGroup(SimpleCommandGroup):
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
        self.add_command(SearchAnyCommand())
