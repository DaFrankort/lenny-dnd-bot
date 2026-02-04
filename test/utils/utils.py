from typing import List, TypeVar, Union


T = TypeVar("T")


def listify(value: Union[T, List[T]]) -> List[T]:
    if isinstance(value, list):
        return value  # type: ignore # Should return a list of value T
    return [value]
