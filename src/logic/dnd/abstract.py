import abc
import json
import logging
import os
from typing import Literal, TypedDict, Union
import discord
from rapidfuzz import fuzz

from logic.app_commands import ChoicedEnum


class DescriptionRowRange(TypedDict):
    type: Literal["range"]
    min: int
    max: int

    @property
    def notation(self) -> str:
        return f"{self['min']} - {self['max']}"


class DescriptionTable(TypedDict):
    headers: list[str]
    rows: list[list[str] | DescriptionRowRange]


class Description(TypedDict):
    name: str
    type: Literal["text", "table"]
    value: Union[str, DescriptionTable]


class DNDObjectTypes(ChoicedEnum):
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


DNDObjectEmojis = {
    DNDObjectTypes.ACTION.value: "🏃",
    DNDObjectTypes.BACKGROUND.value: "📕",
    DNDObjectTypes.CLASS.value: "🧙‍♂️",
    DNDObjectTypes.CONDITION.value: "🤒",
    DNDObjectTypes.CREATURE.value: "🐉",
    DNDObjectTypes.FEAT.value: "🎖️",
    DNDObjectTypes.ITEM.value: "🗡️",
    DNDObjectTypes.LANGUAGE.value: "💬",
    DNDObjectTypes.RULE.value: "📜",
    DNDObjectTypes.SPECIES.value: "🧝",
    DNDObjectTypes.SPELL.value: "🔥",
    DNDObjectTypes.TABLE.value: "📊",
}


class DNDObject(abc.ABC):
    object_type: str
    name: str
    source: str
    url: str | None
    select_description: str | None = None  # Description in dropdown menus

    @property
    def title(self) -> str:
        return f"{self.name} ({self.source})"

    @property
    def emoji(self) -> str:
        return DNDObjectEmojis.get(self.object_type, "❓")


class DNDHomebrewObject(DNDObject):
    object_type: str
    name: str
    source: str = "Homebrew"
    url: None = None
    select_description: str | None = None  # Description in dropdown menus

    description: str
    _author_id: int

    def __init__(self, object_type: str, name: str, select_description: str | None, description: str, author_id: int):
        super().__init__()
        self.object_type = object_type
        self.name = name
        self.select_description = select_description
        self.description = description
        self._author_id = author_id

    def get_author(self, itr: discord.Interaction) -> discord.Member | None:
        if not itr.guild:
            return None
        return itr.guild.get_member(self._author_id)

    def to_json(self) -> dict:
        return {
            "object_type": self.object_type,
            "name": self.name,
            "select_description": self.select_description,
            "description": self.description,
            "author_id": self._author_id,
        }


