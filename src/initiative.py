import random
import discord

from user_colors import UserColor


class Initiative:
    name: str
    d20: int
    modifier: int
    is_npc: bool

    def __init__(self, itr: discord.Interaction, modifier: int, name: str | None):
        if name is None:
            name = itr.user.display_name  # Default to user's name
        self.name = name
        self.d20 = random.randint(1, 20)
        self.modifier = modifier
        self.is_npc = name is not None

    def get_total(self):
        return self.d20 + self.modifier


class InitiativeTracker:
    server_initiatives: dict[int, list[Initiative]]

    def __init__(self):
        self.server_initiatives = {}

    def get(self, itr: discord.Interaction) -> list[Initiative]:
        guild_id = int(itr.guild_id)
        return self.server_initiatives.get(guild_id, [])

    def add(self, itr: discord.Interaction, initiative: Initiative):
        guild_id = int(itr.guild_id)
        if guild_id not in self.server_initiatives:
            self.server_initiatives[guild_id] = [initiative]
            return

        self.server_initiatives[guild_id] = [  # Prevent duplicate users
            s_initiative
            for s_initiative in self.server_initiatives[guild_id]
            if not (s_initiative.name == initiative.name and not s_initiative.is_npc)
        ]

        insert_index = -1
        for i, s_initiative in enumerate(self.server_initiatives[guild_id]):
            if initiative.get_total() > s_initiative.get_total():
                insert_index = i
                break  # Insert user in correct place

        if insert_index == -1:
            self.server_initiatives[guild_id].append(initiative)
        else:
            self.server_initiatives[guild_id].insert(insert_index, initiative)

    def clear(self, itr: discord.Interaction):
        guild_id = int(itr.guild_id)
        if guild_id in self.server_initiatives:
            del self.server_initiatives[guild_id]


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
            type="rich", color=UserColor.get(itr), description=description
        ),
        self.set_author(name=title, icon_url=itr.user.avatar.url)


class InitiativeTrackerEmbed(discord.Embed):
    def __init__(self, itr: discord.Interaction, tracker: InitiativeTracker):
        description = ""
        for initiative in tracker.get(itr):
            total = initiative.get_total()
            description += f"- ``{total:>2}`` - {initiative.name}\n"

        super().__init__(
            title="Initiatives",
            type="rich",
            color=discord.Color.dark_green(),
            description=description,
        )
