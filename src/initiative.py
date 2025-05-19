import random
import discord

from user_colors import UserColor
from rapidfuzz import fuzz
from discord.app_commands import Choice


class Initiative:
    name: str
    d20: int
    modifier: int
    is_npc: bool

    def __init__(self, itr: discord.Interaction, modifier: int, name: str | None):
        self.is_npc = name is not None
        self.name = name or itr.user.display_name
        self.name = self.name.title().strip()
        self.d20 = random.randint(1, 20)
        self.modifier = modifier

    def get_total(self):
        return self.d20 + self.modifier

    def set_value(self, value: int):
        self.d20 = max(1, min(20, value))
        self.modifier = value - self.d20


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

        self.server_initiatives[guild_id] = [  # Enforce unique names
            s_initiative
            for s_initiative in self.server_initiatives[guild_id]
            if not (s_initiative.name == initiative.name)
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

    def get_autocomplete_suggestions(
        self,
        itr: discord.Interaction,
        query: str = "",
        fuzzy_threshold: float = 75,
        limit: int = 25,
    ) -> list[Choice[str]]:
        query = query.strip().lower().replace(" ", "")

        if query == "":
            return []

        choices = []
        for e in self.get(itr):
            name_clean = e.name.strip().lower().replace(" ", "")
            score = fuzz.partial_ratio(query, name_clean)
            if score > fuzzy_threshold:
                starts_with_query = name_clean.startswith(query)
                choices.append(
                    (starts_with_query, score, Choice(name=e.name, value=e.name))
                )

        choices.sort(
            key=lambda x: (-x[0], -x[1], x[2].name)
        )  # Sort by query match => fuzzy score => alphabetically
        return [choice for _, _, choice in choices[:limit]]

    def swap(self, itr: discord.Interaction, target_a: str, target_b: str):
        target_a = target_a.lower().strip()
        target_b = target_b.lower().strip()

        index_a = -1
        index_b = -1
        for i, initiative in enumerate(self.get(itr)):
            name = initiative.name.lower().strip()
            if target_a == name and index_a == -1:
                index_a = i
            if target_b == name and index_b == -1:
                index_b = i
            if index_a != -1 and index_b != -1:
                break

        if index_a == -1 or index_b == -1:
            missing = target_a if index_a == -1 else target_b
            return f"No initiatives found matching ``{missing}``.\n Make sure targets are exact name-matches."

        initiatives = self.get(itr)
        initiative_a = initiatives[index_a]
        initiative_b = initiatives[index_b]

        if index_a == index_b:
            return f"Cannot swap:\n both targets refer to the same initiative (``{initiative_a.name}``)."

        prev_total_a = initiative_a.get_total()  # pre-swap values
        initiative_a.set_value(initiative_b.get_total())
        initiative_b.set_value(prev_total_a)

        guild_id = itr.guild_id  # Swap initiatives
        self.server_initiatives[guild_id][index_a] = initiative_b
        self.server_initiatives[guild_id][index_b] = initiative_a
        return f"``{initiative_a.name}`` <=> ``{initiative_b.name}``\n**Swapped succesfully!**"


class InitiativeEmbed(discord.Embed):
    def __init__(self, itr: discord.Interaction, initiative: Initiative, rolled: bool):
        username = itr.user.display_name
        action_text = "rolled" if rolled else "set"

        if initiative.is_npc:
            title = f"{username} {action_text} Initiative for {initiative.name}!"
        else:
            title = f"{username} {action_text} Initiative!"

        mod = initiative.modifier
        d20 = initiative.d20
        total = initiative.get_total()

        description = ""
        if mod > 0:
            description = f"- ``[{d20}]+{mod}`` -> {total}\n"
        elif mod < 0:
            description = f"- ``[{d20}]-{-mod}`` -> {total}\n"
        description += f"Initiative: **{total}**"

        super().__init__(
            type="rich", color=UserColor.get(itr), description=description
        ),
        self.set_author(name=title, icon_url=itr.user.avatar.url)


class BulkInitiativeEmbed(discord.Embed):
    def __init__(
        self, itr: discord.Interaction, initiatives: list[Initiative], name: str
    ):
        username = itr.user.display_name

        title = f"{username} rolled Initiative for {len(initiatives)} {name}(s)!"

        description = ""
        for initiative in initiatives:
            total = initiative.get_total()
            description += f"- ``{total:>2}`` - {initiative.name}\n"

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
