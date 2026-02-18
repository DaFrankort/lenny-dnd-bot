import pytest

from logic.dnd.data import Data

ENTRY_LIST_PARAMS = [
    ("actions", Data.actions),
    ("backgrounds", Data.backgrounds),
    ("boons", Data.boons),
    ("classes", Data.classes),
    ("conditions", Data.conditions),
    ("creatures", Data.creatures),
    ("cults", Data.cults),
    ("deities", Data.deities),
    ("feats", Data.feats),
    ("hazards", Data.hazards),
    ("items", Data.items),
    ("objects", Data.objects),
    ("rules", Data.rules),
    ("skills", Data.skills),
    ("species", Data.species),
    ("spells", Data.spells),
    ("tables", Data.tables),
    ("vehicles", Data.vehicles),
]


def parametrize_entry_lists():
    """Adds a pytest parametrization for ``entry_list`` with type ``DNDEntryList`` of all possible lists."""
    return pytest.mark.parametrize(
        "entry_list",
        [v for _, v in ENTRY_LIST_PARAMS],
        ids=[k for k, _ in ENTRY_LIST_PARAMS],
    )
