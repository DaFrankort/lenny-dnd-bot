import random
import discord

from user_colors import UserColor


class Initiative:
    name: str
    d20: int
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
        self.d20 = random.randint(1, 20)

    def get_total(self):
        return self.d20 + self.modifier


class InitiativeEmbed(discord.Embed):
    def __init__(self, itr: discord.Interaction, initiative: Initiative):
        username = itr.user.display_name

        if initiative.is_npc:
            title = f"{username} rolled Initiative for {initiative.name}!"
        else:
            title = f"{username} rolled Initiative!"

        mod = initiative.modifier
        d20 = initiative.d20
        total = initiative.get_total()

        description = ""
        if mod > 0:
            description = f"- ``[{d20}]+{mod}`` -> {total}\n"
        elif mod < 0:
            description = f"- ``[{d20}]-{mod*-1}`` -> {total}\n"
        description += f"Initiative: **{total}**"

        super().__init__(
            type="rich",
            color=UserColor.get(itr),
            description=description
        ),
        self.set_author(name=title, icon_url=itr.user.avatar.url)
