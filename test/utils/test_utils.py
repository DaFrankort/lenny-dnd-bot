from enum import Enum


def listify(value: any) -> list[any]:
    if isinstance(value, list):
        return value
    return [value]


def enum_values(enum: Enum) -> list[any]:
    return [e.value for e in enum]
