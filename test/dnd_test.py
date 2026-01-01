import pytest
from utils.mocking import MockInteraction
from utils.utils import AutocompleteMethod

from commands.search import (
    action_name_autocomplete,
    background_name_autocomplete,
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
    table_name_autocomplete,
    vehicle_name_autocomplete,
)
from embeds.search import MultiDNDSelectView
from logic.config import Config
from logic.dnd.abstract import DNDEntry, fuzzy_matches
from logic.dnd.data import Data
from logic.searchcache import SearchCache


class TestDndData:
    queries: list[str] = [
        "fireball",
        "dagger",
        "poisoned",
        "goblin",
        "initiative",
        "attack",
        "tough",
        "ABCDF",
    ]

    def test_dnddatalist_search(self):
        itr = MockInteraction()
        config = Config.get(itr)
        sources = config.allowed_sources
        for query in self.queries:
            for data in Data:
                try:
                    data.search(query, allowed_sources=sources)
                except Exception:
                    assert False, f"{data.entries[0].entry_type} DNDDataList failed search()"

    def test_search_from_query(self):
        itr = MockInteraction()
        config = Config.get(itr)
        sources = config.allowed_sources
        for query in self.queries:
            try:
                Data.search(query, allowed_sources=sources)
            except Exception:
                assert False, "search_from_query threw an error."

    @pytest.mark.asyncio
    async def test_multidndselect(self):
        itr = MockInteraction()
        config = Config.get(itr)
        sources = config.allowed_sources
        name = "pot of awakening"
        entries = Data.items.get(name, sources)
        assert len(entries) >= 2, "Test requires at least 2 items, please update test data."
        try:
            MultiDNDSelectView(name, entries)
        except Exception as e:
            pytest.fail(f"MultiDNDSelectView failed to initialize: {e}")

    @pytest.mark.parametrize(
        "query, value, result",
        [
            ("fire bolt", "fireball", True),
            ("fire bolt", "ray of sickness", False),
            ("ray", "aura", True),
        ],
    )
    def test_fuzzy(self, query: str, value: str, result: bool):
        fuzzy = fuzzy_matches(query, value, fuzzy_threshold=75)
        assert (fuzzy is not None) == result


class TestSearchCache:
    @pytest.mark.asyncio
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
        ],
    )
    async def test_autocompletes(self, entry: DNDEntry, autocomplete_method: AutocompleteMethod):
        itr = MockInteraction()
        SearchCache.get(itr).store(entry)

        choices = await autocomplete_method(itr, "")
        assert (
            choices[0].name == entry.name
        ), f"SearchCache {entry.entry_type}-autocomplete should be '{entry.name}', instead was '{choices[0].value}'"
