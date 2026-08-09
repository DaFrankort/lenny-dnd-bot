import time
import random

import discord
from discord import Interaction

from logic.roll import Advantage


class Initiative:
    name: str
    raw_d20: tuple[int, int, int]
    modifier: int
    advantage: Advantage
    is_npc: bool
    owner: discord.User | discord.Member
    time_added: float

    def __init__(self, itr: Interaction, modifier: int, name: str | None, advantage: Advantage, roll: int | None = None):
        self.is_npc = name is not None
        self.name = name or itr.user.display_name
        self.name = self.name.title().strip()
        self.advantage = advantage
        self.owner = itr.user
        self.modifier = modifier
        self.time_added = time.time()

        if roll is None:
            # Three values, for elven accuracy
            self.raw_d20 = (random.randint(1, 20), random.randint(1, 20), random.randint(1, 20))
        else:
            self.raw_d20 = (roll, roll, roll)

    @property
    def rolls(self) -> list[int]:
        return list(self.raw_d20)[: self.advantage.rolls]

    def get_total(self):
        roll = self.raw_d20[0]

        if self.advantage in [Advantage.ADVANTAGE, Advantage.SAVAGE_ATTACKER]:
            roll = max(self.rolls)

        elif self.advantage == Advantage.DISADVANTAGE:
            roll = min(self.rolls)

        if self.advantage == Advantage.ELVEN_ACCURACY:
            roll = max(self.rolls)

        return roll + self.modifier

    def is_owner(self, user: discord.User | discord.Member) -> bool:
        return self.owner.id == user.id
