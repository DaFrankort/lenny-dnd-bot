import re
from dataclasses import dataclass
from typing import Any

import discord
import pygtrie  # pyright: ignore[reportMissingTypeStubs]
from discord.app_commands import Choice

from logic.dnd.data import Data
from logic.jsonhandler import JsonFolderHandler, JsonHandler
from logic.voice_chat import SPECIAL_ROLL_REASONS

DEFAULT_TRIE = {
    "1d10red": 5,  # Cyberpunk Red roll
    "1d8e8": 5,  # Sorcerous Burst
    "4d6kh3": 5,  # Stat rolling
    "2d20kh1": 10,  # Advantage
    "2d20kl1": 10,  # Disadvantage
    "2d4+2": 10,  # Potion of Healing
    "4d4+4": 10,  # Potion of Greater Healing
}


@dataclass
class DiceCacheInfo:
    rolls: list[str]
    reasons: list[str]
    initiative: int
    trie: dict[str, int]

    @classmethod
    def fromdict(cls, obj: Any) -> "DiceCacheInfo":
        return cls(
            rolls=obj.get("rolls", []),
            reasons=obj.get("reasons", []),
            initiative=obj.get("initiative", 0),
            trie=obj.get("trie", DEFAULT_TRIE),
        )


def normalize_expression(expression: str) -> str:
    # TODO Sorting dice expressions and merging compatible dice and modifiers could be beneficial.
    # e.g. 1d8+1d6+2d6+1+4 => 1d8+3d6+5
    return expression.strip().lower().replace(" ", "")


class DiceCacheTrie:
    _data: DiceCacheInfo

    def __init__(self, data: DiceCacheInfo):
        self._trie = pygtrie.CharTrie(data.trie)
        self._data = data

    def add(self, expression: str):
        expression = normalize_expression(expression)
        if not expression:
            return

        count: int = self._trie.get(expression, 0)  # type: ignore
        self._trie[expression] = count + 1
        self._data.trie = dict(self._trie.items())  # type: ignore

    def get_suggestions(self, expression: str, limit: int = 25) -> list[str]:
        expression = normalize_expression(expression)
        if not expression:
            return []

        try:
            matches = list(self._trie.items(prefix=expression))  # type: ignore
            matches.sort(key=lambda item: item[1], reverse=True)  # type: ignore
            return [expression for expression, _ in matches[:limit]]  # type: ignore
        except KeyError:
            return []

    def clean(self, limit: int = 50, max_count: int = 100):
        items = list(self._trie.items())  # type: ignore
        if len(items) <= limit:  # type: ignore
            return

        # If an expression has thousands of uses, it will just claim space and will
        # likely never be removed from the trie, removing newer expressions instead.
        # To make it easier for a user to 'clear' an expression from the trie, we
        # limit the max count and halve all counts if that limit is exceeded.
        if items and max(count for _, count in items) >= max_count:  # type: ignore
            for key in self._trie.keys():  # type: ignore
                self._trie[key] = max(1, self._trie[key] // 2)  # type: ignore
            items = list(self._trie.items())  # type: ignore

        # Remove least used counts
        items.sort(key=lambda x: x[1], reverse=True)  # type: ignore
        keys_to_remove = [expr for expr, _ in items[limit:]]  # type: ignore
        for key in keys_to_remove:  # type: ignore
            del self._trie[key]

        self._data.trie = dict(self._trie.items())  # type: ignore


class DiceCacheHandler(JsonHandler[DiceCacheInfo]):
    _trie: DiceCacheTrie

    def __init__(self, user_id: int):
        super().__init__(str(user_id), "user_cache")
        if not self.data:
            self.cache = DiceCacheInfo(rolls=[], reasons=[], initiative=0, trie={})  # TODO init trie data
        self._trie = DiceCacheTrie(self.cache)

    @property
    def cache(self) -> DiceCacheInfo:
        return self.data["dice"]

    @cache.setter
    def cache(self, new_cache: DiceCacheInfo):
        self.data["dice"] = new_cache

    def deserialize(self, obj: Any) -> DiceCacheInfo:
        return DiceCacheInfo.fromdict(obj)

    def store_expression(self, expression: str):
        """Stores a user's used diceroll input to the cache, if it is without errors."""
        if expression in self.cache.rolls:
            self.cache.rolls.remove(expression)
        self.cache.rolls.append(expression)

        self.cache.rolls = self.cache.rolls[-5:]  # Store max 5 expressions
        self._trie.add(expression)
        self.save()

    def store_reason(self, reason: str | None):
        if reason is None:
            return

        if reason in self.cache.reasons:
            self.cache.reasons.remove(reason)
        self.cache.reasons.append(reason)

        self.cache.reasons = self.cache.reasons[-5:]  # Store max 5 reasons
        self.save()

    def store_initiative(self, initiative: int):
        if initiative == self.cache.initiative:
            return
        self.cache.initiative = initiative
        self.save()

    def get_autocomplete_suggestions(self, query: str) -> list[Choice[str]]:
        """
        Returns auto-complete choices for the last roll expressions a user used when no query is given.
        """
        rolls = self.cache.rolls
        if len(rolls) == 0:
            return []

        query = query.strip().lower().replace(" ", "")
        suggestions: list[str] = []
        seen: set[str] = set()

        def add_suggestion(value: str) -> None:
            normalized = value.strip().lower().replace(" ", "")
            if not normalized:
                return
            if normalized in seen:
                return

            seen.add(normalized)
            suggestions.append(value)

        if query and re.compile(r"^\d+d\d+$", re.IGNORECASE).match(query):
            add_suggestion(query)  # Suggest query if is clean dice

        for roll in reversed(rolls):
            if query in roll.lower():
                add_suggestion(roll)

        for roll in self._trie.get_suggestions(query, 5):
            add_suggestion(roll)

        return [Choice(name=roll, value=roll) for roll in suggestions[:5]]

    def get_autocomplete_reason_suggestions(self, query: str) -> list[Choice[str]]:
        """
        Returns auto-complete choices for the last reasons a user used when no query is given.
        If query is given, will suggest reasons containing the query.
        """
        query = query.strip().lower().replace(" ", "")
        if query == "":
            last_used = self.cache.reasons
            if len(last_used) == 0:
                return []
            return [Choice(name=expr, value=expr) for expr in reversed(last_used)]

        reasons = [key.title() for key in SPECIAL_ROLL_REASONS]
        for ability in Data.skills.get_abilities():
            for ability_variant in ("", "Check", "Save"):
                reasons.append(f"{ability} {ability_variant}".strip())
        for skill in Data.skills.get_autocomplete_suggestions(query, set(["XPHB"])):
            if skill.value.lower() in SPECIAL_ROLL_REASONS:
                continue
            reasons.append(skill.value)

        filtered_reasons = sorted(
            [reason for reason in reasons if query.lower() in reason.lower()],
            key=lambda x: x.lower().index(query),
        )
        return [discord.app_commands.Choice(name=reason, value=reason) for reason in filtered_reasons[:25]]

    def get_last_initiative(self) -> int:
        return self.cache.initiative


class GlobalDiceCache(JsonFolderHandler[DiceCacheHandler]):
    _handler_type = DiceCacheHandler

    def _itr_key(self, itr: discord.Interaction) -> int:
        return itr.user.id


DiceCache = GlobalDiceCache()
