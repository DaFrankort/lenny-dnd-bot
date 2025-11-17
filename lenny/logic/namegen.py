import dataclasses

from logic.dnd.data import Data
from logic.dnd.name import Gender


@dataclasses.dataclass
class NameGenResult:
    name: str
    species: str
    gender: str


def generate_name(species: str | None, gender: Gender | str) -> NameGenResult:
    gender = Gender(gender)
    name, new_species, new_gender = Data.names.get_random(species, gender)

    if name and new_species and new_gender:
        return NameGenResult(name, new_species, new_gender.value)

    raise LookupError("Can't generate names at this time!")
