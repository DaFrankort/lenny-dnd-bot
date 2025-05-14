import pytest
from utils.mock_discord_interaction import MockInteraction, MockUser

from initiative import Initiative, InitiativeTracker


class TestInitiative:
    @pytest.mark.parametrize("mod", [5, -5, 0])
    def test_init_no_target(self, mod: int):
        itr = MockInteraction()
        initiative = Initiative(itr, mod, None)

        assert initiative.modifier == mod, f"Initative modifier `{initiative.modifier}` is not the same as the input modifier `{mod}`"
        assert initiative.is_npc is False, "Initiative without target should not be labeled as NPC."
        assert itr.user.display_name in initiative.name, "Initiative without target should have the user's name."

    @pytest.mark.parametrize(
        "mod, target",
        [
            (5, "Crab"),
            (-5, "Goblin"),
            (0, "Dragon"),
        ]
    )
    def test_init_with_target(self, mod: int, target: str):
        itr = MockInteraction()
        initiative = Initiative(itr, mod, target)

        assert initiative.modifier == mod, f"Initative modifier `{initiative.modifier}` is not the same as the input modifier `{mod}`"
        assert initiative.is_npc is True, "Initiative with target should be labeled as NPC."
        assert itr.user.display_name not in initiative.name, "Initiative with target should not have the user's name."
        assert target in initiative.name, "Initiative with target should have target's name in the name."

    def test_roll(self):
        itr = MockInteraction()
        initiative = Initiative(itr, 0, None)
        for i in range(50):
            assert 1 <= initiative.d20 <= 20, f"Initiative d20 roll should be value between 1 or 20, was {initiative.d20}"

    @pytest.mark.parametrize("mod", [5, -5, 0])
    def test_get_total(self, mod: int):
        itr = MockInteraction()
        initiative = Initiative(itr, mod, None)
        expected = initiative.d20 + mod
        assert initiative.get_total() == expected, "Initiative total should equal random d20 value + modifier."


class TestInitiativeTracker:
    @pytest.fixture
    def tracker(self):
        return InitiativeTracker()

    @pytest.fixture
    def interaction(self):
        return MockInteraction()

    @pytest.fixture
    def npc_initiative(self, interaction):
        return Initiative(interaction, modifier=2, name="Goblin")

    @pytest.fixture
    def pc_initiative(self, interaction):
        return Initiative(interaction, modifier=1, name=None)

    def test_add_npc_initiative(self, tracker, interaction, npc_initiative):
        tracker.add(interaction, npc_initiative)
        result = tracker.get(interaction)
        assert len(result) == 1, f"Expected 1 initiative, got {len(result)}"
        assert result[0].name == npc_initiative.name, f"Expected initiative name '{npc_initiative.name}', got '{result[0].name}'"
        assert result[0].is_npc is True, "Expected initiative to be NPC (is_npc=True)"

    def test_add_pc_initiative_replaces_existing(self, tracker, interaction, pc_initiative):
        tracker.add(interaction, pc_initiative)

        new_pc = Initiative(interaction, modifier=5, name=None)
        new_pc.d20 = 20
        tracker.add(interaction, new_pc)

        result = tracker.get(interaction)
        assert len(result) == 1, f"Expected 1 initiative after replacement, got {len(result)}"
        assert result[0].modifier == 5, f"Expected modifier 5, got {result[0].modifier}"
        assert result[0].d20 == 20, f"Expected d20 value 20, got {result[0].d20}"

    def test_clear_initiatives(self, tracker, interaction, npc_initiative):
        tracker.add(interaction, npc_initiative)
        tracker.clear(interaction)
        assert tracker.get(interaction) == [], "Expected initiatives to be cleared (empty list)"

    def test_get_returns_empty_for_new_guild(self, tracker):
        fresh_interaction = MockInteraction(guild_id=555)
        assert tracker.get(fresh_interaction) == [], "Expected empty list for new guild"

    def test_multiple_guilds(self, tracker):
        itr1 = MockInteraction(guild_id=1)
        itr2 = MockInteraction(MockUser(456, "Bar"), guild_id=2)

        initiative1 = Initiative(itr1, modifier=1, name="Goblin")
        initiative2 = Initiative(itr2, modifier=3, name="Orc")

        tracker.add(itr1, initiative1)
        tracker.add(itr2, initiative2)

        assert len(tracker.get(itr1)) == 1, f"Expected 1 initiative for guild 1, got {len(tracker.get(itr1))}"
        assert len(tracker.get(itr2)) == 1, f"Expected 1 initiative for guild 2, got {len(tracker.get(itr2))}"
        assert tracker.get(itr1)[0].name == initiative1.name, f"Expected name '{initiative1.name}in' for guild 1, got '{tracker.get(itr1)[0].name}'"
        assert tracker.get(itr2)[0].name == initiative2.name, f"Expected name '{initiative2.name}' for guild 2, got '{tracker.get(itr2)[0].name}'"
