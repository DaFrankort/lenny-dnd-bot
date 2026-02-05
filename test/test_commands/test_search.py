from typing import Awaitable, Callable

import discord
import pytest
from mocking import MockInteraction

from commands.search import (
    action_name_autocomplete,
    background_name_autocomplete,
    boon_name_autocomplete,
    class_name_autocomplete,
    condition_name_autocomplete,
    creature_name_autocomplete,
    cult_name_autocomplete,
    feat_name_autocomplete,
    hazard_name_autocomplete,
    item_name_autocomplete,
    language_name_autocomplete,
    object_name_autocomplete,
    rule_name_autocomplete,
    species_name_autocomplete,
    spell_name_autocomplete,
    subclass_name_lookup,
    table_name_autocomplete,
    vehicle_name_autocomplete,
)
from logic.config import Config
from logic.dnd.abstract import DNDEntry
from logic.dnd.data import Data
from logic.searchcache import SearchCache

AutocompleteMethod = Callable[[discord.Interaction, str], Awaitable[list[discord.app_commands.Choice[str]]]]


class TestSearch:
    @pytest.fixture()
    def itr(self):
        return MockInteraction()

    @pytest.mark.parametrize(
        "class_name, query, contains",
        [
            ("Wizard", "Illusion", True),
            ("Wizard", "DoesNotExist", False),
            ("Barbarian", "Wild Heart", True),
            ("DoesNotExist", "Evoker", False),
        ],
    )
    def test_subclass_lookup(self, itr: discord.Interaction, class_name: str, query: str, contains: bool):
        sources = Config.get(itr).allowed_sources

        subclasses = subclass_name_lookup(class_name, query, sources)
        if contains:
            assert len(subclasses) > 0, f"Class {class_name} expected to have '{query}' as a subclass."
        else:
            assert len(subclasses) == 0, f"Class {class_name} did not expect '{query}' as a subclass."

    @pytest.mark.parametrize(
        "entry, autocomplete_method",
        [
            (Data.spells.entries[0], spell_name_autocomplete),
            (Data.items.entries[0], item_name_autocomplete),
            (Data.conditions.entries[0], condition_name_autocomplete),
            (Data.creatures.entries[0], creature_name_autocomplete),
            (Data.classes.entries[0], class_name_autocomplete),
            (Data.rules.entries[0], rule_name_autocomplete),
            (Data.actions.entries[0], action_name_autocomplete),
            (Data.feats.entries[0], feat_name_autocomplete),
            (Data.languages.entries[0], language_name_autocomplete),
            (Data.backgrounds.entries[0], background_name_autocomplete),
            (Data.tables.entries[0], table_name_autocomplete),
            (Data.species.entries[0], species_name_autocomplete),
            (Data.vehicles.entries[0], vehicle_name_autocomplete),
            (Data.objects.entries[0], object_name_autocomplete),
            (Data.hazards.entries[0], hazard_name_autocomplete),
            (Data.cults.entries[0], cult_name_autocomplete),
            (Data.boons.entries[0], boon_name_autocomplete),
        ],
    )
    async def test_autocompletes(self, itr: discord.Interaction, entry: DNDEntry, autocomplete_method: AutocompleteMethod):
        SearchCache.get(itr).store(entry)

        choices = await autocomplete_method(itr, "")
        assert (
            choices[0].name == entry.name
        ), f"SearchCache {entry.entry_type}-autocomplete should be '{entry.name}', instead was '{choices[0].value}'"
