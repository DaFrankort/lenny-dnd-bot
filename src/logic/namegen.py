from dnd import Data, Gender
from user_colors import UserColor


class NameGenResult(object):
    name: str | None
    desc: str | None
    color: int | None

    def __init__(self):
        self.name = None
        self.desc = None
        self.color = None


def generate_name(species: str | None, gender: str) -> NameGenResult | None:
    result = NameGenResult()

    gender = Gender(gender)
    name, new_species, new_gender = Data.names.get_random(species, gender)

    if name and new_species and new_gender:
        result.name = name
        result.desc = f"*{new_gender.value} {new_species}*".title()
        result.color = UserColor.generate(name)
        return result
    else:
        raise LookupError("Can't generate names at this time")
