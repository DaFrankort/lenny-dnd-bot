from typing import Any, List

from rapidfuzz import fuzz

from logic.dnd.abstract import DNDEntry
from logic.dnd.action import Action, ActionList
from logic.dnd.background import Background, BackgroundList
from logic.dnd.class_ import Class, ClassList
from logic.dnd.condition import Condition, ConditionList
from logic.dnd.creature import Creature, CreatureList
from logic.dnd.feat import Feat, FeatList
from logic.dnd.hazard import Hazard, HazardList
from logic.dnd.item import Item, ItemList
from logic.dnd.language import Language, LanguageList
from logic.dnd.name import NameTable
from logic.dnd.object import DNDObject, DNDObjectList
from logic.dnd.rule import Rule, RuleList
from logic.dnd.species import Species, SpeciesList
from logic.dnd.spell import Spell, SpellList
from logic.dnd.table import DNDTable, DNDTableList
from logic.dnd.vehicle import Vehicle, VehicleList


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
    vehicles: VehicleList
    objects: DNDObjectList
    hazards: HazardList

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
        self.vehicles = VehicleList()
        self.objects = DNDObjectList()
        self.hazards = HazardList()

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
        yield self.vehicles
        yield self.objects
        yield self.hazards

    def search(
        self,
        query: str,
        allowed_sources: set[str],
        threshold: float = 75.0,
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
    vehicles: list[Vehicle]
    objects: list[DNDObject]
    hazards: list[Hazard]
    _type_map: dict[type, List[Any]]

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
        self.vehicles = []
        self.objects = []
        self.hazards = []

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
            Vehicle: self.vehicles,
            DNDObject: self.objects,
            Hazard: self.hazards,
        }

    def add(self, entry: DNDEntry) -> None:
        for entry_type, result_list in self._type_map.items():
            if isinstance(entry, entry_type):
                result_list.append(entry)
                return

    def get_all(self) -> list[DNDEntry]:
        all_entries: list[DNDEntry] = []
        for entries in self._type_map.values():
            all_entries.extend(entries)
        return all_entries

    def get_all_sorted(self) -> list[DNDEntry]:
        return sorted(self.get_all(), key=lambda r: (r.entry_type, r.name, r.source))

    def __len__(self) -> int:
        return len(self.get_all())


Data = DNDData()
