import dataclasses
from typing import Any

import discord
from discord.app_commands import Choice

from logic.config import Config
from logic.dnd.abstract import FuzzyMatchResult, fuzzy_matches
from logic.jsonhandler import JsonFolderHandler, JsonHandler
from methods import ChoicedEnum

HOMEBREW_PATH: str = "./temp/homebrew/"


class HomebrewEntryType(str, ChoicedEnum):
    ACTION = "action"
    BACKGROUND = "background"
    CLASS = "class"
    CONDITION = "condition"
    CREATURE = "creature"
    DEITY = "deity"
    FEAT = "feat"
    HAZARD = "hazard"
    ITEM = "item"
    LANGUAGE = "language"
    OBJECT = "object"
    RULE = "rule"
    SPECIES = "species"
    SPELL = "spell"
    TABLE = "table"
    VEHICLE = "vehicle"

    @property
    def emoji(self) -> str:
        emojis = {
            self.ACTION: "🏃",
            self.BACKGROUND: "📕",
            self.CLASS: "🧙‍♂️",
            self.CONDITION: "🤒",
            self.CREATURE: "🐉",
            self.DEITY: "👁️",
            self.FEAT: "🎖️",
            self.HAZARD: "🪤",
            self.ITEM: "🗡️",
            self.LANGUAGE: "💬",
            self.OBJECT: "🪨",
            self.RULE: "📜",
            self.SPECIES: "🧝",
            self.SPELL: "🔥",
            self.TABLE: "📊",
            self.VEHICLE: "⛵",
        }
        return emojis.get(self, "❓")


@dataclasses.dataclass
class HomebrewEntry:
    name: str
    author_id: int
    entry_type: HomebrewEntryType
    description: str
    select_description: str | None = None  # Description in dropdown menus

    @property
    def title(self) -> str:
        return f"{self.name} ({self.entry_type.title()})"

    @property
    def emoji(self) -> str:
        return self.entry_type.emoji

    def get_author(self, itr: discord.Interaction) -> discord.Member | None:
        if not itr.guild:
            return None
        return itr.guild.get_member(self.author_id)

    def can_manage(self, itr: discord.Interaction) -> bool:
        """Returns true/false depending on whether or not the user can manage this entry"""
        if itr.user.id == self.author_id:
            return True

        config = Config.get(itr)
        if config.user_is_admin_or_has_config_permissions(itr.user):
            return True
        if not isinstance(itr.user, discord.Member):
            return False  # You can only manage permissions in a guild
        return itr.user.guild_permissions.manage_messages

    @classmethod
    def fromdict(cls, data: Any) -> "HomebrewEntry":
        return cls(
            name=data["name"],
            author_id=data["author_id"],
            entry_type=HomebrewEntryType(
                data.get("entry_type", None) or data["object_type"]
            ),  # Name conversion requires support for old format.
            description=data["description"],
            select_description=data["select_description"],
        )


class HomebrewGuildData(JsonHandler[list[HomebrewEntry]]):
    guild_id: int

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        super().__init__(filename=str(guild_id), sub_dir="homebrew")

    def deserialize(self, obj: Any) -> list[HomebrewEntry]:
        return [HomebrewEntry.fromdict(o) for o in obj]

    def _find(self, name: str) -> HomebrewEntry | None:
        for _, items in self.data.items():
            for item in items:
                if name.lower() != item.name.lower():
                    continue
                return item
        return None

    def add(
        self,
        itr: discord.Interaction,
        entry_type: HomebrewEntryType,
        name: str,
        select_description: str | None,
        description: str,
    ) -> HomebrewEntry:
        if not itr.guild:
            raise ValueError("Can only add homebrew content to a server!")
        if self._find(name):
            raise ValueError(f"A homebrew entry with the name '{name}' already exists!")

        author_id = itr.user.id
        new_entry = HomebrewEntry(
            entry_type=entry_type,
            name=name,
            select_description=select_description,
            description=description,
            author_id=author_id,
        )
        if entry_type not in self.data:
            self.data[entry_type] = []
        self.data[entry_type].append(new_entry)
        self.save()
        return new_entry

    def delete(self, itr: discord.Interaction, name: str) -> HomebrewEntry:
        entry_to_delete = self._find(name)
        if entry_to_delete is None:
            raise ValueError(f"Could not delete homebrew entry '{name}', entry does not exist.")
        if not entry_to_delete.can_manage(itr):
            raise ValueError("You do not have permission to remove this homebrew entry.")

        key = entry_to_delete.entry_type
        self.data[key].remove(entry_to_delete)
        self.save()
        return entry_to_delete

    def edit(
        self, itr: discord.Interaction, entry: HomebrewEntry, name: str, select_description: str | None, description: str
    ) -> HomebrewEntry:
        if not entry.can_manage(itr):
            raise ValueError("You do not have permission to edit this homebrew entry.")

        key = entry.entry_type
        edited_entry = HomebrewEntry(
            entry_type=entry.entry_type,
            name=name,
            select_description=select_description,
            description=description,
            author_id=entry.author_id,
        )
        self.data[key].remove(entry)
        self.data[key].append(edited_entry)
        self.save()
        return edited_entry

    def get(self, entry_name: str) -> HomebrewEntry:
        entry = self._find(entry_name)
        if entry is None:
            raise ValueError(f"No homebrew entry with the name '{entry_name}' found!")
        return entry

    def get_all(self, type_filter: HomebrewEntryType | None) -> list[HomebrewEntry]:
        entries: list[HomebrewEntry] = []
        for key, items in self.data.items():
            if type_filter and type_filter != key:
                continue
            entries.extend(items)
        return entries

    def get_autocomplete_suggestions(
        self,
        itr: discord.Interaction,
        query: str,
        fuzzy_threshold: float = 75,
        limit: int = 25,
    ) -> list[Choice[str]]:
        query = query.strip().lower().replace(" ", "")

        if query == "":
            return []

        choices: list[FuzzyMatchResult] = []
        for entries in self.data.values():
            for entry in entries:
                if not entry.can_manage(itr):
                    continue

                choice = fuzzy_matches(query, entry.name, fuzzy_threshold)
                if choice is not None:
                    choices.append(choice)

        # Sort by query match => fuzzy score => alphabetically
        choices.sort(key=lambda x: (-x.starts_with, -x.score, x.choice.name))
        return [choice.choice for choice in choices[:limit]]


class GlobalHomebrewData(JsonFolderHandler[HomebrewGuildData]):
    _handler_type = HomebrewGuildData

    def _itr_key(self, itr: discord.Interaction) -> int:
        if not itr.guild_id:
            raise ValueError("Can only get homebrew content in a server!")
        return itr.guild_id


HomebrewData = GlobalHomebrewData()
