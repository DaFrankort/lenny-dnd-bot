import pytest
from dice import DiceRollMode
from utils.mock_discord_interaction import MockInteraction, MockUser

from initiative import Initiative, InitiativeTracker


class TestInitiative:
    @pytest.mark.parametrize("mod", [5, -5, 0])
    def test_init_no_target(self, mod: int):
        itr = MockInteraction()
        initiative = Initiative(itr, mod, None, DiceRollMode.Normal)

        assert (
            initiative.modifier == mod
        ), f"Initative modifier `{initiative.modifier}` is not the same as the input modifier `{mod}`"
        assert (
            initiative.is_npc is False
        ), "Initiative without target should not be labeled as NPC."
        assert (
            itr.user.display_name in initiative.name
        ), "Initiative without target should have the user's name."

    @pytest.mark.parametrize(
        "mod, target",
        [
            (5, "Crab"),
            (-5, "Goblin"),
            (0, "Dragon"),
        ],
    )
    def test_init_with_target(self, mod: int, target: str):
        itr = MockInteraction()
        initiative = Initiative(itr, mod, target, DiceRollMode.Normal)

        assert (
            initiative.modifier == mod
        ), f"Initative modifier `{initiative.modifier}` is not the same as the input modifier `{mod}`"
        assert (
            initiative.is_npc is True
        ), "Initiative with target should be labeled as NPC."
        assert (
            itr.user.display_name not in initiative.name
        ), "Initiative with target should not have the user's name."
        assert (
            target in initiative.name
        ), "Initiative with target should have target's name in the name."

    def test_roll(self):
        itr = MockInteraction()
        for _ in range(50):
            initiative = Initiative(itr, 0, None, DiceRollMode.Normal)
            assert (
                1 <= initiative.d20[0] <= 20
            ), f"Initiative d20 roll should be value between 1 or 20, was {initiative.d20[0]}"
            assert (
                1 <= initiative.d20[1] <= 20
            ), f"Initiative d20 roll should be value between 1 or 20, was {initiative.d20[1]}"

    def test_roll_advantage(self):
        itr = MockInteraction()
        initiative = Initiative(itr, 0, None, DiceRollMode.Advantage)
        high = max(initiative.d20)

        expected = high + initiative.modifier
        total = initiative.get_total()
        assert (
            total == expected
        ), f"Initiative Advantage result expected {expected}, was {total}"

    def test_roll_disadvantage(self):
        itr = MockInteraction()
        initiative = Initiative(itr, 0, None, DiceRollMode.Disadvantage)
        low = min(initiative.d20)

        expected = low + initiative.modifier
        total = initiative.get_total()
        assert (
            total == expected
        ), f"Initiative Disadvantage result expected {expected}, was {total}"

    @pytest.mark.parametrize("mod", [5, -5, 0])
    def test_get_total(self, mod: int):
        itr = MockInteraction()
        initiative = Initiative(itr, mod, None, DiceRollMode.Normal)
        expected = initiative.d20[0] + mod
        assert (
            initiative.get_total() == expected
        ), "Initiative total should equal random d20 value + modifier."

    @pytest.mark.parametrize(
        "val, expected_d20, expected_modifier",
        [
            (25, 20, 5),  # 25 -> d20=20, modifier=5
            (-3, 1, -4),  # -3 -> d20=1, modifier=-2
            (10, 10, 0),  # 10 -> d20=10, modifier=0
        ],
    )
    def test_set_initiative(self, val, expected_d20, expected_modifier):
        itr = MockInteraction()
        initiative = Initiative(itr, 0, None, DiceRollMode.Normal)
        initiative.set_value(val)
        assert initiative.d20 == (
            expected_d20,
            expected_d20,
        ), f"Expected d20={expected_d20}, got {initiative.d20[0]}"
        assert (
            initiative.modifier == expected_modifier
        ), f"Expected modifier={expected_modifier}, got {initiative.modifier}"


