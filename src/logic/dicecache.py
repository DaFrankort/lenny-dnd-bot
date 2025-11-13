from dataclasses import dataclass
from typing import Any

import discord
from discord import Interaction
from discord.app_commands import Choice

from jsonhandler import JsonHandler


@dataclass
class DiceCacheInfo:
    last_used: list[str]
    last_used_reason: list[str]


class DiceCacheHandler(JsonHandler[DiceCacheInfo]):
    def __init__(self):
        super().__init__("dice_cache")

    def deserialize(self, obj: Any) -> DiceCacheInfo:
        return DiceCacheInfo(last_used=obj["last_used"], last_used_reason=obj["last_used_reason"])

    def store_expression(self, itr: Interaction, expression: str):
        """Stores a user's used diceroll input to the cache, if it is without errors."""

        user_id = str(itr.user.id)
        if user_id not in self.data:
            self.data[user_id] = DiceCacheInfo([expression], [])
            self.save()
            return

        if expression in self.data[user_id].last_used:
            self.data[user_id].last_used.remove(expression)
        self.data[user_id].last_used.append(expression)

        self.data[user_id].last_used = self.data[user_id].last_used[-5:]  # Store max 5 expressions
        self.save()

    def store_reason(self, itr: Interaction, reason: str | None):
        if reason is None:
            return

        user_id = str(itr.user.id)
        if user_id not in self.data:
            self.data[user_id] = DiceCacheInfo([], [reason])
            self.save()
            return

        if reason in self.data[user_id].last_used_reason:
            self.data[user_id].last_used_reason.remove(reason)
        self.data[user_id].last_used_reason.append(reason)

        self.data[user_id].last_used_reason = self.data[user_id].last_used_reason[-5:]  # Store max 5 reasons
        self.save()

    def get_autocomplete_suggestions(self, itr: Interaction, query: str) -> list[Choice[str]]:
        """
        Returns auto-complete choices for the last roll expressions a user used when no query is given.
        """
        user_id = str(itr.user.id)
        if user_id not in self.data:
            return []

        last_used = self.data[user_id].last_used
        if len(last_used) == 0:
            return []

        query = query.strip().lower().replace(" ", "")
        filtered = [Choice(name=roll, value=roll) for roll in reversed(last_used) if query in roll.lower()]

        return filtered[:25]

    def get_autocomplete_reason_suggestions(self, itr: Interaction, query: str) -> list[Choice[str]]:
        """
        Returns auto-complete choices for the last reasons a user used when no query is given.
        If query is given, will suggest reasons containing the query.
        """
        user_id = str(itr.user.id)
        if user_id not in self.data:
            return []

        last_used = self.data[user_id].last_used_reason
        if len(last_used) == 0:
            return []

        query = query.strip().lower().replace(" ", "")
        if query == "":
            return [Choice(name=expr, value=expr) for expr in reversed(last_used)]

        reasons = [
            "Attack",
            "Damage",
            "Strength",
            "Fire",
            "Healing",
            "Dexterity",
            "Constitution",
            "Intelligence",
            "Wisdom",
            "Charisma",
            "Saving Throw",
            "Athletics",
            "Acrobatics",
            "Sleight of Hand",
            "Stealth",
            "Arcana",
            "History",
            "Investigation",
            "Nature",
            "Religion",
            "Animal Handling",
            "Insight",
            "Medicine",
            "Perception",
            "Survival",
            "Deception",
            "Intimidation",
            "Performance",
            "Persuasion",
        ]
        filtered_reasons = sorted(
            [reason for reason in reasons if query.lower() in reason.lower()],
            key=lambda x: x.lower().index(query),
        )
        return [discord.app_commands.Choice(name=reason, value=reason) for reason in filtered_reasons[:25]]


DiceCache = DiceCacheHandler()
