import copy
import dataclasses
from typing import Any

import pytest
from jsonhandler import JsonHandler


@dataclasses.dataclass
class ComplexClass(object):
    a: int
    b: str
    c: float


class SimpleJsonHandler(JsonHandler[list[str]]):
    """This is a basic implementation of JsonHandler, meant to deal with simple data. As such, it is not needed to implement a deserialize method."""

    def __init__(self):
        super().__init__("test1")


class ComplexJsonHandler(JsonHandler[ComplexClass]):
    """This is an implementation of JsonHandler with a complexer class. A deserialize method is implemented."""

    def __init__(self):
        super().__init__("test2")

    def deserialize(self, obj: Any) -> ComplexClass:
        return ComplexClass(a=obj["a"], b=obj["b"], c=obj["c"])


class UnimplementedComplexJsonHandler(JsonHandler[ComplexClass]):
    """This is an implementation of JsonHandler with a complexer class. A deserialize method is *not* implemented."""

    def __init__(self):
        super().__init__("test3")


class TestJsonHandler:
    @pytest.fixture
    def handler(self) -> SimpleJsonHandler:
        handler = SimpleJsonHandler()
        handler.data.clear()
        handler.save()
        return handler

    @pytest.fixture
    def complex(self) -> ComplexJsonHandler:
        complex = ComplexJsonHandler()
        complex.data.clear()
        complex.save()
        return complex

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

    def test_complex_json_handler(self, complex: ComplexJsonHandler) -> None:
        complex.data["1"] = ComplexClass(1, "2", 3.0)
        complex.save()

        complex.data.clear()

        complex.load()
        assert complex.data["1"].a == 1
        assert complex.data["1"].b == "2"
        assert complex.data["1"].c == 3.0

    def test_unimplemented_complex_will_throw_error(self):
        with pytest.raises(NotImplementedError):
            unimplemented = UnimplementedComplexJsonHandler()
            unimplemented.save()
            unimplemented.load()
