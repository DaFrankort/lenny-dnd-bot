"""
Rewrite of pytest's approx, as pytest lacks the appropriate typing we require
in our project. This file introduces a new class named Approx, which can be
used to approximate numerical values.

A common example is `0.1 + 0.2 == 0.3`. Due to floating point imprecisions, this
assertion will typically fail. Instead, to solve this an epsilon comparison is
performed, namely `abs((0.3) - (0.1 + 0.2)) <= EPS`.

Approx is a class that overwrites the equality operator in order to force this
epsilon comparison.
"""

from typing import Union

TNumeric = Union[int, float]


class Approx:
    _value: TNumeric
    _eps: TNumeric

    def __init__(self, value: TNumeric, eps: TNumeric) -> None:
        super().__init__()
        self._value = value
        self._eps = eps

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TNumeric):
            return abs(other - self._value) <= self._eps

        return super().__eq__(other)


def approx(value: TNumeric, eps: TNumeric = 1e-6):
    return Approx(value, eps)
