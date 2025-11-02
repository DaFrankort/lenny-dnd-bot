import dataclasses
from logic.color import UserColor
from logic.dnd.data import Data
from logic.dnd.name import Gender


@dataclasses.dataclass
class NameGenResult(object):
    name: str
    desc: str
    color: int


def generate_name(species: str | None, gender: Gender | str) -> NameGenResult:
    gender = Gender(gender)
    name, new_species, new_gender = Data.names.get_random(species, gender)

    if name and new_species and new_gender:
        desc = f"*{new_gender.value} {new_species}*".title()
        color = UserColor.generate(name)
        return NameGenResult(name, desc, color)
    else:
        raise LookupError("Can't generate names at this time!")
