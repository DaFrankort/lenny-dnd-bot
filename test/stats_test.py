from stats import Stats
from utils.mock_discord_interaction import MockInteraction

class TestStats:
    def test_init(self):
        stats = Stats(MockInteraction())
        
        for stat in stats.stats:
            rolls, result = stat
            assert len(rolls) == 4, "There should be 4 rolls"
            assert all(1 <= roll <= 6 for roll in rolls), "Rolls should be between 1 and 6"
            assert isinstance(result, int), "Result should be an integer"
            assert 4 <= result <= 24 , "Result should be between 4 and 24 (sum of 3 rolls)"

    def test_get_embed_title(self):
        stats = Stats(MockInteraction())
        display_name = stats.interaction.user.display_name
        embed_title = stats.get_embed_title()

        assert display_name in embed_title, "Embed title should contain the user's display name"

    def test_get_embed_description(self):
        stats = Stats(MockInteraction())
        description = stats.get_embed_description()

        for rolls, result in stats.stats:
            for index, roll in enumerate(rolls):
                assert str(roll) in description, f"Description should contain the roll {roll} at index {index}"
            assert str(result) in description, f"Description should contain the result {result}"

        total = sum(result for _, result in stats.stats)
        assert str(total) in description, "Description should contain the total of all stats"