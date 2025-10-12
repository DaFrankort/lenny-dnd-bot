import math
from unittest.mock import MagicMock
import pytest
from dice import DiceCache
from logic.roll import Advantage, roll
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
        dice = roll(expression)
        assert dice.error is None, f"Dice expression '{expression}' should be valid."

    @pytest.mark.parametrize(
        "expression",
        ["1d", "d", "1d20+(4", "invalid", "1d20d20"],
    )
    def test_is_dice_expression_invalid(self, expression):
        dice = roll(expression)
        assert dice.error is not None, f"Dice expression '{expression}' should be invalid."

    def test_advantage_roll_count(self):
        normal = roll("1d20", Advantage.Normal)
        advantage = roll("1d20", Advantage.Advantage)
        disadvantage = roll("1d20", Advantage.Disadvantage)

        assert len(normal.rolls) == 1, "Normal rolls should only have one roll."
        assert len(advantage.rolls) == 2, "Advantage rolls should have two rolls."
        assert len(disadvantage.rolls) == 2, "Disadvantage rolls should have two rolls."

    @pytest.mark.parametrize("iterations", [1000])
    def test_advantage_is_greater(self, iterations):
        # Monte Carlo test to see if advantage is always the greatest of the two numbers
        for _ in range(iterations):
            dice = roll("1d20+5", Advantage.Advantage)
            totals = [roll.total for roll in dice.rolls]
            assert dice.roll.total in totals, "Advantage value should be in rolls."
            for roll_ in dice.rolls:
                assert dice.roll.total >= roll_.total, "Advantage result should be greater or equal to all rolls."

    @pytest.mark.parametrize("iterations", [1000])
    def test_disadvantage_is_less(self, iterations):
        # Same as test_advantage_is_greater, except for disadvantage
        for _ in range(iterations):
            dice = roll("1d20+5", Advantage.Disadvantage)
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
    def test_mathematical_expressions(self, expression, result):
        dice = roll(expression)
        assert dice.roll.total == result, f"Math expression '{expression}' should equal {result}"

    @pytest.mark.parametrize(
        "expression, min, max, iterations",
        [
            ("1d20+5", 6, 25, 1000),
            ("2d20", 2, 40, 1000),
        ],
    )
    def test_rolls_are_bounded(self, expression, min, max, iterations):
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


class TestDiceExpressionCache:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.test_path = tmp_path / "dice_cache.json"
        DiceCache.PATH = self.test_path
        DiceCache._data = {}  # Reset cache before each test

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

    @pytest.mark.parametrize(
        "expression",
        ["1d20+5", "123+456", "6"],
    )
    def test_store_expression_adds_to_cache(self, itr, expression: str):
        DiceCache.store_expression(itr, expression)
        user_id = str(itr.user.id)
        data = DiceCache._data

        assert user_id in data, f"User ID {user_id} should be in cache data."
        assert expression in data[user_id]["last_used"], f"'{expression}' should be in last_used for user."

    @pytest.mark.parametrize(
        "reason",
        ["reason", "attack", "1d20"],
    )
    def test_store_reason(self, itr, reason: str):
        DiceCache.store_reason(itr, reason)
        user_id = str(itr.user.id)
        data = DiceCache._data

        assert user_id in data, f"User ID {user_id} should not be in cache for invalid expression."
        assert reason in data[user_id]["last_used_reason"], f"'{reason} should be in last_used_reason"

    def test_get_autocomplete_suggestions_empty(self, itr):
        DiceCache._data = {}
        suggestions = DiceCache.get_autocomplete_suggestions(itr, "")
        assert suggestions == [], "Suggestions should be empty when no data is present."
