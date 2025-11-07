import dataclasses
import random

from methods import ChoicedEnum
from logic.dnd.abstract import DNDEntryList


class Gender(str, ChoicedEnum):
    FEMALE = "female"
    MALE = "male"
    OTHER = "other"


@dataclasses.dataclass
class NameTableNames(object):
    male: list[str]
    female: list[str]
    family: list[str]

    def names(self, gender: Gender | None) -> list[str]:
        if gender == Gender.MALE:
            return self.male
        if gender == Gender.FEMALE:
            return self.female
        return self.male + self.female


class NameTable:
    """Names supplied by 5etools, does not adhere to normal DNDObject format!"""

    path = "./submodules/lenny-dnd-data/generated/names.json"
    tables: dict[str, NameTableNames]

    def __init__(self):
        self.tables = dict()
        data = DNDEntryList.read_dnd_data_contents(self.path)

        for datum in data:
            male = datum["tables"]["male"]
            female = datum["tables"]["female"]
            family = datum["tables"]["family"]

            species = datum["name"].lower()
            self.tables[species] = NameTableNames(male, female, family)

    def get_random(self, species: str | None, gender: Gender | None) -> tuple[str, str, Gender] | tuple[None, None, None]:
        """
        Species and gender are randomised if not specified.
        Returns the selected name, species and gender in a tuple.
        """
        if species is None or species not in self.tables:
            species = random.choice(list(self.tables.keys()))
        if gender is Gender.OTHER or gender is None:
            gender = random.choice([Gender.FEMALE, Gender.MALE])

        species = species.lower()
        table = self.tables.get(species, None)

        if table is None:
            return None, None, None

        names = table.names(gender)
        surnames = table.family

        name = random.choice(names)
        if len(surnames) != 0:
            surname = random.choice(surnames)
            return f"{name} {surname}", species, gender
        return name, species, gender

    def get_species(self):
        return self.tables.keys()
