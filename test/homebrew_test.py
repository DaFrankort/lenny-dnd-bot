import pytest
import os
from utils.mocking import MockInteraction
from logic.homebrew import DNDHomebrewData, DNDObjectType, HOMEBREW_PATH


class TestHomebrew:
    _test_data = None

    @pytest.fixture(autouse=True)
    def setup_cleanup(self, itr):
        os.makedirs(HOMEBREW_PATH, exist_ok=True)
        file_path = os.path.join(HOMEBREW_PATH, f"{itr.guild_id}.json")

        if os.path.exists(file_path):
            os.remove(file_path)

        yield

        if os.path.exists(file_path):
            os.remove(file_path)

    @pytest.fixture()
    def test_data(self):
        if not self._test_data:
            self._test_data = DNDHomebrewData()
        return self._test_data

    @pytest.fixture
    def itr(self):
        return MockInteraction()

    def test_add_server(self, itr, test_data):
        guild_data = test_data.get(itr)
        assert guild_data is not None
        assert itr.guild_id in test_data._data.keys()

    def test_add_homebrew_entry(self, itr, test_data):
        guild_data = test_data.get(itr)
        entry = guild_data.add(itr, DNDObjectType.SPELL.value, "Fireball", "A powerful fire spell", "Deals 8d6 fire damage")
        assert entry.name == "Fireball"
        assert entry.object_type == DNDObjectType.SPELL

    def test_get_homebrew_entry(self, itr, test_data):
        guild_data = test_data.get(itr)
        guild_data.add(itr, DNDObjectType.SPELL.value, "Ice Bolt", "A cold spell", "Deals 4d6 cold damage")

        entry = guild_data.get("Ice Bolt")
        assert entry.name == "Ice Bolt"
        assert entry.description == "Deals 4d6 cold damage"

    def test_delete_homebrew_entry(self, itr, test_data):
        guild_data = test_data.get(itr)
        guild_data.add(itr, DNDObjectType.SPELL.value, "Lightning", "An electric spell", "Deals 6d6 lightning damage")

        deleted_entry = guild_data.delete(itr, "Lightning")
        assert deleted_entry.name == "Lightning"

        with pytest.raises(ValueError):
            guild_data.get("Lightning")

    def test_edit_homebrew_entry(self, itr, test_data):
        guild_data = test_data.get(itr)
        original = guild_data.add(itr, DNDObjectType.SPELL.value, "Magic", "Old description", "Old details")

        edited = guild_data.edit(itr, original, "Updated Magic", "New description", "New details")

        assert edited.name == "Updated Magic"
        assert edited.select_description == "New description"
        assert edited.description == "New details"

    def test_duplicate_name_raises_error(self, itr, test_data):
        guild_data = test_data.get(itr)
        guild_data.add(itr, DNDObjectType.SPELL.value, "Duplicate", "desc", "details")

        with pytest.raises(ValueError):
            guild_data.add(itr, DNDObjectType.SPELL.value, "Duplicate", "desc", "details")

    def test_get_all_entries(self, itr, test_data):
        guild_data = test_data.get(itr)
        guild_data.entries = {DNDObjectType.SPELL.value: [], DNDObjectType.ITEM.value: []}  # Reset entries
        guild_data.add(itr, DNDObjectType.SPELL.value, "Spell1", "d1", "desc1")
        guild_data.add(itr, DNDObjectType.ITEM.value, "Item1", "d2", "desc2")

        all_entries = guild_data.get_all(None)
        expected_count = len(guild_data.entries.get(DNDObjectType.SPELL.value, [])) + len(
            guild_data.entries.get(DNDObjectType.ITEM.value, [])
        )
        assert len(all_entries) == expected_count

        spell_entries = guild_data.get_all(DNDObjectType.SPELL.value)
        assert len(spell_entries) == 1
        assert spell_entries[0].name == "Spell1"
