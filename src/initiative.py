import random
import discord

from dice import DiceRollMode
from embeds import SimpleEmbed
from rapidfuzz import fuzz
from discord.app_commands import Choice


class Initiative:
    name: str
    d20: int
    modifier: int
    roll_mode: DiceRollMode
    is_npc: bool
    owner: discord.User

    title: str
    description: str

    def __init__(self, itr: discord.Interaction, modifier: int, name: str | None, roll_mode: DiceRollMode):
        self.is_npc = name is not None
        self.name = name or itr.user.display_name
        self.name = self.name.title().strip()
        self.roll_mode = roll_mode
        self._set_d20()
        self.modifier = modifier
        self.owner = itr.user

        self._set_title(True)
        self._set_description()

    def _set_d20(self):
        roll_1 = random.randint(1, 20)
        roll_2 = random.randint(1, 20)

        if self.roll_mode == DiceRollMode.Advantage:
            self.d20 = max(roll_1, roll_2)
        elif self.roll_mode == DiceRollMode.Disadvantage:
            self.d20 = min(roll_1, roll_2)
        else:
            self.d20 = roll_1

    def _set_title(self, rolled: bool) -> str:
        action_text = "rolled" if rolled else "set"
        title = f"{self.owner.display_name} {action_text} Initiative"

        title += f" for {self.name}" if self.is_npc else ''
        title += " with Advantage" if self.roll_mode == DiceRollMode.Advantage else ''
        title += " with Disadvantage" if self.roll_mode == DiceRollMode.Disadvantage else ''

        self.title = f"{title.strip()}!"

    def _set_description(self):
        mod = self.modifier
        d20 = self.d20
        total = self.get_total()

        description = ""
        if mod > 0:
            description = f"- ``[{d20}]+{mod}`` -> {total}\n"
        elif mod < 0:
            description = f"- ``[{d20}]-{-mod}`` -> {total}\n"
        description += f"Initiative: **{total}**"

        self.description = description

    def get_total(self):
        return self.d20 + self.modifier

    def set_value(self, value: int):
        self.d20 = max(1, min(20, value))
        self.modifier = value - self.d20
        self._set_title(False)
        self._set_description()


class InitiativeTracker:
    server_initiatives: dict[int, list[Initiative]]

    def __init__(self):
        self.server_initiatives = {}

    def _sanitize_name(self, name: str) -> str:
        """Used to make name-comparisons less strict. (Case insensitive, no spaces)"""
        return name.strip().lower()

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
        query = self._sanitize_name(query)

        if query == "":
            return []

        choices = []
        for e in self.get(itr):
            name_clean = self._sanitize_name(e.name)
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

    def swap(
        self, itr: discord.Interaction, target_a: str, target_b: str
    ) -> tuple[str, bool]:
        """
        Swaps the initiative values between two initiatives identified by their names.
        Returns a tuple containing a message string explaining the result of the swap and a boolean indicating whether the swap was successful.
        """

        target_a = self._sanitize_name(target_a)
        target_b = self._sanitize_name(target_b)

        if target_a == target_b:
            return (
                f"Cannot swap target with itself!\n``{target_a}`` was specified twice.",
                False,
            )

        index_a = -1
        index_b = -1
        for i, initiative in enumerate(self.get(itr)):
            name = self._sanitize_name(initiative.name)
            if name == target_a:
                index_a = i
            if name == target_b:
                index_b = i

        if index_a == -1 and index_b == -1:
            return (
                f"No initiatives found matching ``{target_a}`` or ``{target_b}``.\nMake sure targets are exact name-matches.",
                False,
            )
        elif index_a == -1:
            return (
                f"No initiatives found matching ``{target_a}``.\nMake sure targets are exact name-matches.",
                False,
            )
        elif index_b == -1:
            return (
                f"No initiatives found matching ``{target_b}``.\nMake sure targets are exact name-matches.",
                False,
            )

        initiatives = self.get(itr)
        initiative_a = initiatives[index_a]
        initiative_b = initiatives[index_b]

        prev_total_a = initiative_a.get_total()  # pre-swap values
        initiative_a.set_value(initiative_b.get_total())
        initiative_b.set_value(prev_total_a)

        guild_id = itr.guild_id  # Swap initiatives
        self.server_initiatives[guild_id][index_a] = initiative_b
        self.server_initiatives[guild_id][index_b] = initiative_a
        return (
            f"``{initiative_a.name}`` <=> ``{initiative_b.name}``",
            True,
        )

    def remove(self, itr: discord.Interaction, name: str | None) -> tuple[str, bool]:
        """Remove an initiative from the list. Returns a message and a success flag."""
        guild_id = int(itr.guild_id)
        if guild_id not in self.server_initiatives:
            return f"No initiatives to remove in {itr.guild.name.title()}.", False

        if name is None:
            name = itr.user.display_name

        sanitized_name = self._sanitize_name(name)

        removal_index = -1
        for i, e in enumerate(self.get(itr)):
            if self._sanitize_name(e.name) == sanitized_name:
                removal_index = i
                break

        if removal_index == -1:
            return (
                f"No initiatives found matching ``{name}``.\n Make sure targets are exact name-matches.",
                False,
            )

        if removal_index != -1:
            del self.server_initiatives[guild_id][removal_index]

        if len(self.server_initiatives[guild_id]) == 0:
            del self.server_initiatives[guild_id]

        if sanitized_name == self._sanitize_name(itr.user.display_name):
            return f"{itr.user.display_name} removed their own Initiative.", True
        return (
            f"{itr.user.display_name} removed Initiative for ``{name.title()}``.",
            True,
        )

    def add_bulk(
        self,
        itr: discord.Interaction,
        modifier: int,
        name: str,
        amount: int,
        roll_mode: DiceRollMode,
        shared: bool,
    ) -> tuple[str, str]:
        """Adds many initiatives to a server. Returns a title and description for the embed."""
        title = f"{itr.user.display_name} rolled Initiative for {amount} {name.strip().title()}(s)"
        title += " with Advantage" if roll_mode == DiceRollMode.Advantage else ''
        title += " with Disadvantage" if roll_mode == DiceRollMode.Disadvantage else ''
        title += '!'

        initiatives = []
        for i in range(amount):
            initiative = Initiative(itr, modifier, f"{name}", roll_mode)
            if shared and i != 0:
                initiative.d20 = initiatives[0].d20
            initiatives.append(initiative)

        initiatives.sort(key=lambda x: x.get_total(), reverse=True)
        description = ""
        for i, initiative in enumerate(initiatives):
            initiative.name += f" {i+1}"
            total = initiative.get_total()
            description += f"- ``{total:>2}`` - {initiative.name}\n"
            self.add(itr, initiative)

        return title, description


class InitiativeTrackerEmbed(SimpleEmbed):
    def __init__(self, itr: discord.Interaction, tracker: InitiativeTracker):
        description = ""
        for initiative in tracker.get(itr):
            total = initiative.get_total()
            description += f"- ``{total:>2}`` - {initiative.name}\n"

        super().__init__(
            title="Initiatives",
            description=description,
        ),
