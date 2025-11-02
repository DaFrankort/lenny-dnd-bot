import json
import os

from pathlib import Path
from discord import Interaction
import discord
from discord.app_commands import Choice


class DiceCache:
    PATH = Path("./temp/dice_cache.json")
    _data = {}  # cache in memory to avoid frequent file reads

    @classmethod
    def _get_user_data_template(cls) -> object:
        return {"last_used": [], "last_used_reason": []}

    @classmethod
    def _load_data(cls):
        if cls._data is not None:
            return cls._data
        if cls.PATH.exists():
            with cls.PATH.open("r") as f:
                cls._data = json.load(f)
        else:
            os.makedirs(os.path.dirname(cls.PATH), exist_ok=True)
            cls._data = {}
        return cls._data

    @classmethod
    def _save_data(cls):
        if cls._data is None:
            return
        with cls.PATH.open("w") as f:
            json.dump(cls._data, f, indent=4)

    @classmethod
    def store_expression(cls, itr: Interaction, expression: str):
        """Stores a user's used diceroll input to the cache, if it is without errors."""

        user_id = str(itr.user.id)
        data = cls._load_data()
        user_data = data.get(user_id, cls._get_user_data_template())
        last_used = user_data.get("last_used", [])
        if expression in last_used:
            last_used.remove(expression)
        last_used.append(expression)

        user_data["last_used"] = last_used[-5:]  # Store max 5 expressions
        data[user_id] = user_data
        cls._save_data()

    @classmethod
    def store_reason(cls, itr: Interaction, reason: str | None):
        if reason is None:
            return

        user_id = str(itr.user.id)
        data = cls._load_data()
        user_data = data.get(user_id, cls._get_user_data_template())
        last_used_reasons = user_data.get("last_used_reason", [])
        if reason in last_used_reasons:
            last_used_reasons.remove(reason)
        last_used_reasons.append(reason)

        user_data["last_used_reason"] = last_used_reasons[-5:]  # Store max 5 reasons
        data[user_id] = user_data
        cls._save_data()

    @classmethod
    def get_autocomplete_suggestions(cls, itr: Interaction, query: str) -> list[Choice[str]]:
        """
        Returns auto-complete choices for the last roll expressions a user used when no query is given.
        """
        user_id = str(itr.user.id)
        user_data = cls._load_data().get(user_id, cls._get_user_data_template())
        last_used = user_data.get("last_used", [])

        if len(last_used) == 0:
            return []

        query = query.strip().lower().replace(" ", "")
        filtered = [Choice(name=roll, value=roll) for roll in reversed(last_used) if query in roll.lower()]

        return filtered[:25]

    @classmethod
    def get_autocomplete_reason_suggestions(cls, itr: Interaction, query: str) -> list[Choice[str]]:
        """
        Returns auto-complete choices for the last reasons a user used when no query is given.
        If query is given, will suggest reasons containing the query.
        """
        user_id = str(itr.user.id)
        user_data = cls._load_data().get(user_id, cls._get_user_data_template())
        last_used = user_data.get("last_used_reason", [])

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
