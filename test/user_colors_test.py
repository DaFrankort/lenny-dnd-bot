import os
import discord
import pytest
from logic.color import UserColor
from utils.mocking import MockInteraction


class TestUserColor:
    @pytest.mark.parametrize(
        "hex_value, expected_result",
        [
            ("ffffff", True),
            ("#6c7e27", True),
            ("NOTAHEXVALUE", False),
            ("#1234567", False),
        ],
    )
    def test_validate(self, hex_value: str, expected_result: bool):
        assert (
            bool(UserColor.validate(hex_value)) == expected_result
        ), f"Validation failed for hex value: {hex_value}, should be {expected_result}"

    @pytest.mark.parametrize("hex_value", ["ffffff", "#6c7e27"])
    def test_parse(self, hex_value: str):
        parsed = UserColor.parse(hex_value)
        assert isinstance(parsed, int), "Parsed value is not an integer."

    @pytest.mark.parametrize("seed", [MockInteraction(), "Billy"])
    def test_generate(self, seed: discord.Interaction | str):
        generated_color = UserColor.generate(seed)
        assert isinstance(generated_color, int), "Generated color is not an integer."
        assert UserColor.validate(hex(generated_color)[2:]), "Generated color is not a valid hex value."

    def test_file_operations(self):
        interaction = MockInteraction()
        color = 7110183

        ORIGINAL_FILE_PATH = UserColor.FILE_PATH
        UserColor.FILE_PATH = ORIGINAL_FILE_PATH.replace(".json", "_test.json")
        if os.path.exists(UserColor.FILE_PATH):
            os.remove(UserColor.FILE_PATH)
        else:
            dirname = os.path.dirname(UserColor.FILE_PATH)
            os.makedirs(dirname, exist_ok=True)

        assert not os.path.exists(UserColor.FILE_PATH), "Test file should not exist before the test."

        # Assert random color generation, if no data
        random_color = UserColor.get(interaction)
        assert random_color != color, "If file has no color for user, it should return a generated one."

        # Test saving
        UserColor.save(interaction, color)
        assert os.path.exists(UserColor.FILE_PATH), "Test file should exist after saving."

        # Test getting color
        stored_color = UserColor.get(interaction)
        assert stored_color == color, f"Stored color {stored_color} does not match expected color {color}."
        assert os.path.exists(UserColor.FILE_PATH), "Test file should exist after getting color."

        # Test removing color
        remove_status = UserColor.remove(interaction)
        assert remove_status, "Failed to remove color from file."
        remove_status = UserColor.remove(interaction)
        assert not remove_status, "Removal should fail as color is already removed."

        os.remove(UserColor.FILE_PATH)
        UserColor.FILE_PATH = ORIGINAL_FILE_PATH
