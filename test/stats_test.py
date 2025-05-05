import pytest
from stats import StatsEmbed

class TestStatsEmbed:
    def test_roll(self):
        embed = StatsEmbed(MockInteraction())
        rolls, result = embed._roll()
        
        assert len(rolls) == 4
        assert all(1 <= roll <= 6 for roll in rolls)
        
        # Check that the result is the sum of the highest 3 rolls
        assert result == sum(sorted(rolls)[1:])