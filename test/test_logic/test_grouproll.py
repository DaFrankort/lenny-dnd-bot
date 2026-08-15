import pytest
from mocking import MockInteraction

from logic.grouproll import GroupRollRoll
from logic.roll import Advantage


class TestGroupRoll:
    @pytest.mark.parametrize("mod", ["5", "-5", "1d4+2"])
    def test_init_no_target(self, mod: str):
        itr = MockInteraction()
        group_roll = GroupRollRoll(itr, None, mod, Advantage.NORMAL)

        assert (
            group_roll.modifier == mod
        ), f"GroupRoll modifier `{group_roll.modifier}` is not the same as the input modifier `{mod}`"
        assert group_roll.is_npc is False, "GroupRoll without target should not be labeled as NPC."
        assert itr.user.display_name.title().strip() in group_roll.name, "GroupRoll without target should have the user's name."

    @pytest.mark.parametrize(
        "mod, target",
        [
            ("5", "Crab"),
            ("-5", "Goblin"),
            ("1d8", "Dragon"),
        ],
    )
    def test_init_with_target(self, mod: str, target: str):
        itr = MockInteraction()
        group_roll = GroupRollRoll(itr, target, mod, Advantage.NORMAL)

        assert (
            group_roll.modifier == mod
        ), f"GroupRoll modifier `{group_roll.modifier}` is not the same as the input modifier `{mod}`"
        assert group_roll.is_npc is True, "GroupRoll with target should be labeled as NPC."
        assert itr.user.display_name not in group_roll.name, "GroupRoll with target should not have the user's name."
        assert target in group_roll.name, "GroupRoll with target should have target's name in the name."

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
            group_roll = GroupRollRoll(itr, None, "0", advantage)
            for roll in group_roll.roll.result.rolls:
                assert 1 <= roll.total <= 20, f"GroupRoll d20 roll should be value between 1 or 20, was {roll}"
