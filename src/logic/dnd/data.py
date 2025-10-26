from typing import Iterable

import discord
from logic.dnd.abstract import DNDHomebrewObject, DNDObject, DNDObjectList, DNDObjectTypes
from logic.dnd.action import Action, ActionList
from logic.dnd.background import Background, BackgroundList
from logic.dnd.condition import Condition, ConditionList
from logic.dnd.creature import Creature, CreatureList
from logic.dnd.class_ import Class, ClassList
from logic.dnd.feat import Feat, FeatList
from logic.dnd.item import Item, ItemList
from logic.dnd.language import Language, LanguageList
from logic.dnd.name import NameTable
from logic.dnd.rule import Rule, RuleList
from logic.dnd.species import Species, SpeciesList
from logic.dnd.spell import Spell, SpellList
from logic.dnd.table import DNDTable, DNDTableList

from rapidfuzz import fuzz


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
    backgrounds: BackgroundList
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

    def __iter__(self) -> Iterable[DNDObjectList]:
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
        itr: discord.Interaction | None = None,
        threshold=75.0,
    ) -> "DNDSearchResults":
        query = query.strip().lower()
        results = DNDSearchResults()
        for entries in self:
            for entry in entries.get_entries(itr):
                name = entry.name.strip().lower()
                source = entry.source

                if source not in allowed_sources:
                    continue
                if fuzz.partial_ratio(query, name) > threshold:
                    results.add(entry)
        return results


class DNDSearchResults(object):
    spells: list[Spell | DNDHomebrewObject]
    items: list[Item | DNDHomebrewObject]
    conditions: list[Condition | DNDHomebrewObject]
    creatures: list[Creature | DNDHomebrewObject]
    classes: list[Class | DNDHomebrewObject]
    rules: list[Rule | DNDHomebrewObject]
    actions: list[Action | DNDHomebrewObject]
    feats: list[Feat | DNDHomebrewObject]
    languages: list[Language | DNDHomebrewObject]
    backgrounds: list[Background | DNDHomebrewObject]
    tables: list[DNDTable | DNDHomebrewObject]
    species: list[Species | DNDHomebrewObject]
    _type_map: dict[str, list[DNDObject | DNDHomebrewObject]]

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
            DNDObjectTypes.SPELL.value: self.spells,
            DNDObjectTypes.ITEM.value: self.items,
            DNDObjectTypes.CONDITION.value: self.conditions,
            DNDObjectTypes.CREATURE.value: self.creatures,
            DNDObjectTypes.CLASS.value: self.classes,
            DNDObjectTypes.RULE.value: self.rules,
            DNDObjectTypes.ACTION.value: self.actions,
            DNDObjectTypes.FEAT.value: self.feats,
            DNDObjectTypes.LANGUAGE.value: self.languages,
            DNDObjectTypes.BACKGROUND.value: self.backgrounds,
            DNDObjectTypes.TABLE.value: self.tables,
            DNDObjectTypes.SPECIES.value: self.species,
        }

    def add(self, entry):
        if entry.object_type in self._type_map:
            self._type_map[entry.object_type].append(entry)

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
