import dataclasses
import logging
import os
from typing import Any, Set
import discord
from rapidfuzz import fuzz
from jsonhandler import JsonHandler
from methods import ChoicedEnum
from logic.config import user_is_admin_or_has_config_permissions
from discord.app_commands import Choice

HOMEBREW_PATH: str = "./temp/homebrew/"


class HomebrewEntryType(str, ChoicedEnum):
    ACTION = "action"
    BACKGROUND = "background"
    CLASS = "class"
    CONDITION = "condition"
    CREATURE = "creature"
    FEAT = "feat"
    ITEM = "item"
    LANGUAGE = "language"
    RULE = "rule"
    SPECIES = "species"
    SPELL = "spell"
    TABLE = "table"
    VEHICLE = "vehicle"
    OBJECT = "object"

    @property
    def emoji(self) -> str:
        emojis = {
            self.ACTION: "🏃",
            self.BACKGROUND: "📕",
            self.CLASS: "🧙‍♂️",
            self.CONDITION: "🤒",
            self.CREATURE: "🐉",
            self.FEAT: "🎖️",
            self.ITEM: "🗡️",
            self.LANGUAGE: "💬",
            self.RULE: "📜",
            self.SPECIES: "🧝",
            self.SPELL: "🔥",
            self.TABLE: "📊",
            self.VEHICLE: "⛵",
            self.OBJECT: "🪨",
        }
        return emojis.get(self, "❓")


@dataclasses.dataclass
class HomebrewEntry(object):
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
        if user_is_admin_or_has_config_permissions(itr.guild, itr.user):
            return True
        if not isinstance(itr.user, discord.Member):
            return False  # You can only manage permissions in a server
        return itr.user.guild_permissions.manage_messages

    @classmethod
    def fromdict(cls, data: Any) -> "HomebrewEntry":
        return cls(
            name=data["name"],
            author_id=data["author_id"],
            entry_type=HomebrewEntryType(data["entry_type"]),
            description=data["description"],
            select_description=data["select_description"],
        )


class HomebrewGuildData(JsonHandler[list[HomebrewEntry]]):
    server_id: int

    def __init__(self, server_id: int):
        self.server_id = server_id
        super().__init__(filename=str(server_id), sub_dir="homebrew")

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

        choices: list[tuple[bool, float, Choice[str]]] = []
        for key in self.data.keys():
            for e in self.data.get(key, []):
                if not e.can_manage(itr):
                    continue

                name_clean = e.name.strip().lower().replace(" ", "")
                score = fuzz.partial_ratio(query, name_clean)
                if score > fuzzy_threshold:
                    starts_with_query = name_clean.startswith(query)
                    choices.append(
                        (
                            starts_with_query,
                            score,
                            Choice(name=e.name, value=e.name),
                        )
                    )

        choices.sort(key=lambda x: (-x[0], -x[1], x[2].name))  # Sort by query match => fuzzy score => alphabetically
        return [choice for _, _, choice in choices[:limit]]


class GlobalHomebrewData:
    _data: dict[int, HomebrewGuildData] = {}

    def __init__(self):
        if not os.path.exists(HOMEBREW_PATH):
            os.makedirs(HOMEBREW_PATH)
            logging.info(f"Created homebrew directory at '{HOMEBREW_PATH}'")
            return

        for filename in os.listdir(HOMEBREW_PATH):
            if not filename.endswith(".json"):
                continue
            server_id = int(filename[:-5])
            self._data[server_id] = HomebrewGuildData(server_id)

    def get(self, itr: discord.Interaction) -> HomebrewGuildData:
        if not itr.guild_id:
            raise ValueError("Can only get homebrew content in a server!")
        if itr.guild_id not in self._data:
            self._data[itr.guild_id] = HomebrewGuildData(itr.guild_id)
        return self._data[itr.guild_id]

    @property
    def guilds(self) -> Set[int]:
        return set(self._data.keys())


HomebrewData = GlobalHomebrewData()
