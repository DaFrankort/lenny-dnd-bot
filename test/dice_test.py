class Test_Die:
    def test_init(self):
        from dice import _Die

        # Test the constructor with a custom number of sides
        die = _Die("1d20")
        assert die.is_valid == True, "Die should be valid"
        assert die.sides == 20, "Sides should be 20"
        assert die.roll_amount == 1, "Roll amount should be 1"
        assert die.rolls != [], "Rolls should not be empty"

    def test_roll(self):
        from dice import _Die
        die = _Die("100d6")

        assert all(1 <= roll <= 6 for roll in die.rolls), "All rolled values should be between 1 and 6"

    def test_get_total(self):
        from dice import _Die
        die = _Die("1d20")
        assert die.get_total() == sum(die.rolls), "Total should be the sum of rolls"

class TestDiceExpression:
    pass # TODO MERGE DICEEXPRESSION REFACTOR FIRST