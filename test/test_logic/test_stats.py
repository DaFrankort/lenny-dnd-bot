from test.mocking import MockInteraction, MockUser

import pytest

from logic.stats import POINT_BUY_COST, BoughtStats, Stats


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
        with pytest.raises(TimeoutError):
            Stats(min_total=999)


class TestBoughtStats:
    @pytest.fixture
    def stats(self) -> BoughtStats:
        itr = MockInteraction()
        return BoughtStats(itr)

    def test_initial_values(self, stats: BoughtStats):
        assert stats.points == stats.max_points
        assert stats.stats == {"STR": 8, "DEX": 8, "CON": 8, "INT": 8, "WIS": 8, "CHA": 8}
        assert stats.values == [8, 8, 8, 8, 8, 8]

    def test_add_score(self, stats: BoughtStats):
        key = "STR"
        assert stats.can_add(key) is True
        stats.add_score(key)
        assert stats.stats[key] == 9
        expected_cost = POINT_BUY_COST[9] - POINT_BUY_COST[8]
        assert stats.points == stats.max_points - expected_cost

    def test_cannot_add_above_15(self, stats: BoughtStats):
        """Stats cannot exceed 15."""
        key = "DEX"
        stats.stats[key] = 15
        assert stats.can_add(key) is False
        stats.add_score(key)
        assert stats.stats[key] == 15

    def test_take_score(self, stats: BoughtStats):
        key = "CON"
        stats.stats[key] = 10
        stats.points = stats.max_points - 2  # simulate prior spending

        assert stats.can_take(key) is True
        stats.take_score(key)
        assert stats.stats[key] == 9
        refund = POINT_BUY_COST[10] - POINT_BUY_COST[9]
        assert stats.points == stats.max_points - 2 + refund

    def test_cannot_take_below_8(self, stats: BoughtStats):
        key = "INT"
        assert stats.stats[key] == 8
        assert stats.can_take(key) is False
        stats.take_score(key)
        assert stats.stats[key] == 8

    def test_viable_scores(self, stats: BoughtStats):
        key = "WIS"
        valid_scores = stats.viable_scores(key)
        expected_scores = [8, 9, 10, 11, 12, 13, 14, 15]
        assert valid_scores == expected_scores

    def test_is_owner(self, stats: BoughtStats):
        user_same = MockUser("Owner")
        user_same.id = stats.owner_id
        user_other = MockUser("Other")
        assert stats.is_owner(user_same) is True
        assert stats.is_owner(user_other) is False
