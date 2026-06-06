import pytest
from mocking import MockInteraction

from logic.config import Config
from logic.dnd.abstract import fuzzy_matches
from logic.dnd.data import Data
from logic.dnd.table import DNDTable


class TestDNDData:
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

    def test_name_table_species_input_gives_species_name(self):
        species_list = Data.names.get_species()
        for species in species_list:
            _, new_species, _ = Data.names.get_random(species, None)
            assert new_species, "Namegen - Returned species must not be None"
            assert new_species.lower() == species.lower(), "Namegen - Returned Species must match input species"

    @pytest.mark.strict
    @pytest.mark.parametrize("table", [t for t in Data.tables.entries if t.is_rollable])
    def test_rollable_table_rows(self, table: DNDTable):
        for row in table.table["table"]["rows"]:
            for val in row:
                if isinstance(val, str):
                    continue

                elif val is None:
                    continue

                elif isinstance(val, int):
                    value = val

                else:
                    assert isinstance(
                        val["min"], int
                    ), f"Table '{table.name}' row-range minimum in {val} is not an integer, but is: {val['min']} (type: {type(val['min'])})"
                    assert isinstance(
                        val["max"], int
                    ), f"Table '{table.name}' row-range maximum in {val} is not an integer, but is: {val['max']} (type: {type(val['max'])})"

                    value = val["min"]

                table.get_rollable_row(value)
