import pytest

from logic.stats import Stats


class TestStats:
    def test_stat_values(self):
        stats = Stats()

        for stat in stats.stats:
            rolls, result = stat
            assert len(rolls) == 4, "There should be 4 rolls"
            assert all(1 <= roll <= 6 for roll in rolls), "Rolls should be between 1 and 6"
            assert isinstance(result, int), "Result should be an integer"
            assert 3 <= result <= 24, "Result should be between 4 and 24 (sum of 3 rolls)"

    def test_stat_limits(self):
        """Stats can only roll up to 108 total. In this case, the value will never be reached and will thus timeout."""
        with pytest.raises(ValueError):
            Stats(min_total=999)
