class Test_Die:
    def test_init(self):
        from dice import _Die

        # Test positive die, single roll
        die = _Die("1d20")
        assert die.is_valid == True, "Die should be valid"
        assert die.is_positive == True, "Die should be positive"
        assert die.sides == 20, "Sides should be 20"
        assert die.roll_amount == 1, "Roll amount should be 1"
        assert die.warnings == [], "Warnings should be empty"
        assert die.is_single_roll() == True, "Die should be a single roll"

        # Test negative die, multiple rolls
        die = _Die("4d6", is_positive=False)
        assert die.is_valid == True, "Die should be valid"
        assert die.is_positive == False, "Die should be positive"
        assert die.sides == 6, "Sides should be 6"
        assert die.roll_amount == 4, "Roll amount should be 4"
        assert die.warnings == [], "Warnings should be empty"
        assert die.is_single_roll() == False, "Die should not be a single roll"

        # Invalid die
        die = _Die("INVALID")
        assert die.is_valid == False, "Die should be invalid"

        # Test die with warnings
        roll_amount = 99999
        die = _Die(f"{roll_amount}d20") # Too many rolls
        assert die.is_valid == True, "Die should be valid"
        assert die.roll_amount != roll_amount, "Rolls should be limited to lower value"
        assert len(die.warnings) > 0, "Warnings should not be empty"

        sides = 99999
        die = _Die(f"1d{sides}") # Too many sides
        assert die.is_valid == True, "Die should be valid"
        assert die.sides != sides, "Sides should be limited to lower value"
        assert len(die.warnings) > 0, "Warnings should not be empty"

    def test_str(self):
        from dice import _Die
        die = _Die("1d20")
        assert str(die).startswith("+"), "String representation should start with '+'"

        die = _Die("4d6", is_positive=False)
        assert str(die).startswith("-"), "String representation should start with '-'"

    def test_roll(self):
        from dice import _Die
        die = _Die("100d6")

        assert all(1 <= roll <= 6 for roll in die.rolls), "All rolled values should be between 1 and 6"

    def test_get_total(self):
        from dice import _Die
        die = _Die("1d20", is_positive=True)
        assert die.get_total() == sum(die.rolls), "Total should be the sum of rolls"

        die = _Die("4d6" , is_positive=False)
        assert die.get_total() == -sum(die.rolls), "Total should be the sum of rolls, but negative"

    def test_is_nat_20(self):
        from dice import _Die
        die = _Die("1d20")
        die.rolls = [20]  # Simulate a nat 20
        assert die.is_natural_twenty() == True, "Die should be a natural 20"

    def test_is_nat_1(self):
        from dice import _Die
        die = _Die("1d20")
        die.rolls = [1]  # Simulate a nat 1
        assert die.is_natural_one() == True, "Die should be a natural 1"

class Test_Modifier:
    def test_init(self):
        from dice import _Modifier

        # Test positive modifier
        mod = _Modifier("5", is_positive=True)
        assert mod.is_valid == True, "Modifier should be valid"
        assert mod.is_positive == True, "Modifier should be positive"
        assert mod.value == 5, "Modifier value should be 5"
        assert mod.get_value() == 5, "Modifier whole value should be 5"
        assert mod.warnings == [], "Warnings should be empty"

        # Test negative modifier
        mod = _Modifier("3", is_positive=False)
        assert mod.is_valid == True, "Modifier should be valid"
        assert mod.is_positive == False, "Modifier should be positive"
        assert mod.value == 3, "Modifier value should be 3"
        assert mod.get_value() == -3, "Modifier whole value should be -3"
        assert mod.warnings == [], "Warnings should be empty"

        # Invalid modifier
        mod = _Modifier("INVALID")
        assert mod.is_valid == False, "Modifier should be invalid"

        # Test modifier with overly large value
        mod_value = 99999
        mod = _Modifier(str(mod_value)) # Value too high
        assert mod.is_valid == True, "Modifier should be valid"
        assert mod.value != mod_value, "Modifier value should be limited to lower value"
        assert abs(mod.get_value()) != mod_value, "Modifier value should be limited to lower value"
        assert len(mod.warnings) > 0, "Warnings should not be empty"

    def test_str(self):
        from dice import _Modifier
        mod = _Modifier("5", is_positive=True)
        assert str(mod) == "+5", "String representation should be '+5'"

        mod = _Modifier("3", is_positive=False)
        assert str(mod) == "-3", "String representation should be '-3'"

class TestDiceExpression:
    def test_init(self):
        from dice import DiceExpression

        # Test valid expression
        expr = DiceExpression("1d20+5")
        assert expr.is_valid() == True, "Expression should be valid"
        assert expr.has_warnings() == False, "Should not have warnings"
        assert len(expr.dice) == 1, "There should be one die"
        assert len(expr.modifiers) == 1, "There should be one modifier"
        assert len(expr.steps) == 2, "There should be two steps (one die, one mod)"

        # Test invalid expression
        expr = DiceExpression("INVALID")
        assert expr.is_valid() == False, "Expression should be invalid"

    def test_sanitize(self):
        from dice import DiceExpression
        
        def assert_sanitized(notation, expected):
            e = DiceExpression("")
            result = e._sanitize_die_notation(notation)
            assert result == expected, f"Expected {expected}, but got {result}"

        good_notation = ['1d20', '2d6+3', '-4d8-2']
        for notation in good_notation:
            assert_sanitized(notation, notation)

        assert_sanitized("1D20 + 5", "1d20+5") # Remove spaces and normalize case
        assert_sanitized("WRONG", "") # Remove any invalid characters
        assert_sanitized("1ddd20++5--10", "1d20+5-10") # Collapse any double signs and d's
        assert_sanitized("d20+5", "1d20+5") # Default to 1 if no number before d

    def test_get_total(self):
        from dice import DiceExpression

        expr = DiceExpression("1d20+5")
        expr.dice[0].rolls = [20]
        assert expr.get_total() == 25, "Total should be 25"

    def test_str(self):
        from dice import DiceExpression

        expr = DiceExpression("1d20")
        assert str(expr.get_total()) in str(expr), "String representation should include total"

        expr = DiceExpression("4d6-3")
        assert str(expr.get_total()) in str(expr), "String representation should include total"

    def test_dirty_20(self):
        from dice import DiceExpression

        expr = DiceExpression("1d20+5")
        expr.dice[0].rolls = [15]
        assert expr.is_dirty_twenty() == True, "Expression should be dirty"
        expr.dice[0].rolls = [1]
        assert expr.is_dirty_twenty() == False, "Expression should not be dirty"

        expr = DiceExpression("2d20+1")
        expr.dice[0].rolls = [18, 1]
        assert expr.is_dirty_twenty() == False, "Dirty twenty should only be for 1d20 dice"

        expr = DiceExpression("1d20+1d20")
        expr.dice[0].rolls = [20]
        expr.dice[1].rolls = [0]
        assert expr.is_dirty_twenty() == False, "Dirty twenty should only be for single dice expressions"