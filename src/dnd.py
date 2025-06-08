from abc import abstractmethod
import json
import logging
import os.path

import discord
from rapidfuzz import fuzz
from discord.app_commands import Choice
from typing import Literal, Union, TypedDict


def is_source_phb2014(source: str) -> bool:
    return source in ["PHB", "DMG", "MM"]


def _read_dnd_data(path: str) -> list[dict]:
    if not os.path.exists(path):
        logging.warning(f"D&D data file not found: '{path}'")
        return []
    if not os.path.isfile(path):
        logging.warning(f"D&D data file is not a file: '{path}'")
        return []
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


class DescriptionTable(TypedDict):
    headers: list[str]
    rows: list[list[str]]


class Description(TypedDict):
    name: str
    type: Literal["text", "table"]
    value: Union[str, DescriptionTable]


class DNDObject(object):
    object_type: str
    name: str
    source: str
    url: str | None
    emoji: str = "❓"
    select_description: str | None = None  # Description in dropdown menus

    @property
    def is_phb2014(self) -> bool:
        return is_source_phb2014(self.source)

    @property
    def title(self) -> str:
        return f"{self.name} ({self.source})"

    @abstractmethod
    def get_embed(self) -> discord.Embed:
        pass


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
        for e in self.entries:
            if ignore_phb2014 and e.is_phb2014:
                continue

            name_clean = e.name.strip().lower().replace(" ", "")
            score = fuzz.partial_ratio(query, name_clean)
            if score > fuzzy_threshold:
                starts_with_query = name_clean.startswith(query)
                choices.append(
                    (starts_with_query, score, Choice(name=e.name, value=e.name))
                )

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
    description: list[Description]
    classes: list

    def __init__(self, json: any):
        self.object_type = "spell"
        self.emoji = "🔥"

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

        self.select_description = f"{self.level} {self.school}"

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

    @abstractmethod
    def get_embed(self) -> discord.Embed:
        from embeds import SpellEmbed

        return SpellEmbed(self)


class SpellList(DNDObjectList):
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
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = "item"
        self.emoji = "🗡️"

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

    @abstractmethod
    def get_embed(self) -> discord.Embed:
        from embeds import ItemEmbed

        return ItemEmbed(self)


class ItemList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/items.json"

    def __init__(self):
        super().__init__()
        data = _read_dnd_data(self.path)
        for item in data:
            self.entries.append(Item(item))


class Condition(DNDObject):
    description: list[Description]
    image: str | None

    def __init__(self, json: any):
        self.object_type = "condition"
        self.emoji = "💀"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.description = json["description"]
        self.image = json["image"]

    @abstractmethod
    def get_embed(self) -> discord.Embed:
        from embeds import ConditionEmbed

        return ConditionEmbed(self)


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
    subtitle: str | None
    summoned_by_spell: str | None
    token_url: str | None
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = "creature"
        self.emoji = "🐉"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.subtitle = json["subtitle"]
        self.summoned_by_spell = json["summonedBySpell"]
        self.token_url = json["tokenUrl"]
        self.description = json["description"]

        self.select_description = self.subtitle

    @abstractmethod
    def get_embed(self) -> discord.Embed:
        from embeds import CreatureEmbed

        return CreatureEmbed(self)


class CreatureList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/creatures.json"

    def __init__(self):
        super().__init__()
        for creature in _read_dnd_data(self.path):
            self.entries.append(Creature(creature))


class Rule(DNDObject):
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = "rule"
        self.emoji = "📜"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = f"{json['ruleType']} Rule"

        self.description = json["description"]

    @abstractmethod
    def get_embed(self) -> discord.Embed:
        from embeds import RuleEmbed

        return RuleEmbed(self)


class RuleList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/rules.json"

    def __init__(self):
        super().__init__()
        for rule in _read_dnd_data(self.path):
            self.entries.append(Rule(rule))


class Action(DNDObject):
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = "action"
        self.emoji = "🏃"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = json["time"]

        self.description = json["description"]

    @abstractmethod
    def get_embed(self) -> discord.Embed:
        from embeds import ActionEmbed

        return ActionEmbed(self)


class ActionList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/actions.json"

    def __init__(self):
        super().__init__()
        for action in _read_dnd_data(self.path):
            self.entries.append(Action(action))


class DNDData(object):
    spells: SpellList
    items: ItemList
    conditions: ConditionList
    creatures: CreatureList
    rules: RuleList
    actions: ActionList

    def __init__(self):
        self.spells = SpellList()
        self.items = ItemList()
        self.conditions = ConditionList()
        self.creatures = CreatureList()
        self.rules = RuleList()
        self.actions = ActionList()

    def __iter__(self):
        yield self.spells
        yield self.items
        yield self.conditions
        yield self.creatures
        yield self.rules
        yield self.actions


class DNDSearchResults(object):
    spells: list[Spell]
    items: list[Item]
    conditions: list[Condition]
    creatures: list[Creature]
    rules: list[Rule]
    actions: list[Action]
    _type_map: dict[type, list[DNDObject]]

    def __init__(self):
        self.spells = []
        self.items = []
        self.conditions = []
        self.creatures = []
        self.rules = []
        self.actions = []

        self._type_map = {
            Spell: self.spells,
            Item: self.items,
            Condition: self.conditions,
            Creature: self.creatures,
            Rule: self.rules,
            Action: self.actions,
        }

    def add(self, entry):
        for entry_type, result_list in self._type_map.items():
            if isinstance(entry, entry_type):
                result_list.append(entry)
                break

    def get_all(self) -> list[DNDObject]:
        all_entries = []
        for entries in self._type_map.values():
            all_entries.extend(entries)
        return all_entries

    def get_all_sorted(self) -> list[DNDObject]:
        return sorted(self.get_all(), key=lambda r: (r.object_type, r.name, r.source))

    def __len__(self) -> int:
        return len(self.get_all())
