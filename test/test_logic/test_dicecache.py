import pytest
from discord import Interaction
from mocking import MockInteraction, MockUser

from logic.dicecache import DiceCache, DiceCacheInfo, DiceCacheTrie


class TestDiceCacheTrie:
    @pytest.fixture
    def cache_info(self) -> DiceCacheInfo:
        return DiceCacheInfo(rolls=[], reasons=[], initiative=0, trie={})

    @pytest.fixture
    def trie_handler(self, cache_info: DiceCacheInfo) -> DiceCacheTrie:
        return DiceCacheTrie(cache_info)

    def test_add_expression(self, trie_handler: DiceCacheTrie, cache_info: DiceCacheInfo):
        trie_handler.add("1d20+5")
        trie_handler.add("1d20+5")

        assert cache_info.trie["1d20+5"] == 2

        # Ensure it normalizes input (lowercase, no spaces)
        trie_handler.add(" 2d6 + 2 ")
        assert "2d6+2" in cache_info.trie

    def test_get_suggestions_sorting(self, trie_handler: DiceCacheTrie):
        trie_handler.add("8d6")
        trie_handler.add("8d8")
        trie_handler.add("8d8")

        suggestions = trie_handler.get_suggestions("8d", limit=5)

        assert suggestions[0] == "8d8", "most used trie expression should be the first suggestion."
        assert suggestions[1] == "8d6", "second most used trie expression should be the second suggestion."

    def test_clean_pruning(self, trie_handler: DiceCacheTrie, cache_info: DiceCacheInfo):
        for i in range(60):
            trie_handler.add(f"1d{i + 1}")

        trie_handler.clean(limit=10)
        assert len(cache_info.trie) == 10, "trie data should be limited to clean-limit"

    def test_clean_halving_logic(self):
        info = DiceCacheInfo(rolls=[], reasons=[], initiative=0, trie={"1d10": 120, "1d10red": 1})
        handler = DiceCacheTrie(info)

        handler.clean(limit=50, max_count=100)

        assert info.trie["1d10"] == 60, "Largest should be halved"
        assert info.trie["1d10red"] >= 1, "Values should not drop under 1 after halving"

    def test_get_suggestions_no_match(self, trie_handler: DiceCacheTrie):
        suggestions = trie_handler.get_suggestions("99d99", limit=5)
        assert suggestions == [], "Non-existent trie data should return empty array"


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
        DiceCache.get(itr).cache = DiceCacheInfo([], [], 0, {})
        suggestions = DiceCache.get(itr).get_autocomplete_suggestions("")
        assert suggestions == [], "Suggestions should be empty when no data is present."

    def test_autocompletes_clean_dice_instead_of_cache(self, itr: Interaction):
        DiceCache.get(itr).cache = DiceCacheInfo([], [], 0, {})
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
