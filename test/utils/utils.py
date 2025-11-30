from typing import Awaitable, Callable, List, TypeVar, Union

import discord

T = TypeVar("T")


def listify(value: Union[T, List[T]]) -> List[T]:
    if isinstance(value, list):
        return value  # type: ignore # Should return a list of value T
    return [value]


AutocompleteMethod = Callable[[discord.Interaction, str], Awaitable[list[discord.app_commands.Choice[str]]]]
