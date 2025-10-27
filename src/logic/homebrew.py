import json
import logging
import os
import discord
from rapidfuzz import fuzz
from logic.app_commands import ChoicedEnum
from logic.dnd.abstract import DNDObject


HOMEBREW_SOURCE: str = "HBRW"
HOMEBREW_PATH: str = "./temp/homebrew/"


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


class DNDHomebrewObject(DNDObject):
    object_type: str
    source: str = HOMEBREW_SOURCE
    _author_id: int

    name: str
    select_description: str | None = None  # Description in dropdown menus
    description: str

    def __init__(self, object_type: str, name: str, select_description: str | None, description: str, author_id: int):
        if select_description:
            select_description = select_description.strip()

        super().__init__()
        self.object_type = object_type
        self.name = name.title()
        self.select_description = select_description or None
        self.description = description
        self._author_id = author_id

    def get_author(self, itr: discord.Interaction) -> discord.Member | None:
        if not itr.guild:
            return None
        return itr.guild.get_member(self._author_id)

    def to_dict(self) -> dict:
        return {
            "object_type": self.object_type,
            "name": self.name,
            "select_description": self.select_description,
            "description": self.description,
            "author_id": self._author_id,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            object_type=d.get("object_type", ""),
            name=d.get("name", ""),
            select_description=d.get("select_description", ""),
            description=d.get("description", ""),
            author_id=int(d.get("author_id", 0)),
        )


class HomebrewGuildData:
    entries: dict[str, list[DNDHomebrewObject]]
    server_id: int

    def __init__(self, data: dict | None, server_id: int):
        self.server_id = server_id
        self.entries: dict[str, list[DNDHomebrewObject]] = {}

        if not data:
            for type in DNDObjectTypes:
                self.entries[type.value] = []
            self.save()
            return

        for key, items in data.items():
            objs: list[DNDHomebrewObject] = []
            for item in items:
                objs.append(DNDHomebrewObject.from_dict(item))
            self.entries[key] = objs

    @property
    def _file_path(self) -> str:
        return os.path.join(HOMEBREW_PATH, f"{self.server_id}.json")

    def save(self):
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
        entries = {k: [obj.to_dict() for obj in v] for k, v in self.entries.items()}
        with open(self._file_path, "w", encoding="utf-8") as file:
            json.dump(entries, file, indent=2)

    def add(
        self, itr: discord.Interaction, object_type: str, name: str, select_description: str | None, description: str
    ) -> DNDHomebrewObject:
        if not itr.guild:
            raise ValueError("Can only add homebrew content to a server!")

        for key in self.entries.keys():
            for entry in self.entries.get(key, []):
                if entry.name.lower() == name.lower():
                    raise ValueError(f"A homebrew entry with the name '{name}' already exists!")

        author_id = itr.user.id
        new_entry = DNDHomebrewObject(
            object_type=object_type,
            name=name,
            select_description=select_description,
            description=description,
            author_id=author_id,
        )
        self.entries[object_type].append(new_entry)
        self.save()
        return new_entry

    def get(self, entry_name: str) -> DNDHomebrewObject:
        for key in self.entries.keys():
            for entry in self.entries.get(key, []):
                if entry.name.lower() == entry_name.lower():
                    return entry
        raise ValueError(f"No homebrew entry with the name '{entry_name}' found!")

    def get_autocomplete_suggestions(
        self, query: str, fuzzy_threshold: float = 75, limit: int = 25
    ) -> list[discord.app_commands.Choice[str]]:
        query = query.strip().lower().replace(" ", "")

        if query == "":
            return []

        choices = []
        for key in self.entries.keys():
            for e in self.entries.get(key, []):
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

        choices.sort(key=lambda x: (-x[0], -x[1], x[2].name))  # Sort by query match => fuzzy score => alphabetically
        return [choice for _, _, choice in choices[:limit]]


class DNDHomebrewData:
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
            path = os.path.join(HOMEBREW_PATH, filename)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    self._data[server_id] = HomebrewGuildData(data, server_id)
            except Exception as e:
                logging.warning(f"Failed to load homebrew file '{path}': {e}")
                self._data[server_id] = HomebrewGuildData(None, server_id)

    def get(self, itr: discord.Interaction) -> HomebrewGuildData:
        if not itr.guild_id:
            raise ValueError("Can only get homebrew content in a server!")
        if itr.guild_id not in self._data:
            print("Not in data :(")
            self._data[itr.guild_id] = HomebrewGuildData(None, itr.guild_id)
        return self._data[itr.guild_id]


HomebrewData = DNDHomebrewData()
