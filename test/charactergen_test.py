import pytest
from logic.charactergen import generate_dnd_character
from logic.dnd.data import Data
from logic.dnd.name import Gender


class TestCharacterGen:
    @pytest.fixture
    def enabled(self) -> bool:
        return False

    def test_all_possible_combinations(self, enabled: bool):
        """Ensures all possible species, class, and gender combinations (in XPHB) are possible."""
        if not enabled:
            return

        species = [species for species in Data.species.entries if species.source == "XPHB"]
        classes = [class_ for class_ in Data.classes.entries if class_.source == "XPHB"]
        genders = Gender.values()

        for spec in species:
            for class_ in classes:
                for gender in genders:
                    generate_dnd_character(gender, spec.name, class_.name)
