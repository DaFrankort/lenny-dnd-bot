import pytest
from mocking import MockInteraction

from logic.initiative import Initiative
from logic.roll import Advantage


class TestInitiative:
    @pytest.mark.parametrize("mod", [5, -5, 0])
    def test_init_no_target(self, mod: int):
        itr = MockInteraction()
        initiative = Initiative(itr, mod, None, Advantage.NORMAL)

        assert (
            initiative.modifier == mod
        ), f"Initiative modifier `{initiative.modifier}` is not the same as the input modifier `{mod}`"
        assert initiative.is_npc is False, "Initiative without target should not be labeled as NPC."
        assert (
            itr.user.display_name.title().strip() in initiative.name
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
        initiative = Initiative(itr, mod, target, Advantage.NORMAL)

        assert (
            initiative.modifier == mod
        ), f"Initiative modifier `{initiative.modifier}` is not the same as the input modifier `{mod}`"
        assert initiative.is_npc is True, "Initiative with target should be labeled as NPC."
        assert itr.user.display_name not in initiative.name, "Initiative with target should not have the user's name."
        assert target in initiative.name, "Initiative with target should have target's name in the name."

    @pytest.mark.parametrize(
        "advantage",
        [
            Advantage.NORMAL,
            Advantage.ADVANTAGE,
            Advantage.DISADVANTAGE,
            Advantage.ELVEN_ACCURACY,
            Advantage.SAVAGE_ATTACKER,
        ],
    )
    def test_roll(self, advantage: Advantage):
        itr = MockInteraction()
        for _ in range(50):
            initiative = Initiative(itr, 0, None, advantage)
            for roll in initiative.rolls:
                assert 1 <= roll <= 20, f"Initiative d20 roll should be value between 1 or 20, was {roll}"

    def test_roll_advantage(self):
        itr = MockInteraction()
        initiative = Initiative(itr, 0, None, Advantage.ADVANTAGE)
        high = max(initiative.rolls)

        expected = high + initiative.modifier
        total = initiative.get_total()
        assert total == expected, f"Initiative Advantage result expected {expected}, was {total}"

    def test_roll_disadvantage(self):
        itr = MockInteraction()
        initiative = Initiative(itr, 0, None, Advantage.DISADVANTAGE)
        low = min(initiative.rolls)

        expected = low + initiative.modifier
        total = initiative.get_total()
        assert total == expected, f"Initiative Disadvantage result expected {expected}, was {total}"

    @pytest.mark.parametrize("mod", [5, -5, 0])
    def test_get_total(self, mod: int):
        itr = MockInteraction()
        initiative = Initiative(itr, mod, None, Advantage.NORMAL)
        expected = initiative.rolls[0] + mod
        assert initiative.get_total() == expected, "Initiative total should equal random d20 value + modifier."

    @pytest.mark.parametrize("val", [25, -3, 10])
    def test_set_initiative(self, val: int):
        itr = MockInteraction()
        initiative = Initiative(itr, 0, None, Advantage.NORMAL, roll=val)
        assert (
            initiative.get_total() == val
        ), f"Expected total ({initiative.get_total()}) to equal set initiative value, got {val}."
