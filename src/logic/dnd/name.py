import random

from command import ChoicedEnum
from logic.dnd.abstract import DNDObjectList


class Gender(ChoicedEnum):
    FEMALE = "female"
    MALE = "male"
    OTHER = "other"


class NameTable:
    """Names supplied by 5etools, does not adhere to normal DNDObject format!"""

    path = "./submodules/lenny-dnd-data/generated/names.json"
    tables: dict[str, dict[str, list[str]]] = {}

    def __init__(self):
        data = DNDObjectList.read_dnd_data_contents(self.path)
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

    def get_random(self, species: str | None, gender: Gender) -> tuple[str, str, Gender] | tuple[None, None, None]:
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
