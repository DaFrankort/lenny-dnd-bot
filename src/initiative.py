import random
import discord


class Initiative:
    name: str
    value: int
    modifier: int
    is_npc: bool

    def __init__(self, itr: discord.Interaction, modifier: int, name: str | None):
        self.is_valid = True
        self.modifier = modifier
        self.is_npc = name is not None

        if name is None:
            name = itr.user.display_name  # Default to user's name
        self.name = name
        self.roll()

    def roll(self):
        """Rolls and sets initiative value"""
        d20 = random.randint(1, 20)
        self.value = d20 + self.modifier
