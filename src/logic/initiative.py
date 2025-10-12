import logging
import random
import time
import discord
from discord import Interaction, Message, NotFound
from rapidfuzz import fuzz
from discord.app_commands import Choice
from logic.roll import DiceRollMode


async def clean_up_old_message(message: Message, MAX_AGE: int = 600):
    """Cleans up old discord.Message objects, removing any that are younger than MAX_AGE (default = 10min) and removing the view of those that are older."""
    now = time.time()
    timestamp = message.created_at.timestamp()
    age = int(now - timestamp)

    if age > MAX_AGE:
        await message.edit(view=None)
        return

    try:
        await message.delete()
    except NotFound:
        logging.debug("Previous message was already been deleted!")


class Initiative:
    name: str
    d20: tuple[int, int]
    modifier: int
    roll_mode: DiceRollMode
    is_npc: bool
    owner: discord.User

    title: str
    description: str

    def __init__(
        self,
        itr: Interaction,
        modifier: int,
        name: str | None,
        roll_mode: DiceRollMode,
    ):
        self.is_npc = name is not None
        self.name = name or itr.user.display_name
        self.name = self.name.title().strip()
        self.roll_mode = roll_mode
        self.d20 = (random.randint(1, 20), random.randint(1, 20))
        self.modifier = modifier
        self.owner = itr.user

        self._set_title(True)
        self._set_description()

    def _set_title(self, rolled: bool) -> str:
        action_text = "rolled" if rolled else "set"
        title_parts = [f"{self.owner.display_name} {action_text} Initiative"]

        if self.is_npc:
            title_parts.append(f"for {self.name}")

        if self.roll_mode == DiceRollMode.Advantage:
            title_parts.append("with Advantage")

        elif self.roll_mode == DiceRollMode.Disadvantage:
            title_parts.append("with Disadvantage")

        self.title = " ".join(title_parts).strip() + "!"

    def _set_description(self):
        mod = self.modifier

        def get_roll_line(d20: int):
            if mod == 0:
                return ""

            total = d20 + mod
            mod_str = f"+ {mod}" if mod > 0 else f"- {-mod}"
            return f"- ``[{d20}] {mod_str}`` -> {total}\n"

        description = ""
        description += get_roll_line(self.d20[0])
        if self.roll_mode != DiceRollMode.Normal:
            description += get_roll_line(self.d20[1])
        description += f"\n**Initiative: {self.get_total()}**"

        self.description = description

    def get_total(self):
        roll = self.d20[0]

        if self.roll_mode == DiceRollMode.Advantage:
            roll = max(self.d20)

        elif self.roll_mode == DiceRollMode.Disadvantage:
            roll = min(self.d20)

        return roll + self.modifier

    def set_value(self, value: int):
        d20 = max(1, min(20, value))
        self.d20 = (d20, d20)
        self.modifier = value - d20
        self._set_title(False)
        self._set_description()


class InitiativeTracker:
    server_initiatives: dict[int, list[Initiative]]
    server_messages: dict[int, Message]
    INITIATIVE_LIMIT = 30  # 4096/128 = 32 | 4096 Chars per description, max-name-length is 128 => lowered to 30 for safety.

    def __init__(self):
        self.server_initiatives = {}
        self.server_messages = {}

    def _sanitize_name(self, name: str) -> str:
        """Used to make name-comparisons less strict. (Case insensitive, no spaces)"""
        return name.strip().lower()

    async def set_message(self, itr: Interaction, message: Message):
        guild_id = int(itr.guild_id)
        prev_message = self.server_messages.get(guild_id, None)
        if prev_message is None:
            self.server_messages[guild_id] = message
            return

        is_new_message = prev_message != message
        if is_new_message:
            await clean_up_old_message(prev_message)
            self.server_messages[guild_id] = message

    def get(self, itr: Interaction) -> list[Initiative]:
        guild_id = int(itr.guild_id)
        return self.server_initiatives.get(guild_id, [])

    def add(self, itr: Interaction, initiative: Initiative) -> bool:
        """Adds an initiative to the tracker. Returns True if added successfully, otherwise False."""
        guild_id = int(itr.guild_id)
        if guild_id not in self.server_initiatives:
            self.server_initiatives[guild_id] = [initiative]
            return True

        existing = [
            s_initiative
            for s_initiative in self.server_initiatives[guild_id]
            if s_initiative.name == initiative.name
        ]
        self.server_initiatives[guild_id] = [  # Enforce unique names
            s_initiative
            for s_initiative in self.server_initiatives[guild_id]
            if not (s_initiative.name == initiative.name)
        ]

        # Limit protection (only if initiative is a new creature)
        is_new_entry = not existing
        exceeds_limit = len(self.server_initiatives[guild_id]) >= self.INITIATIVE_LIMIT
        if is_new_entry and exceeds_limit:
            return False

        insert_index = -1
        for i, s_initiative in enumerate(self.server_initiatives[guild_id]):
            if initiative.get_total() > s_initiative.get_total():
                insert_index = i
                break  # Insert user in correct place

        if insert_index == -1:
            self.server_initiatives[guild_id].append(initiative)
        else:
            self.server_initiatives[guild_id].insert(insert_index, initiative)
        return True

    def clear(self, itr: Interaction):
        guild_id = int(itr.guild_id)
        if guild_id in self.server_initiatives:
            del self.server_initiatives[guild_id]

    def get_autocomplete_suggestions(
        self,
        itr: Interaction,
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

    def remove(self, itr: Interaction, name: str | None) -> tuple[bool, str]:
        """Remove an initiative from the list. Returns a message and a success flag."""
        guild_id = int(itr.guild_id)
        if guild_id not in self.server_initiatives:
            return False, f"No initiatives to remove in {itr.guild.name.title()}."

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
                False,
                f"No initiatives found matching ``{name}``.\n Make sure targets are exact name-matches.",
            )

        if removal_index != -1:
            del self.server_initiatives[guild_id][removal_index]

        if len(self.server_initiatives[guild_id]) == 0:
            del self.server_initiatives[guild_id]

        if sanitized_name == self._sanitize_name(itr.user.display_name):
            return True, f"{itr.user.display_name} removed their own Initiative."
        return (
            True,
            f"{itr.user.display_name} removed Initiative for ``{name.title()}``.",
        )

    def add_bulk(
        self,
        itr: Interaction,
        modifier: int,
        name: str,
        amount: int,
        roll_mode: DiceRollMode,
        shared: bool,
    ) -> tuple[str, str, bool]:
        """Adds many initiatives to a server. Returns a title and description for the embed and a boolean to signify if everything was added succesfully."""
        guild_id = itr.guild_id
        initiative_count = amount + len(self.server_initiatives.get(guild_id, []))
        if initiative_count > self.INITIATIVE_LIMIT:
            return (
                "Bulk-add failed!",
                f"You attempted to add too many initiatives, max limit is {self.INITIATIVE_LIMIT}!",
                False,
            )

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

        title = f"{itr.user.display_name} rolled Initiative for {amount} {name.strip().title()}(s)"
        title += " with Advantage" if roll_mode == DiceRollMode.Advantage else ""
        title += " with Disadvantage" if roll_mode == DiceRollMode.Disadvantage else ""
        title += "!"

        return title, description, True
