from typing import Any


def listify(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]
