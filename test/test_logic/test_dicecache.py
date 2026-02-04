import pytest
from discord import Interaction
from utils.mocking import MockInteraction, MockUser

from logic.dicecache import DiceCache, DiceCacheInfo


class TestDiceExpressionCache:
    @pytest.fixture
    def itr(self):
        return MockInteraction()

    @pytest.mark.parametrize(
        "expression",
        ["1d20+5", "123+456", "6"],
    )
    def test_store_expression_adds_to_cache(self, itr: Interaction, expression: str):
        DiceCache.get(itr).store_expression(expression)
        data = DiceCache.get(itr).cache

        assert expression in data.rolls, f"'{expression}' should be in 'rolls'."

    @pytest.mark.parametrize(
        "reason",
        ["reason", "attack", "1d20"],
    )
    def test_store_reason(self, itr: Interaction, reason: str):
        DiceCache.get(itr).store_reason(reason)
        data = DiceCache.get(itr).cache

        assert reason in data.reasons, f"'{reason} should be in 'reasons'"

    def test_get_autocomplete_suggestions_empty(self, itr: Interaction):
        DiceCache.get(itr).cache = DiceCacheInfo([], [], 0)
        suggestions = DiceCache.get(itr).get_autocomplete_suggestions("")
        assert suggestions == [], "Suggestions should be empty when no data is present."

    def test_autocompletes_clean_dice_instead_of_cache(self, itr: Interaction):
        DiceCache.get(itr).cache = DiceCacheInfo([], [], 0)
        expected = "1d20"
        cached_expression = f"{expected}+5"
        DiceCache.get(itr).store_expression(cached_expression)

        suggestions = DiceCache.get(itr).get_autocomplete_suggestions(expected)
        assert (
            suggestions[0].value == expected
        ), "Autocomplete should prioritize the clean NdN query over stored modified rolls."

    def test_reason_autocomplete_for_new_user(self):
        itr = MockInteraction(user=MockUser("ReasonTest"))
        DiceCache.get(itr).data = {}  # Wipe cache to ensure user is "new"
        DiceCache.get(itr).save()

        reasons = DiceCache.get(itr).get_autocomplete_reason_suggestions("s")
        assert len(reasons) > 0, "New user could not get reason autocomplete-suggestions."
