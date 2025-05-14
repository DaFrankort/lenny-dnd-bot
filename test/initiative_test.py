import pytest
from utils.mock_discord_interaction import MockInteraction

from initiative import Initiative


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