class TestInitiativeTracker:
    @pytest.fixture
    def tracker(self):
        return InitiativeTracker()

    @pytest.fixture
    def itr(self):
        return MockInteraction()

    @pytest.fixture
    def npc_initiative(self, itr):
        return Initiative(itr, modifier=2, name="Goblin", roll_mode=DiceRollMode.Normal)

    @pytest.fixture
    def pc_initiative(self, itr):
        return Initiative(itr, modifier=1, name=None, roll_mode=DiceRollMode.Normal)

    def test_add_npc_initiative(self, tracker, itr, npc_initiative):
        tracker.add(itr, npc_initiative)
        result = tracker.get(itr)
        assert len(result) == 1, f"Expected 1 initiative, got {len(result)}"
        assert (
            result[0].name == npc_initiative.name
        ), f"Expected initiative name '{npc_initiative.name}', got '{result[0].name}'"
        assert result[0].is_npc is True, "Expected initiative to be NPC (is_npc=True)"

    def test_add_pc_initiative_replaces_existing(self, tracker, itr, pc_initiative):
        tracker.add(itr, pc_initiative)

        new_pc = Initiative(itr, modifier=5, name=None, roll_mode=DiceRollMode.Normal)
        new_pc.d20 = (20, 20)
        tracker.add(itr, new_pc)

        result = tracker.get(itr)
        assert (
            len(result) == 1
        ), f"Expected 1 initiative after replacement, got {len(result)}"
        assert result[0].modifier == 5, f"Expected modifier 5, got {result[0].modifier}"
        assert result[0].d20[0] == 20, f"Expected d20 value 20, got {result[0].d20[0]}"

    def test_clear_initiatives(self, tracker, itr, npc_initiative):
        tracker.add(itr, npc_initiative)
        tracker.clear(itr)
        assert tracker.get(itr) == [], "Expected initiatives to be cleared (empty list)"

    def test_get_returns_empty_for_new_guild(self, tracker):
        fresh_interaction = MockInteraction(guild_id=555)
        assert tracker.get(fresh_interaction) == [], "Expected empty list for new guild"

    def test_multiple_guilds(self, tracker):
        itr1 = MockInteraction(guild_id=1)
        itr2 = MockInteraction(MockUser(456, "Bar"), guild_id=2)

        initiative1 = Initiative(
            itr1, modifier=1, name="Goblin", roll_mode=DiceRollMode.Normal
        )
        initiative2 = Initiative(
            itr2, modifier=3, name="Orc", roll_mode=DiceRollMode.Normal
        )

        tracker.add(itr1, initiative1)
        tracker.add(itr2, initiative2)

        assert (
            len(tracker.get(itr1)) == 1
        ), f"Expected 1 initiative for guild 1, got {len(tracker.get(itr1))}"
        assert (
            len(tracker.get(itr2)) == 1
        ), f"Expected 1 initiative for guild 2, got {len(tracker.get(itr2))}"
        assert (
            tracker.get(itr1)[0].name == initiative1.name
        ), f"Expected name '{initiative1.name}in' for guild 1, got '{tracker.get(itr1)[0].name}'"
        assert (
            tracker.get(itr2)[0].name == initiative2.name
        ), f"Expected name '{initiative2.name}' for guild 2, got '{tracker.get(itr2)[0].name}'"

    def test_sorting_order(self, tracker, itr):
        for i in range(50):
            initiative = Initiative(
                itr, 3, f"Goblin {i}", roll_mode=DiceRollMode.Normal
            )
            tracker.add(itr, initiative)

        sorted_initiatives = tracker.get(itr)

        for i in range(1, len(sorted_initiatives)):
            assert (
                sorted_initiatives[i - 1].get_total()
                >= sorted_initiatives[i].get_total()
            ), "Initiatives are not sorted in descending order"

        for i in range(1, len(sorted_initiatives)):
            prev_initiative = sorted_initiatives[i - 1]
            curr_initiative = sorted_initiatives[i]
            if prev_initiative.get_total() == curr_initiative.get_total():
                assert sorted_initiatives.index(
                    prev_initiative
                ) < sorted_initiatives.index(
                    curr_initiative
                ), "Equal total initiatives are not in insertion order"

    @pytest.mark.parametrize("name", [None, "NPC"])
    def test_names_are_unique(self, name, tracker, itr):
        def add_initiative():
            initiative = Initiative(itr, 0, name, roll_mode=DiceRollMode.Normal)
            tracker.add(itr, initiative)

        add_initiative()
        length = len(tracker.get(itr))
        add_initiative()
        assert length == len(
            tracker.get(itr)
        ), f"Initiative names should be unique, not unique for {name or 'User'}"

    def test_swap(self, tracker):
        itr = MockInteraction()
        name_1, name_2 = "Goblin", "Orc"
        high, low = 20, 1

        initiative_1 = Initiative(itr, 0, name_1, roll_mode=DiceRollMode.Normal)
        initiative_2 = Initiative(itr, 0, name_2, roll_mode=DiceRollMode.Normal)
        initiative_1.d20 = (high, high)
        initiative_2.d20 = (low, low)
        tracker.add(itr, initiative_1)
        tracker.add(itr, initiative_2)

        initiatives = tracker.get(itr)
        assert [(i.name, i.get_total()) for i in initiatives] == [
            (name_1, high),
            (name_2, low),
        ]

        tracker.swap(itr, name_1, name_2)

        initiatives = tracker.get(itr)
        assert [(i.name, i.get_total()) for i in initiatives] == [
            (name_2, high),
            (name_1, low),
        ]

    def test_remove_initiative(self, tracker, itr, npc_initiative):
        tracker.add(itr, npc_initiative)
        assert len(tracker.get(itr)) == 1, "Expected 1 initiative before removal"

        _, success = tracker.remove(itr, npc_initiative.name)
        assert len(tracker.get(itr)) == 0, "Expected 0 initiatives after removal"
        assert (
            itr.guild_id not in tracker.server_initiatives
        ), "Expected guild entry to be removed after last initiative is removed"
        assert success, "Expected successful removal of initiative"

    def test_remove_initiative_fail(self, tracker, itr, npc_initiative, pc_initiative):
        tracker.add(itr, npc_initiative)

        _, success = tracker.remove(itr, pc_initiative.name)  # Remove wrong name
        assert len(tracker.get(itr)) == 1, "Expected 1 initiative after failed removal"
        assert success is False, "Expected unsuccessful removal of initiative"