class DNDObjectList(abc.ABC):
    object_type: str
    entries: list[DNDObject]
    homebrew_entries: dict[int, list[DNDHomebrewObject]]
    homebrew_base_path: str = "./temp/homebrew/"

    def __init__(self, object_type: str, exclude_homebrew: bool = False):
        self.object_type = object_type
        self.entries = []
        self.homebrew_entries = {}
        if not exclude_homebrew:
            self._load_homebrew_entries()

    @staticmethod
    def read_dnd_data_contents(path: str) -> list[dict]:
        if not os.path.exists(path):
            logging.warning(f"D&D data file not found: '{path}'")
            return []
        if not os.path.isfile(path):
            logging.warning(f"D&D data file is not a file: '{path}'")
            return []
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _load_homebrew_entries(self):
        if not os.path.exists(self.homebrew_base_path):
            os.makedirs(self.homebrew_base_path)
            logging.info(f"Created homebrew directory at '{self.homebrew_base_path}'")
            return

        for filename in os.listdir(self.homebrew_base_path):
            if not filename.endswith(".json"):
                continue
            server_id = int(filename[:-5])  # Remove .json extension
            path = os.path.join(self.homebrew_base_path, filename)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if self.object_type in data:
                        self.homebrew_entries[server_id] = []
                        for entry_json in data[self.object_type]:
                            entry = DNDHomebrewObject(
                                object_type=self.object_type,
                                name=entry_json["name"],
                                select_description=entry_json["select_description"],
                                description=entry_json["description"],
                                author_id=int(entry_json["author_id"]),
                            )
                            self.homebrew_entries[server_id].append(entry)
            except Exception as e:
                logging.warning(f"Failed to load homebrew file '{path}': {e}")

    def add_homebrew_entry(
        self, itr: discord.Interaction, name: str, select_description: str | None, description: str
    ) -> DNDHomebrewObject:
        if itr.guild_id is None:
            raise ValueError("You can only add Homebrew data in a server.")
        guild_id = int(itr.guild_id)

        entry = DNDHomebrewObject(
            object_type=self.object_type,
            name=name,
            select_description=select_description,
            description=description,
            author_id=itr.user.id,
        )

        file_path = os.path.join(self.homebrew_base_path, f"{guild_id}.json")
        data = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

        if self.object_type not in data:
            data[self.object_type] = []
        data[self.object_type].append(entry.to_json())

        os.makedirs(self.homebrew_base_path, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        if guild_id not in self.homebrew_entries:
            self.homebrew_entries[guild_id] = []
        self.homebrew_entries[guild_id].append(entry)
        return entry

    def get(
        self,
        query: str,
        allowed_sources: set[str],
        itr: discord.Interaction | None = None,
        fuzzy_threshold: float = 75,
    ) -> list[DNDObject]:
        query = query.strip().lower()
        exact: list[DNDObject] = []
        fuzzy: list[DNDObject] = []

        for entry in self.get_entries(itr):
            if entry.source not in allowed_sources:
                continue

            entry_name = entry.name.strip().lower()
            if entry_name == query:
                exact.append(entry)
            if fuzz.ratio(query, entry_name) > fuzzy_threshold:
                fuzzy.append(entry)

        exact = sorted(exact, key=lambda e: (e.name, e.source))
        fuzzy = sorted(fuzzy, key=lambda e: (e.name, e.source))

        if len(exact) > 0:
            return exact
        return fuzzy

    def get_autocomplete_suggestions(
        self,
        query: str,
        allowed_sources: set[str],
        itr: discord.Interaction | None = None,
        fuzzy_threshold: float = 75,
        limit: int = 25,
    ) -> list[discord.app_commands.Choice[str]]:
        query = query.strip().lower().replace(" ", "")

        if query == "":
            return []

        choices = []
        seen_names = set()  # Required to avoid duplicate suggestions
        for e in self.get_entries(itr):
            if e.source not in allowed_sources:
                continue
            if e.name in seen_names:
                continue

            name_clean = e.name.strip().lower().replace(" ", "")
            score = fuzz.partial_ratio(query, name_clean)
            if score > fuzzy_threshold:
                starts_with_query = name_clean.startswith(query)
                choices.append(
                    (
                        starts_with_query,
                        score,
                        discord.app_commands.Choice(name=e.name, value=e.name),
                    )
                )
                seen_names.add(e.name)

        choices.sort(key=lambda x: (-x[0], -x[1], x[2].name))  # Sort by query match => fuzzy score => alphabetically
        return [choice for _, _, choice in choices[:limit]]

    def search(
        self,
        query: str,
        allowed_sources: set[str],
        itr: discord.Interaction | None = None,
        fuzzy_threshold: float = 75,
    ) -> list[DNDObject]:
        query = query.strip().lower()
        found: list[DNDObject] = []

        for entry in self.get_entries(itr):
            if entry.source not in allowed_sources:
                continue

            entry_name = entry.name.strip().lower()
            if fuzz.partial_ratio(query, entry_name) > fuzzy_threshold:
                found.append(entry)

        found = sorted(found, key=lambda e: (e.name, e.source))
        return found

    def get_entries(self, itr: discord.Interaction | None = None) -> list[DNDObject]:
        """Returns all entries with homebrew entries included if itr is provided."""
        entries = self.entries
        if itr is not None and itr.guild_id and itr.guild_id in self.homebrew_entries:
            entries.extend(self.homebrew_entries[int(itr.guild_id)])
        return entries
