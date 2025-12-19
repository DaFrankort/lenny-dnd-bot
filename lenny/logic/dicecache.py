import re
from dataclasses import dataclass
from typing import Any

import discord
from discord.app_commands import Choice

from logic.dnd.data import Data
from logic.jsonhandler import JsonFolderHandler, JsonHandler
from logic.voice_chat import SPECIAL_ROLL_REASONS


@dataclass
class DiceCacheInfo:
    rolls: list[str]
    reasons: list[str]
    initiative: int

    @classmethod
    def fromdict(cls, obj: Any) -> "DiceCacheInfo":
        return cls(
            rolls=obj.get("rolls", []),
            reasons=obj.get("reasons", []),
            initiative=obj.get("initiative", 0),
        )


class DiceCacheHandler(JsonHandler[DiceCacheInfo]):
    def __init__(self, user_id: int):
        super().__init__(str(user_id), "user_cache")
        if not self.data:
            self.cache = DiceCacheInfo(rolls=[], reasons=[], initiative=0)

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
        if query and re.compile(r"^\d+d\d+$", re.IGNORECASE).match(query):
            suggestions.append(query)  # Suggest query if is clean dice
        suggestions.extend([roll for roll in reversed(rolls) if query in roll.lower()])

        return [Choice(name=roll, value=roll) for roll in suggestions[:25]]

    def get_autocomplete_reason_suggestions(self, query: str) -> list[Choice[str]]:
        """
        Returns auto-complete choices for the last reasons a user used when no query is given.
        If query is given, will suggest reasons containing the query.
        """
        last_used = self.cache.reasons
        if len(last_used) == 0:
            return []

        query = query.strip().lower().replace(" ", "")
        if query == "":
            return [Choice(name=expr, value=expr) for expr in reversed(last_used)]

        reasons = [r.title() for r in list(SPECIAL_ROLL_REASONS.keys())]
        for ability in Data.skills.get_abilities():
            for ability_variant in ("", "Check", "Save"):
                reasons.append(f"{ability} {ability_variant}".strip())
        for skill in Data.skills.get_autocomplete_suggestions(query, set(["XPHB"])):
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
