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

        # TODO some basic initialization logic would be nice, like knowledge of basic dice expressions.
        self._trie = pygtrie.CharTrie(self.data.get("global", DiceTrie(trie={})).trie)

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


DiceTrieCache = DiceTrieCacheHandler()
