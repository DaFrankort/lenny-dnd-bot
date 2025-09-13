from abc import abstractmethod
from enum import Enum
import json
import logging
import os.path
import random

import discord
from rapidfuzz import fuzz
from discord.app_commands import Choice
from typing import Literal, Union, TypedDict


def _read_dnd_data(path: str) -> list[dict]:
    if not os.path.exists(path):
        logging.warning(f"D&D data file not found: '{path}'")
        return []
    if not os.path.isfile(path):
        logging.warning(f"D&D data file is not a file: '{path}'")
        return []
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


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


class DNDObject(object):
    object_type: str
    name: str
    source: str
    url: str | None
    emoji: str = "❓"
    select_description: str | None = None  # Description in dropdown menus

    @property
    def title(self) -> str:
        return f"{self.name} ({self.source})"

    @abstractmethod
    def get_embed(
        self, itr: discord.Interaction
    ) -> discord.Embed | discord.ui.LayoutView:
        pass


class DNDObjectList(object):
    entries: list[DNDObject]

    def __init__(self):
        self.entries = []

    def get(
        self,
        query: str,
        allowed_sources: set[str],
        fuzzy_threshold: float = 75,
    ) -> list[DNDObject]:
        query = query.strip().lower()
        exact: list[DNDObject] = []
        fuzzy: list[DNDObject] = []

        for entry in self.entries:
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
        fuzzy_threshold: float = 75,
        limit: int = 25,
    ) -> list[Choice[str]]:
        query = query.strip().lower().replace(" ", "")

        if query == "":
            return []

        choices = []
        seen_names = set()  # Required to avoid duplicate suggestions
        for e in self.entries:
            if e.source not in allowed_sources:
                continue
            if e.name in seen_names:
                continue

            name_clean = e.name.strip().lower().replace(" ", "")
            score = fuzz.partial_ratio(query, name_clean)
            if score > fuzzy_threshold:
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
        self,
        query: str,
        allowed_sources: set[str],
        fuzzy_threshold: float = 75,
    ) -> list[DNDObject]:
        query = query.strip().lower()
        found: list[DNDObject] = []

        for entry in self.entries:
            if entry.source not in allowed_sources:
                continue

            entry_name = entry.name.strip().lower()
            if fuzz.partial_ratio(query, entry_name) > fuzzy_threshold:
                found.append(entry)

        found = sorted(found, key=lambda e: (e.name, e.source))
        return found


async def send_dnd_embed(itr: discord.Interaction, dnd_object: DNDObject):
    await itr.response.defer(thinking=False)
    embed = dnd_object.get_embed(itr=itr)
    file = embed.file or discord.interactions.MISSING

    if isinstance(embed, discord.ui.LayoutView):
        await itr.followup.send(view=embed, file=file)
        return

    view = embed.view or discord.interactions.MISSING
    await itr.followup.send(embed=embed, view=view, file=file)


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

    def get_formatted_classes(self, allowed_sources: set[str]):
        classes = set()
        for class_ in self.classes:
            if class_["source"] not in allowed_sources:
                continue
            classes.add(class_["name"])
        return ", ".join(sorted(list(classes)))

    @property
    def level_school(self) -> str:
        return f"{self.level} {self.school}"

    @abstractmethod
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import SpellEmbed

        return SpellEmbed(itr, self)


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
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import ItemEmbed

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
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import ConditionEmbed

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
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import CreatureEmbed

        return CreatureEmbed(self)


class CreatureList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/creatures.json"

    def __init__(self):
        super().__init__()
        for creature in _read_dnd_data(self.path):
            self.entries.append(Creature(creature))


class Class(DNDObject):
    subclass_unlock_level: int | None
    primary_ability: str | None
    spellcast_ability: str | None
    base_info: list[Description]
    level_resources: dict[str, list[Description]]
    level_features: dict[str, list[Description]]
    subclass_level_features: dict[str, dict[str, list[Description]]]

    def __init__(self, json: any):
        self.object_type = "class"
        self.emoji = "🧙‍♂️"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.subclass_unlock_level = json["subclassUnlockLevel"]
        self.primary_ability = json["primaryAbility"]
        self.spellcast_ability = json["spellcastAbility"]
        self.base_info = json["baseInfo"]
        self.level_resources = json["levelResources"]
        self.level_features = json["levelFeatures"]
        self.subclass_level_features = json["subclassLevelFeatures"]

    def __repr__(self):
        return str(self)

    @abstractmethod
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import ClassEmbed

        return ClassEmbed(self)


