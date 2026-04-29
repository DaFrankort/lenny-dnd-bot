from dataclasses import dataclass
from typing import Any

import pygtrie  # pyright: ignore[reportMissingTypeStubs]

from logic.jsonhandler import JsonHandler


@dataclass
class DiceTrie:
    trie: dict[str, int]


class DiceTrieCacheHandler(JsonHandler[DiceTrie]):
    def __init__(self):
        super().__init__(filename="dice_trie")

        data = self.data.get("global", DiceTrie(trie={})).trie
        self._trie = pygtrie.CharTrie(data)
        if len(self._trie) <= 0:
            self._init_trie_values()

    def _init_trie_values(self):
        """Default trie structure with commonly used expressions."""
        DEFAULT_DICE_EXPRESSIONS = {
            "1d10red": 5,  # Cyberpunk Red roll
            "1d8e8": 5,  # Sorcerous Burst
            "4d6kh3": 5,  # Stat rolling
            "2d20kh1": 10,  # Advantage
            "2d20kl1": 10,  # Disadvantage
            "2d4+2": 10,  # Potion of Healing
            "4d4+4": 10,  # Potion of Greater Healing
        }

        for expr, count in DEFAULT_DICE_EXPRESSIONS.items():
            self._trie[expr] = count

        self.data["global"] = DiceTrie(trie=dict(self._trie.items()))  # type: ignore
        self.save()

    def deserialize(self, obj: Any) -> DiceTrie:
        if isinstance(obj, dict):
            return DiceTrie(trie=obj.get("trie", {}))  # type: ignore
        return DiceTrie(trie={})

    def serialize(self, obj: DiceTrie):
        return super().serialize(obj)

    def add(self, expr: str) -> None:
        """Updates the trie with a new roll and saves to disk."""
        expr = expr.strip().lower().replace(" ", "")
        if not expr:
            return

        count = self._trie.get(expr, 0)  # type: ignore
        self._trie[expr] = count + 1
        self.data["global"] = DiceTrie(trie=dict(self._trie.items()))  # type: ignore
        self.save()

    def get_suggestions(self, expr: str, limit: int = 25) -> list[str]:
        expr = expr.strip().lower().replace(" ", "")
        if not expr:
            return []

        try:
            matches = list(self._trie.items(prefix=expr))  # type: ignore
            matches.sort(key=lambda item: item[1], reverse=True)  # type: ignore
            return [expression for expression, _ in matches[:limit]]  # type: ignore
        except KeyError:
            return []

    def clean(self, limit: int = 512):
        all_items = list(self._trie.items())  # type: ignore
        if len(all_items) <= limit:  # type: ignore
            return

        all_items.sort(key=lambda x: x[1], reverse=True)  # type: ignore
        keys_to_remove = [expr for expr, count in all_items[limit:]]  # type: ignore
        for key in keys_to_remove:  # type: ignore
            del self._trie[key]

        self.data["global"] = DiceTrie(trie=dict(self._trie.items()))  # type: ignore
        self.save()


DiceTrieCache = DiceTrieCacheHandler()
