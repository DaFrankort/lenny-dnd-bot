import json
import logging
import os.path

from rapidfuzz import fuzz
from discord.app_commands import Choice


def is_source_phb2014(source: str) -> bool:
    return source == "PHB" or source == "DMG"


def _read_dnd_data(path: str) -> list[dict]:
    if not os.path.exists(path):
        logging.warning(f"D&D data file not found: '{path}'")
        return []
    if not os.path.isfile(path):
        logging.warning(f"D&D data file is not a file: '{path}'")
        return []
    with open(path, "r") as file:
        return json.load(file)


class DNDObject(object):
    object_type: str
    name: str
    source: str
    url: str | None

    @property
    def is_phb2014(self) -> bool:
        return is_source_phb2014(self.source)


class DNDObjectList(object):
    entries: list[DNDObject]

    def __init__(self):
        self.entries = []

    def get(
        self, query: str, ignore_phb2014: bool = True, fuzzy_threshold: float = 75
    ) -> list[DNDObject]:
        query = query.strip().lower()
        exact: list[DNDObject] = []
        fuzzy: list[DNDObject] = []

        for entry in self.entries:
            if ignore_phb2014 and entry.is_phb2014:
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
        query: str = "",
        ignore_phb2014: bool = True,
        fuzzy_threshold: float = 75,
        limit: int = 25,
    ) -> list[Choice[str]]:
        query = query.strip().lower().replace(" ", "")

        if query == "":
            return []

        choices = []
        seen_names = set()

        for e in self.entries:
            if ignore_phb2014 and e.is_phb2014:
                continue

            name_clean = e.name.strip().lower().replace(" ", "")
            score = fuzz.partial_ratio(query, name_clean)
            if score > fuzzy_threshold and e.name not in seen_names:
                starts_with_query = name_clean.startswith(query)
                choices.append(
                    (starts_with_query, score, Choice(name=e.name, value=e.name))
                )
                seen_names.add(e.name)

        choices.sort(
            key=lambda x: (-x[0], -x[1], x[2].name)
        )  # Sort by query match => fuzzy score => alphabetically
        return [choice for _, _, choice in choices[:limit]]

    def search(
        self, query: str, ignore_phb2014: bool = True, fuzzy_threshold: float = 75
    ) -> list[DNDObject]:
        query = query.strip().lower()
        found: list[DNDObject] = []

        for entry in self.entries:
            if ignore_phb2014 and entry.is_phb2014:
                continue

            entry_name = entry.name.strip().lower()
            if fuzz.partial_ratio(query, entry_name) > fuzzy_threshold:
                found.append(entry)

        found = sorted(found, key=lambda e: (e.name, e.source))
        return found


class Spell(DNDObject):
    """A class representing a Dungeons & Dragons spell."""

    level: str
    school: str
    casting_time: str
    spell_range: str
    components: str
    duration: str
    description: list
    classes: list

    def __init__(self, json: any):
        self.object_type = "spell"
        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.level = json["level"]
        self.school = json["school"]
        self.casting_time = json["casting_time"]
        self.spell_range = json["range"]
        self.components = json["components"]
        self.duration = json["duration"]
        self.description = json["description"]
        self.classes = json["classes"]

    def __str__(self):
        return f"{self.name} ({self.source})"

    def __repr__(self):
        return str(self)

    def get_formatted_classes(self, ignore_phb2014: bool = True):
        classes = set()
        for class_ in self.classes:
            if ignore_phb2014 and is_source_phb2014(class_["source"]):
                continue
            classes.add(class_["name"])
        return ", ".join(sorted(list(classes)))

    @property
    def level_school(self) -> str:
        return f"{self.level} {self.school}"


class SpellList(DNDObjectList):
    """A class representing a list of Dungeons & Dragons spells."""

    path = "./submodules/lenny-dnd-data/generated/spells.json"

    def __init__(self):
        super().__init__()
        data = _read_dnd_data(self.path)
        for spell in data:
            self.entries.append(Spell(spell))


