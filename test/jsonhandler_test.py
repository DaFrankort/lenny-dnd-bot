import copy
from typing import Any

import pytest
from jsonhandler import JsonHandler


class SimpleJsonHandler(JsonHandler[list[str]]):
    """This is a basic implementation of JsonHandler, meant to deal with simple data."""

    def __init__(self):
        super().__init__("test")

    def deserialize(self, obj: Any) -> list[str]:
        return [str(o) for o in obj]


class TestJsonHandler:
    @pytest.fixture
    def handler(self) -> SimpleJsonHandler:
        handler = SimpleJsonHandler()
        handler.data.clear()
        handler.save()
        return handler

    def test_save_load(self, handler: SimpleJsonHandler) -> None:
        handler.data["spells"] = ["Fire Bolt", "Chain Lightning"]
        handler.data["items"] = ["Bow", "Arrow", "Arrow"]
        handler.save()

        new_handler = SimpleJsonHandler()
        assert "spells" in new_handler.data, "New handler should have 'spells' key."
        assert "items" in new_handler.data, "New handler should have 'items' key."

    def test_idempotent_load(self, handler: SimpleJsonHandler) -> None:
        """Test if loading after a save does not change the actual data."""

        handler.data["spells"] = ["Fire Bolt", "Chain Lightning"]
        handler.data["items"] = ["Bow", "Arrow", "Arrow"]

        dict1 = copy.deepcopy(handler.data)

        handler.save()
        handler.load()

        dict2 = copy.deepcopy(handler.data)

        assert len(dict1.keys()) == len(dict2.keys()), "Keys should be the same after saving and loading."

        for key, values1 in dict1.items():
            assert key in dict2.keys(), "Key should be in both keys list"

            values2 = dict2[key]
            assert all(
                v1 == v2 for v1, v2 in zip(values1, values2)
            ), "Contents of the values should be the same after saving and loading."

    def test_loading_without_save_does_not_maintain_data(self, handler: SimpleJsonHandler) -> None:
        handler.data["spells"] = ["Fire Bolt", "Chain Lightning"]
        handler.data["items"] = ["Bow", "Arrow", "Arrow"]
        handler.save()

        handler.data["skills"] = ["Athletics"]
        handler.load()

        assert "items" in handler.data, "Saved data should still exist."
        assert "spells" in handler.data, "Saved data should still exist."
        assert "skills" not in handler.data, "Loading without saving should not maintain contents."