class ClassList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/classes.json"

    def __init__(self):
        super().__init__()
        for character_class in _read_dnd_data(self.path):
            self.entries.append(Class(character_class))


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
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import RuleEmbed

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
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import ActionEmbed

        return ActionEmbed(self)


class ActionList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/actions.json"

    def __init__(self):
        super().__init__()
        for action in _read_dnd_data(self.path):
            self.entries.append(Action(action))


class Feat(DNDObject):
    prerequisite: str | None
    ability_increase: str | None
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = "feat"
        self.emoji = "🎖️"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = json["type"]

        self.prerequisite = json["prerequisite"]
        self.ability_increase = json["abilityIncrease"]
        self.description = json["description"]

    @abstractmethod
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import FeatEmbed

        return FeatEmbed(self)


class FeatList(DNDObjectList):
    paths = [
        "./submodules/lenny-dnd-data/generated/feats.json",
        "./submodules/lenny-dnd-data/generated/classfeats.json",
    ]

    def __init__(self):
        super().__init__()
        for path in self.paths:
            for feat in _read_dnd_data(path):
                self.entries.append(Feat(feat))


class Language(DNDObject):
    speakers: str | None
    script: str | None
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = "language"
        self.emoji = "🗣️"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = json["type"]

        self.speakers = json["typicalSpeakers"]
        self.script = json["script"]
        self.description = json["description"]

    @abstractmethod
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import LanguageEmbed

        return LanguageEmbed(self)


class LanguageList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/languages.json"

    def __init__(self):
        super().__init__()
        for language in _read_dnd_data(self.path):
            self.entries.append(Language(language))


class Background(DNDObject):
    abilities: list[str] | None
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = "background"
        self.emoji = "📕"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.abilities = json["abilities"]
        self.description = json["description"]

    @abstractmethod
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import BackgroundEmbed

        return BackgroundEmbed(self)


class BackgroundList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/backgrounds.json"

    def __init__(self):
        super().__init__()
        for background in _read_dnd_data(self.path):
            self.entries.append(Background(background))


class DNDTable(DNDObject):
    dice_notation: str | None
    table: Description
    footnotes: list[str] | None

    def __init__(self, json: any):
        self.object_type = "table"
        self.emoji = "📊"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.dice_notation = json["roll"]
        self.table = json["table"]
        self.footnotes = json["footnotes"]

    @abstractmethod
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from components.table_containers import DNDTableContainerView

        return DNDTableContainerView(self)

    @property
    def is_rollable(self) -> bool:
        return self.dice_notation is not None

    def roll(self):  # -> tuple[list[str] | None, DiceExpression | None]:
        return None, None

        # Temporarily disabled
        # if not self.is_rollable:
        #     return None, None
        #
        # expression = DiceExpression(self.dice_notation)
        # result = expression.roll.value
        # rows = self.table["value"]["rows"]
        # for row in rows:
        #     range = row[0]
        #     if range["min"] <= result <= range["max"]:
        #         return row, expression
        # return None, expression


class DNDTableList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/tables.json"

    def __init__(self):
        super().__init__()
        for table in _read_dnd_data(self.path):
            self.entries.append(DNDTable(table))


class Species(DNDObject):
    image: str | None
    sizes: list[str]
    speed: list[str]
    type: str | None

    description: list[Description]
    info: list[Description]

    def __init__(self, json: any):
        self.object_type = "species"
        self.emoji = "🧝"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.image = json["image"]
        self.sizes = json["sizes"]
        self.speed = json["speed"]
        self.type = json["creatureType"]

        self.description = json["description"]
        self.info = json["info"]

    @abstractmethod
    def get_embed(self, itr: discord.Interaction) -> discord.Embed:
        from embeds2 import SpeciesEmbed

        return SpeciesEmbed(self)


class SpeciesList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/species.json"

    def __init__(self):
        super().__init__()
        for species in _read_dnd_data(self.path):
            self.entries.append(Species(species))


class Gender(Enum):
    FEMALE = "female"
    MALE = "male"
    OTHER = "other"