class Item(DNDObject):
    value: str | None
    weight: str | None
    type: list[str]
    properties: list[str]
    description: list[tuple[str, str]]

    def __init__(self, json: any):
        self.object_type = "item"
        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.value = json["value"]
        self.weight = json["weight"]
        self.type = json["type"]
        self.properties = json["properties"]
        self.description = json["description"]

    @property
    def formatted_value_weight(self) -> str | None:
        value_weight = []
        if self.value is not None:
            value_weight.append(self.value)
        if self.weight is not None:
            value_weight.append(self.weight)

        if len(value_weight) == 0:
            return None
        return ", ".join(value_weight)

    @property
    def formatted_type(self) -> str | None:
        if len(self.type) == 0:
            return None
        return ", ".join(self.type).capitalize()

    @property
    def formatted_properties(self) -> str | None:
        if len(self.properties) == 0:
            return None
        return ", ".join(self.properties).capitalize()


class ItemList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/items.json"

    def __init__(self):
        super().__init__()
        data = _read_dnd_data(self.path)
        for item in data:
            self.entries.append(Item(item))


class Condition(DNDObject):
    description: list[tuple[str, str]]
    image: str | None

    def __init__(self, json: any):
        self.object_type = "condition"
        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.description = json["description"]
        self.image = json["image"]


class ConditionList(DNDObjectList):
    paths = [
        "./submodules/lenny-dnd-data/generated/conditions.json",
        "./submodules/lenny-dnd-data/generated/diseases.json",
    ]

    def __init__(self):
        super().__init__()
        for path in self.paths:
            data = _read_dnd_data(path)
            for condition in data:
                self.entries.append(Condition(condition))


class Creature(DNDObject):
    name: str
    source: str
    subtitle: str | None
    summon_spell: str | None
    summon_spell_lvl: int | None
    url: str
    token_url: str | None
    description: list[tuple[str, str]] | None

    def __init__(self, json: any):
        self.object_type = "creature"
        self.name = json["name"]
        self.source = json["source"]
        self.subtitle = json["subtitle"]
        self.summon_spell = json["summoned_by_spell"]
        self.summon_spell_lvl = json["summoned_by_spell_level"]
        self.url = json["url"]
        self.token_url = json["token_url"]
        self.description = json["description"]


class CreatureList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/creatures.json"

    def __init__(self):
        super().__init__()
        data = _read_dnd_data(self.path)
        for creature in data:
            self.entries.append(Creature(creature))


class Class(DNDObject):
    name: str
    source: str
    url: str
    subclass_unlock_level: int | None
    descriptions: dict[str, list[tuple[str, str]]] | None
    subclass: dict[str, dict[str, list[tuple[str, str]]]] | None

    def __init__(self, json: any):
        self.object_type = "class"
        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.subclass_unlock_level = json["subclass_unlock_level"]
        self.descriptions = json.get("descriptions", None)
        self.subclass = json.get("subclass", None)

    def get_description(self, page: int, subclass: str | None) -> list[tuple[str, str]]:
        """Makes sure page number is within bounds and appends subclass information if available."""
        # 0 Is always base description, the rest are per-level.
        page = max(0, min(page, len(self.descriptions) - 1))
        page_key = str(page)

        descriptions = list(self.descriptions.get(page_key, []))
        if subclass:
            subclass_descriptions = self.subclass.get(subclass, {}).get(page_key, [])
            descriptions.extend(subclass_descriptions)

        return descriptions


class ClassList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/classes.json"

    def __init__(self):
        super().__init__()
        data = _read_dnd_data(self.path)
        for character_class in data:
            self.entries.append(Class(character_class))


class DNDData(object):
    spells: SpellList
    items: ItemList
    conditions: ConditionList
    creatures: CreatureList
    classes: ClassList

    def __init__(self):
        self.spells = SpellList()
        self.items = ItemList()
        self.conditions = ConditionList()
        self.creatures = CreatureList()
        self.classes = ClassList()


class DNDSearchResults(object):
    spells: list[Spell]
    items: list[Item]
    conditions: list[Condition]
    creatures: list[Creature]
    classes: list[Class]

    def __init__(self):
        self.spells = []
        self.items = []
        self.conditions = []
        self.creatures = []
        self.classes = []

    def get_all(self) -> list[DNDObject]:
        return self.spells + self.items + self.conditions + self.creatures + self.classes

    def get_all_sorted(self) -> list[DNDObject]:
        return sorted(self.get_all(), key=lambda r: (r.object_type, r.name, r.source))

    def __len__(self) -> int:
        return len(self.get_all())
