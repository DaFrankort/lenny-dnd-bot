from stats import StatsEmbed
from utils.mock_discord_interaction import MockInteraction

class TestStatsEmbed:
    def test_roll(self):
        embed = StatsEmbed(MockInteraction())
        rolls, result = embed._roll()
        
        assert len(rolls) == 4, "Should roll 4 dice"
        assert all(1 <= roll <= 6 for roll in rolls), "Each roll should be between 1 and 6"
        
        assert result == sum(sorted(rolls)[1:]), "Result should be the sum of the 3 highest rolls"