class NameTable:
    """Names supplied by 5etools, does not adhere to normal DNDObject format!"""

    path = "./submodules/lenny-dnd-data/generated/names.json"
    tables: dict[str, dict[str, list[str]]] = {}

    def __init__(self):
        data = _read_dnd_data(self.path)
        if len(data) == 0:
            self.tables = None
            return

        for d in data:
            species = d["name"].lower()
            table = {}
            table[Gender.FEMALE.value] = d["tables"]["female"]
            table[Gender.MALE.value] = d["tables"]["male"]
            table["family"] = d["tables"]["family"]

            self.tables[species] = table

    def get_random(
        self, species: str | None, gender: Gender
    ) -> tuple[str, str, Gender] | tuple[None, None, None]:
        """
        Species and gender are randomised if not specified.
        Returns the selected name, species and gender in a tuple.
        """
        if self.tables is None:
            return None, None, None

        if species:
            species = species.lower()

        table = self.tables.get(species, None)
        if table is None:
            species = random.choice(list(self.tables.keys()))
            table = self.tables.get(species)

        if gender is Gender.OTHER:
            gender = random.choice([Gender.FEMALE, Gender.MALE])

        names = table.get(gender.value, None)
        surnames = table.get("family", [])

        name = random.choice(names)
        if len(surnames) != 0:
            surname = random.choice(surnames)
            return f"{name} {surname}", species, gender
        return name, species, gender

    def get_species(self):
        return self.tables.keys()


class Source(object):
    """Note: this object does not inherit from DNDObject as it is meta data about DNDObjects"""

    id: str
    name: str
    source: str
    published: str
    author: str | None
    group: str

    def __init__(self, source: dict):
        self.id = source["id"]
        self.name = source["name"]
        self.source = source["source"]
        self.published = source["published"]
        self.author = source["author"]
        self.group = source["group"]


class SourceList(object):
    path = "./submodules/lenny-dnd-data/generated/sources.json"
    entries: list[Source]

    def __init__(self):
        data = _read_dnd_data(self.path)
        self.entries = [Source(e) for e in data]


class DNDData(object):
    spells: SpellList
    items: ItemList
    conditions: ConditionList
    creatures: CreatureList
    classes: ClassList
    rules: RuleList
    actions: ActionList
    feats: FeatList
    languages: LanguageList
    tables: DNDTableList
    species: SpeciesList

    names: NameTable

    def __init__(self):
        # LISTS
        self.spells = SpellList()
        self.items = ItemList()
        self.conditions = ConditionList()
        self.creatures = CreatureList()
        self.classes = ClassList()
        self.rules = RuleList()
        self.actions = ActionList()
        self.feats = FeatList()
        self.languages = LanguageList()
        self.backgrounds = BackgroundList()
        self.tables = DNDTableList()
        self.species = SpeciesList()

        # TABLES
        self.names = NameTable()

    def __iter__(self):
        yield self.spells
        yield self.items
        yield self.conditions
        yield self.creatures
        yield self.classes
        yield self.rules
        yield self.actions
        yield self.feats
        yield self.languages
        yield self.backgrounds
        yield self.tables
        yield self.species

    def search(
        self,
        query: str,
        allowed_sources: set[str],
        threshold=75.0,
    ) -> "DNDSearchResults":
        query = query.strip().lower()
        results = DNDSearchResults()
        for entries in self:
            for entry in entries.entries:
                name = entry.name.strip().lower()
                source = entry.source

                if source not in allowed_sources:
                    continue
                if fuzz.partial_ratio(query, name) > threshold:
                    results.add(entry)
        return results


class DNDSearchResults(object):
    spells: list[Spell]
    items: list[Item]
    conditions: list[Condition]
    creatures: list[Creature]
    classes: list[Class]
    rules: list[Rule]
    actions: list[Action]
    feats: list[Feat]
    languages: list[Language]
    backgrounds: list[Background]
    tables: list[DNDTable]
    species: list[Species]
    _type_map: dict[type, list[DNDObject]]

    def __init__(self):
        self.spells = []
        self.items = []
        self.conditions = []
        self.creatures = []
        self.classes = []
        self.rules = []
        self.actions = []
        self.feats = []
        self.languages = []
        self.backgrounds = []
        self.tables = []
        self.species = []

        self._type_map = {
            Spell: self.spells,
            Item: self.items,
            Condition: self.conditions,
            Creature: self.creatures,
            Class: self.classes,
            Rule: self.rules,
            Action: self.actions,
            Feat: self.feats,
            Language: self.languages,
            Background: self.backgrounds,
            DNDTable: self.tables,
            Species: self.species,
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


Data = DNDData()
