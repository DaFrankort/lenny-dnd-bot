import math
import pytest
from dice import (
    ASTCompoundExpression,
    ASTDiceExpression,
    ASTGroupExpression,
    DiceExpression,
    DiceRollDice,
    DiceRollMode,
    TokenType,
)


class TestDiceAST:
    def test_ast_tree(self):
        """
        The base tree should look like this:
             +
           /   \
        1d20   ( )
                |
                5
        """

        dice = DiceExpression("1d20+(5)")
        assert isinstance(
            dice.ast, ASTCompoundExpression
        ), "Base AST expression should be a compound expression."
        assert (
            dice.ast.operator.type == TokenType.Plus
        ), "Base AST expression should be a plus."
        assert isinstance(
            dice.ast.left, ASTDiceExpression
        ), "Left AST expression should be a dice expression."
        assert isinstance(
            dice.ast.right, ASTGroupExpression
        ), "Right AST expression should be a group expression."
        assert isinstance(
            dice.ast.right.expression, ASTDiceExpression
        ), "Right AST internal expression should be a dice expression."


class TestDiceExpression:
    @pytest.mark.parametrize(
        "expression",
        [
            "1d20+4",
            "1d20-1d20-1d20-1d20 / 2",
            "1invalid20",  # is valid as this gets cleaned to 1d20
        ],
    )
    def test_is_dice_expression_valid(self, expression):
        dice = DiceExpression(expression)
        assert dice.is_valid, f"Dice expression '{expression}' should be valid."

    @pytest.mark.parametrize(
        "expression",
        ["1d", "d", "1d20+(4", "invalid", "1d20d20"],
    )
    def test_is_dice_expression_invalid(self, expression):
        dice = DiceExpression(expression)
        assert not dice.is_valid, f"Dice expression '{expression}' should be invalid."

    def test_advantage_roll_count(self):
        normal = DiceExpression("1d20", DiceRollMode.Normal)
        advantage = DiceExpression("1d20", DiceRollMode.Advantage)
        disadvantage = DiceExpression("1d20", DiceRollMode.Disadvantage)

        assert len(normal.rolls) == 1, "Normal rolls should only have one roll."
        assert len(advantage.rolls) == 2, "Advantage rolls should have two rolls."
        assert len(disadvantage.rolls) == 2, "Disadvantage rolls should have two rolls."

    @pytest.mark.parametrize("iterations", [1000])
    def test_advantage_is_greater(self, iterations):
        # Monte Carlo test to see if advantage is always the greatest of the two numbers
        for _ in range(iterations):
            dice = DiceExpression("1d20+5", DiceRollMode.Advantage)
            values = [roll.value for roll in dice.rolls]
            assert dice.roll.value in values, "Advantage value should be in rolls."
            for roll in dice.rolls:
                assert (
                    dice.roll.value >= roll.value
                ), "Advantage result should be greater or equal to all rolls."

    @pytest.mark.parametrize("iterations", [1000])
    def test_disadvantage_is_less(self, iterations):
        # Same as test_advantage_is_greater, except for disadvantage
        for _ in range(iterations):
            dice = DiceExpression("1d20+5", DiceRollMode.Disadvantage)
            values = [roll.value for roll in dice.rolls]
            assert dice.roll.value in values, "Disadvantage value should be in rolls."
            for roll in dice.rolls:
                assert (
                    dice.roll.value <= roll.value
                ), "Disadvantage result should be less or equal to all rolls."

    @pytest.mark.parametrize(
        "expression, result",
        [
            ("4 + 4 - 3", 4 + 4 - 3),
            ("99*99-99", 99 * 99 - 99),
            ("10/4", int(math.floor(10 / 4))),
            ("(100 + 150) * (1000+ 1500) + 4", (100 + 150) * (1000 + 1500) + 4),
        ],
    )
    def test_mathematical_expressions(self, expression, result):
        dice = DiceExpression(expression)
        assert (
            dice.roll.value == result
        ), f"Math expression '{expression}' should equal {result}"

    @pytest.mark.parametrize(
        "expression, min, max, iterations",
        [
            ("1d20+5", 6, 25, 1000),
            ("2d20", 2, 40, 1000),
        ],
    )
    def test_rolls_are_bounded(self, expression, min, max, iterations):
        for _ in range(iterations):
            dice = DiceExpression(expression)
            assert (
                min <= dice.roll.value <= max
            ), f"Expression '{expression}' should be within [{min}, {max}]"

    def test_is_nat_one(self):
        dice = DiceExpression("1d20+5+5+5")
        dice.roll.dice_rolled[0] = DiceRollDice(1, 20)
        assert dice.roll.is_natural_one, "Modified dice roll should be natural one."

    def test_is_nat_twenty(self):
        dice = DiceExpression("1d20+5+5+5")
        dice.roll.dice_rolled[0] = DiceRollDice(20, 20)
        assert (
            dice.roll.is_natural_twenty
        ), "Modified dice roll should be natural twenty."

    def test_is_dirty_twenty(self):
        dice = DiceExpression("1d20+5+5+5")
        dice.roll.dice_rolled[0] = DiceRollDice(5, 20)
        dice.roll.value = 20
        assert dice.roll.is_dirty_twenty, "Modified dice roll should be dirty twenty."
