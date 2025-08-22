import math
from unittest.mock import MagicMock
import pytest
from dice import (
    DiceExpression,
    DiceExpressionCache,
    DiceRollMode,
)
from utils.mock_discord_interaction import MockInteraction


class TestDiceExpression:
    @pytest.mark.parametrize(
        "expression",
        [
            "1d20+4",
            "1d20-1d20-1d20-1d20 / 2",
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

    """
    The following three tests are chance-based, where 1000 d20's are rolled for one
    specific result. The odds of failure are deemed low enough, namely (1/20)^1000
    """

    def test_is_nat_one(self):
        dice = DiceExpression("1000d20kl1+5+5+5")
        assert dice.roll.is_natural_one, "Dice roll should be natural one."

    def test_is_nat_twenty(self):
        dice = DiceExpression("1000d20kh1+5+5+5")
        assert dice.roll.is_natural_twenty, "Dice roll should be natural twenty."

    def test_is_dirty_twenty(self):
        dice = DiceExpression("1000d20kh1ma17+3")
        assert dice.roll.is_dirty_twenty, "Dice roll should be dirty twenty."

    def test_contains_dice(self):
        dice1 = DiceExpression("1d20+5")
        dice2 = DiceExpression("120 + 5")

        assert "Expression contains no dice." not in dice1.description
        assert "Expression contains no dice." in dice2.description


class TestDiceExpressionCache:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.test_path = tmp_path / "dice_cache.json"
        DiceExpressionCache.PATH = self.test_path
        DiceExpressionCache._data = {}  # Reset cache before each test

    @pytest.fixture
    def itr(self):
        return MockInteraction()

    @pytest.fixture
    def valid_expression(self):
        mock_expr = MagicMock()
        mock_expr.roll.errors = []
        mock_expr.roll.expression = "1d20+5"
        mock_expr.reason = "Attack"
        mock_expr.description = "A valid roll"
        return mock_expr

    @pytest.fixture
    def invalid_expression(self):
        mock_expr = MagicMock()
        mock_expr.roll.errors = ["error"]
        mock_expr.description = "An invalid roll"
        return mock_expr

    def test_store_expression_adds_to_cache(self, itr, valid_expression):
        DiceExpressionCache.store_expression(itr, valid_expression, "1d20+5")
        user_id = str(itr.user.id)
        data = DiceExpressionCache._data
        reason = valid_expression.reason

        assert user_id in data, f"User ID {user_id} should be in cache data."
        assert (
            "1d20+5" in data[user_id]["last_used"]
        ), "'1d20+5' should be in last_used for user."
        assert (
            reason in data[user_id]["last_used_reason"]
        ), f"'{reason}' should be in last_used_reason for user."

    def test_store_expression_does_not_add_invalid(self, itr, invalid_expression):
        DiceExpressionCache.store_expression(itr, invalid_expression, "2d6")
        user_id = str(itr.user.id)

        assert (
            user_id not in DiceExpressionCache._data
        ), f"User ID {user_id} should not be in cache for invalid expression."

    def test_store_shortcut_valid(self, itr):
        description, success = DiceExpressionCache.store_shortcut(
            itr, "quickattack", "1d6+3", "Fast strike"
        )

        user_data = DiceExpressionCache._data[str(itr.user.id)]
        assert (
            "quickattack" in user_data["shortcuts"]
        ), "'quickattack' should be in user's shortcuts."
        assert success is True, "Success should be True for valid shortcut."

    def test_store_shortcut_invalid(self, itr):
        description, success = DiceExpressionCache.store_shortcut(
            itr, "failshot", "1d8+WRONG", None
        )

        assert success is False, "Success should be False for invalid shortcut."

    def test_remove_shortcut_success(self, itr):
        DiceExpressionCache._data = {
            str(itr.user.id): {
                "shortcuts": {"fireball": {"expression": "8d6", "reason": "big boom"}}
            }
        }

        desc, success = DiceExpressionCache.remove_shortcut(itr, "fireball")
        assert success is True, "Shortcut should be removed successfully."
        assert (
            "fireball" not in DiceExpressionCache._data[str(itr.user.id)]["shortcuts"]
        ), "'fireball' should not be in user's shortcuts after removal."

    def test_remove_shortcut_fail(self, itr):
        DiceExpressionCache._data = {}
        desc, success = DiceExpressionCache.remove_shortcut(itr, "doesnotexist")
        assert (
            success is False
        ), "Should return False when trying to remove non-existent shortcut."

    def test_get_shortcut_found(self, itr):
        user_id = str(itr.user.id)
        DiceExpressionCache._data = {
            user_id: {"shortcuts": {"blast": {"expression": "2d10", "reason": "boom"}}}
        }

        result = DiceExpressionCache.get_shortcut(itr, "blast")
        assert (
            result["expression"] == "2d10"
        ), "Should return correct expression for found shortcut."

    def test_get_shortcut_not_found(self, itr):
        DiceExpressionCache._data = {}
        result = DiceExpressionCache.get_shortcut(itr, "nothing")
        assert result is None, "Should return None for non-existent shortcut."

    def test_get_autocomplete_suggestions_empty(self, itr):
        DiceExpressionCache._data = {}
        suggestions = DiceExpressionCache.get_autocomplete_suggestions(itr, "")
        assert suggestions == [], "Suggestions should be empty when no data is present."

    def test_get_shortcut_autocomplete_suggestions_match(self, itr):
        itr.namespace = MagicMock()
        itr.namespace.action = "REMOVE"
        user_id = str(itr.user.id)

        DiceExpressionCache._data = {
            user_id: {
                "shortcuts": {
                    "attack": {"expression": "1d20+3", "reason": None},
                    "defend": {"expression": "1d20+2", "reason": None},
                }
            }
        }

        suggestions = DiceExpressionCache.get_shortcut_autocomplete_suggestions(
            itr, "att"
        )
        assert len(suggestions) == 1, "Should return one suggestion matching 'att'."
        assert suggestions[0].name == "attack", "Suggestion name should be 'attack'."
