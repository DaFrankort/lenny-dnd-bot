import os

import pytest
from discord import Interaction
from mocking import MockInteraction

from logic.dnd.abstract import DNDEntryType
from logic.homebrew import HOMEBREW_PATH, GlobalHomebrewData


class TestHomebrew:
    @pytest.fixture(autouse=True)
    def setup_cleanup(self, itr: Interaction):
        os.makedirs(HOMEBREW_PATH, exist_ok=True)
        file_path = os.path.join(HOMEBREW_PATH, f"{itr.guild_id}.json")

        if os.path.exists(file_path):
            os.remove(file_path)

        yield

        if os.path.exists(file_path):
            os.remove(file_path)

    @pytest.fixture()
    def data(self) -> GlobalHomebrewData:
        return GlobalHomebrewData()

    @pytest.fixture
    def itr(self):
        return MockInteraction()

    def test_add_guild(self, itr: Interaction, data: GlobalHomebrewData):
        guild_data = data.get(itr)
        assert guild_data is not None
        assert itr.guild_id in data.keys

    def test_add_homebrew_entry(self, itr: Interaction, data: GlobalHomebrewData):
        guild_data = data.get(itr)
        entry = guild_data.add(itr, DNDEntryType.SPELL, "Fireball", None, "A powerful fire spell", "Deals 8d6 fire damage")
        assert entry.name == "Fireball"
        assert entry.entry_type == DNDEntryType.SPELL

    def test_get_homebrew_entry(self, itr: Interaction, data: GlobalHomebrewData):
        guild_data = data.get(itr)
        guild_data.add(itr, DNDEntryType.SPELL, "Ice Bolt", None, "A cold spell", "Deals 4d6 cold damage")

        entry = guild_data.get("Ice Bolt")
        assert entry.name == "Ice Bolt"
        assert entry.description == "Deals 4d6 cold damage"

    def test_delete_homebrew_entry(self, itr: Interaction, data: GlobalHomebrewData):
        guild_data = data.get(itr)
        guild_data.add(itr, DNDEntryType.SPELL, "Lightning", None, "An electric spell", "Deals 6d6 lightning damage")

        deleted_entry = guild_data.delete(itr, "Lightning")
        assert deleted_entry.name == "Lightning"

        with pytest.raises(ValueError):
            guild_data.get("Lightning")

    def test_edit_homebrew_entry(self, itr: Interaction, data: GlobalHomebrewData):
        guild_data = data.get(itr)
        original = guild_data.add(itr, DNDEntryType.SPELL, "Magic", None, "Old description", "Old details")

        edited = guild_data.edit(itr, original, "Updated Magic", None, "New description", "New details")

        assert edited.name == "Updated Magic"
        assert edited.select_description == "New description"
        assert edited.description == "New details"

    def test_duplicate_name_raises_error(self, itr: Interaction, data: GlobalHomebrewData):
        guild_data = data.get(itr)
        guild_data.add(itr, DNDEntryType.SPELL, "Duplicate", None, "desc", "details")

        with pytest.raises(ValueError):
            guild_data.add(itr, DNDEntryType.SPELL, "Duplicate", None, "desc", "details")

    def test_get_all_entries(self, itr: Interaction, data: GlobalHomebrewData):
        guild_data = data.get(itr)
        guild_data.data = {DNDEntryType.SPELL: [], DNDEntryType.ITEM: []}  # Reset entries
        guild_data.add(itr, DNDEntryType.SPELL, "Spell1", None, "d1", "desc1")
        guild_data.add(itr, DNDEntryType.ITEM, "Item1", None, "d2", "desc2")

        all_entries = guild_data.get_all(None)
        expected_count = len(guild_data.data.get(DNDEntryType.SPELL, [])) + len(guild_data.data.get(DNDEntryType.ITEM, []))
        assert len(all_entries) == expected_count

        spell_entries = guild_data.get_all(DNDEntryType.SPELL)
        assert len(spell_entries) == 1
        assert spell_entries[0].name == "Spell1"

    def test_add_faulty_url(self, itr: Interaction, data: GlobalHomebrewData):
        guild_data = data.get(itr)
        entry_type = DNDEntryType.RULE
        guild_data.data = {entry_type: []}  # Reset entries
        guild_data.add(itr, entry_type=entry_type, name="NotUrl", url="NotAUrl", description="Desc", select_description="Sub")
        guild_data.add(
            itr, entry_type=entry_type, name="FaultyLink", url="ww.faulty.link", description="Desc", select_description="Sub"
        )

        all_entries = guild_data.get_all(entry_type)
        for entry in all_entries:
            assert entry.url is None, f"Invalid URL was added to Homebrew data: '{entry.url}'"

    def test_edit_faulty_url(self, itr: Interaction, data: GlobalHomebrewData):
        guild_data = data.get(itr)
        valid_url = "www.google.com"
        invalid_url = "NoLongerValid!"
        original = guild_data.add(itr, DNDEntryType.RULE, "Name", None, valid_url, "desc")
        edited = guild_data.edit(itr, original, "Name", None, invalid_url, "desc")

        assert edited.url != invalid_url, f"Invalid URL was edited into Homebrew Entry: `{valid_url}` -> `{invalid_url}`"
