import math

import pytest

from logic.roll import Advantage, roll


class TestDiceExpression:
    @pytest.mark.parametrize(
        "expression",
        [
            "1d20+4",
            "1d20-1d20-1d20-1d20 / 2",
        ],
    )
    def test_is_dice_expression_valid(self, expression: str):
        # This should not raise an exception
        roll(expression)

    @pytest.mark.parametrize(
        "expression",
        ["1d", "d", "1d20+(4", "invalid", "1d20d20"],
    )
    def test_is_dice_expression_invalid(self, expression: str):
        with pytest.raises(Exception):
            roll(expression)

    def test_advantage_roll_count(self):
        normal = roll("1d20", Advantage.NORMAL)
        advantage = roll("1d20", Advantage.ADVANTAGE)
        disadvantage = roll("1d20", Advantage.DISADVANTAGE)
        elven_accuracy = roll("1d20", Advantage.ELVEN_ACCURACY)

        assert len(normal.rolls) == 1, "Normal rolls should only have one roll."
        assert len(advantage.rolls) == 2, "Advantage rolls should have two rolls."
        assert len(disadvantage.rolls) == 2, "Disadvantage rolls should have two rolls."
        assert len(elven_accuracy.rolls) == 3, "Elven accuracy rolls should have three rolls."

    @pytest.mark.parametrize("advantage", (Advantage.ADVANTAGE, Advantage.ELVEN_ACCURACY))
    def test_advantage_is_greater(self, advantage: Advantage):
        # Monte Carlo test to see if advantage is always the greatest of the two numbers
        for _ in range(1000):
            dice = roll("1d20+5", advantage)
            totals = [roll.total for roll in dice.rolls]
            assert dice.roll.total in totals, "Advantage value should be in rolls."
            for roll_ in dice.rolls:
                assert dice.roll.total >= roll_.total, "Advantage result should be greater or equal to all rolls."

    def test_disadvantage_is_less(self):
        # Same as test_advantage_is_greater, except for disadvantage
        for _ in range(1000):
            dice = roll("1d20+5", Advantage.DISADVANTAGE)
            totals = [roll.total for roll in dice.rolls]
            assert dice.roll.total in totals, "Disadvantage value should be in rolls."
            for roll_ in dice.rolls:
                assert dice.roll.total <= roll_.total, "Disadvantage result should be less or equal to all rolls."

    @pytest.mark.parametrize(
        "expression, result",
        [
            ("4 + 4 - 3", 4 + 4 - 3),
            ("99*99-99", 99 * 99 - 99),
            ("10/4", int(math.floor(10 / 4))),
            ("(100 + 150) * (1000+ 1500) + 4", (100 + 150) * (1000 + 1500) + 4),
        ],
    )
    def test_mathematical_expressions(self, expression: str, result: int):
        dice = roll(expression)
        assert dice.roll.total == result, f"Math expression '{expression}' should equal {result}"

    @pytest.mark.parametrize(
        "expression, min, max, iterations",
        [
            ("1d20+5", 6, 25, 1000),
            ("2d20", 2, 40, 1000),
        ],
    )
    def test_rolls_are_bounded(self, expression: str, min: int, max: int, iterations: int):
        for _ in range(iterations):
            dice = roll(expression)
            assert min <= dice.roll.total <= max, f"Expression '{expression}' should be within [{min}, {max}]"

    """
    The following three tests are chance-based, where 1000 d20's are rolled for one
    specific result. The odds of failure are deemed low enough, namely (1/20)^1000
    """

    def test_is_nat_one(self):
        dice = roll("1d20ma1+5+5+5")
        assert dice.roll.is_natural_one, "Dice roll should be natural one."

    def test_is_nat_twenty(self):
        dice = roll("1d20mi20+5+5+5")
        assert dice.roll.is_natural_twenty, "Dice roll should be natural twenty."

    def test_is_dirty_twenty(self):
        dice = roll("1d20mi17ma17+3")
        assert dice.roll.is_dirty_twenty, "Dice roll should be dirty twenty."

    def test_contains_dice(self):
        dice1 = roll("1d20+5")
        dice2 = roll("120 + 5")

        assert dice1.roll.contains_dice
        assert not dice2.roll.contains_dice

    @pytest.mark.parametrize(
        "expected, expr",
        [
            (True, "1>0"),
            (True, "1<0"),
            (True, "1==1"),
            (True, "1!=1"),
            (True, "1>=1"),
            (True, "1<=1"),
            (True, "(6>7)"),
            (True, "(((((6>7)))))"),
            (False, "(6>7)*1"),
            (False, "(6>7)*0"),
            (False, "(6>7)*(1d8+7)"),
            (False, "((6>7)*(1d8+7))"),
            (False, "1d20"),
            (False, "1d20+7"),
            (False, "1d20*7"),
            (False, "1d20-7"),
            (False, "1d20/2"),
            (False, "(6<7)*0"),
            (False, "(6<7)*1"),
            (False, "1"),
            (False, "0"),
            (False, "4d8kh3"),
            (False, "1d4ro1"),
        ],
    )
    def test_has_comparison_result(self, expected: bool, expr: str):
        result = roll(expr).roll.has_comparison_result
        assert result == expected, f"expression '{expr}' expected {expected} but got {result}"
