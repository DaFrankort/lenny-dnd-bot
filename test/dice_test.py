import pytest
from dice import _Die, _Modifier, DiceExpression


def assert_die_properties(
    die, is_positive, sides, roll_amount, is_single_roll, warnings_length=0
):
    assert die.is_valid is True, "Die should be valid"
    assert (
        die.is_positive == is_positive
    ), f"Die should be {'positive' if is_positive else 'negative'}"
    assert die.sides == sides, f"Sides should be {sides}"
    assert die.roll_amount == roll_amount, f"Roll amount should be {roll_amount}"
    assert len(die.warnings) == warnings_length, f"Warnings should be {warnings_length}"
    assert (
        die.is_single_roll() == is_single_roll
    ), f"Die should {'be' if is_single_roll else 'not be'} a single roll"


class Test_Die:
    @pytest.mark.parametrize(
        "notation, is_positive, sides, roll_amount, is_single_roll",
        [("1d20", True, 20, 1, True), ("4d6", False, 6, 4, False)],
    )
    def test_init_valid(
        self, notation, is_positive, sides, roll_amount, is_single_roll
    ):
        die = _Die(notation, is_positive=is_positive)
        assert_die_properties(die, is_positive, sides, roll_amount, is_single_roll)

    @pytest.mark.parametrize("notation", ["INVALID", "1d20+5", "4d6-3"])
    def test_init_invalid(self, notation):
        die = _Die(notation)
        assert die.is_valid is False, "Die should be invalid"

    def test_warnings(self):
        roll_amount = 99999
        die = _Die(f"{roll_amount}d20")
        assert die.is_valid is True, "Die should be valid"
        assert die.roll_amount != roll_amount, "Rolls should be limited to lower value"
        assert len(die.warnings) > 0, "Warnings should not be empty"

        sides = 99999
        die = _Die(f"1d{sides}")
        assert die.is_valid is True, "Die should be valid"
        assert die.sides != sides, "Sides should be limited to lower value"
        assert len(die.warnings) > 0, "Warnings should not be empty"

    def test_str(self):
        assert str(_Die("1d20", is_positive=True)).startswith(
            "+"
        ), "String representation should start with '+'"
        assert str(_Die("4d6", is_positive=False)).startswith(
            "-"
        ), "String representation should start with '-'"

    def test_roll(self):
        die = _Die("100d6")
        assert all(
            1 <= roll <= 6 for roll in die.rolls
        ), "All rolled values should be between 1 and 6"

    def test_get_total(self):
        die = _Die("1d20", is_positive=True)
        assert die.get_total() == sum(die.rolls), "Total should be the sum of rolls"
        die = _Die("4d6", is_positive=False)
        assert die.get_total() == -sum(
            die.rolls
        ), "Total should be the sum of rolls, but negative"

    def test_is_nat_20(self):
        die = _Die("1d20")
        die.rolls = [20]  # Simulate a nat 20
        assert die.is_natural_twenty(), "Die should be a natural 20"

    def test_is_nat_1(self):
        die = _Die("1d20")
        die.rolls = [1]  # Simulate a nat 1
        assert die.is_natural_one(), "Die should be a natural 1"


class Test_Modifier:
    def test_init(self):
        # Test positive modifier
        mod = _Modifier("5", is_positive=True)
        assert mod.is_valid, "Modifier should be valid"
        assert mod.is_positive, "Modifier should be positive"
        assert mod.value == 5, "Modifier value should be 5"
        assert mod.get_value() == 5, "Modifier whole value should be 5"
        assert len(mod.warnings) == 0, "Warnings should be empty"

        # Test negative modifier
        mod = _Modifier("3", is_positive=False)
        assert mod.is_valid, "Modifier should be valid"
        assert not mod.is_positive, "Modifier should be positive"
        assert mod.value == 3, "Modifier value should be 3"
        assert mod.get_value() == -3, "Modifier whole value should be -3"
        assert mod.warnings == [], "Warnings should be empty"

        # Invalid modifier
        mod = _Modifier("INVALID")
        assert not mod.is_valid, "Modifier should be invalid"

        # Test modifier with overly large value
        mod_value = 99999
        mod = _Modifier(str(mod_value))  # Value too high
        assert mod.is_valid, "Modifier should be valid"
        assert mod.value != mod_value, "Modifier value should be limited to lower value"
        assert (
            abs(mod.get_value()) != mod_value
        ), "Modifier value should be limited to lower value"
        assert len(mod.warnings) > 0, "Warnings should not be empty"

    def test_str(self):
        mod = _Modifier("5", is_positive=True)
        assert str(mod) == "+5", "String representation should be '+5'"

        mod = _Modifier("3", is_positive=False)
        assert str(mod) == "-3", "String representation should be '-3'"


class TestDiceExpression:
    def test_init_valid(self):
        # Test valid expression
        expr = DiceExpression("1d20+5")
        assert expr._is_valid, "Expression should be valid"
        assert expr.is_valid(), "Expression should be valid"
        assert not expr.has_warnings(), "Should not have warnings"
        assert len(expr.dice) == 1, "There should be one die"
        assert len(expr.modifiers) == 1, "There should be one modifier"
        assert len(expr.steps) == 2, "There should be two steps (one die, one mod)"

    def test_init_invalid(self):
        expr = DiceExpression("MONKEY")
        assert expr._is_valid is False, "DiceExpression should be invalid"
        assert expr.is_valid() is False, "DiceExpression should be invalid"

    def test_sanitize(self):
        def assert_sanitized(notation, expected):
            e = DiceExpression("")
            result = e._sanitize_die_notation(notation)
            assert result == expected, f"Expected {expected}, but got {result}"

        good_notation = ["1d20", "2d6+3", "-4d8-2"]
        for notation in good_notation:
            assert_sanitized(notation, notation)

        assert_sanitized("1D20 + 5", "1d20+5")  # Remove spaces and normalize case
        assert_sanitized("WRONG", "")  # Remove any invalid characters
        assert_sanitized(
            "1ddd20++5--10", "1d20+5-10"
        )  # Collapse any double signs and d's
        assert_sanitized("d20+5", "1d20+5")  # Default to 1 if no number before d

    def test_get_total(self):
        expr = DiceExpression("1d20+5")
        expr.dice[0].rolls = [20]
        assert expr.get_total() == 25, "Total should be 25"

    def test_str(self):
        expr = DiceExpression("1d20")
        assert str(expr.get_total()) in str(
            expr
        ), "String representation should include total"

        expr = DiceExpression("4d6-3")
        assert str(expr.get_total()) in str(
            expr
        ), "String representation should include total"

    def test_dirty_20(self):
        expr = DiceExpression("1d20+5")
        expr.dice[0].rolls = [15]
        assert expr.is_dirty_twenty(), "Expression should be dirty"
        expr.dice[0].rolls = [1]
        assert not expr.is_dirty_twenty(), "Expression should not be dirty"

        expr = DiceExpression("2d20+1")
        expr.dice[0].rolls = [18, 1]
        assert not expr.is_dirty_twenty(), "Dirty twenty should only be for 1d20 dice"

        expr = DiceExpression("1d20+1d20")
        expr.dice[0].rolls = [20]
        expr.dice[1].rolls = [0]
        assert (
            not expr.is_dirty_twenty()
        ), "Dirty twenty should only be for single dice expressions"
