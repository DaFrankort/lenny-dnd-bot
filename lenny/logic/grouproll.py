import time

import discord
from discord import Interaction

from logic.roll import Advantage, RollResult, parse, roll


class GroupRollRoll:
    name: str
    roll: RollResult
    modifier: str
    advantage: Advantage
    is_npc: bool
    owner: discord.User | discord.Member
    time_added: float

    def __init__(self, itr: Interaction, name: str | None, modifier: str, advantage: Advantage):
        self.is_npc = name is not None
        self.name = (name or itr.user.display_name).title().strip()
        self.advantage = advantage
        self.owner = itr.user
        self.modifier = modifier
        self.time_added = time.time()

        # Check if the modifier contains a d20 expression, e.g. "1d20 + 5". In this case, the user
        # most likely made a mistake and placed the entire expression, rather than just the modifier.
        expr, _ = parse(modifier, advantage=advantage)
        if expr.find_d20() is not None:
            self.roll = roll(modifier, advantage=advantage)
        else:
            self.roll = roll(f"1d20 + ({modifier})", advantage=advantage)

    @property
    def total(self) -> int:
        return self.roll.total

    def is_owner(self, user: discord.User | discord.Member) -> bool:
        return self.owner.id == user.id


class GroupRollSet:
    name: str
    total: int
    is_npc: bool
    owner: discord.User | discord.Member
    time_added: float

    def __init__(self, itr: Interaction, name: str | None, total: int):
        self.is_npc = name is not None
        self.name = (name or itr.user.display_name).title().strip()
        self.total = total
        self.owner = itr.user
        self.time_added = time.time()

    def is_owner(self, user: discord.User | discord.Member) -> bool:
        return self.owner.id == user.id


GroupRoll = GroupRollRoll | GroupRollSet
