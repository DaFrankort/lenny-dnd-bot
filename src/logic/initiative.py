import logging
import random
import time
import discord
from discord import Interaction, Message, NotFound
from rapidfuzz import fuzz
from discord.app_commands import Choice
from logic.roll import Advantage


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
    advantage: Advantage
    is_npc: bool
    owner: discord.User | discord.Member

    def __init__(self, itr: Interaction, modifier: int, name: str | None, advantage: Advantage, roll: int | None = None):
        self.is_npc = name is not None
        self.name = name or itr.user.display_name
        self.name = self.name.title().strip()
        self.advantage = advantage
        self.owner = itr.user
        self.modifier = modifier

        if roll is None:
            self.d20 = (random.randint(1, 20), random.randint(1, 20))
        else:
            self.d20 = (roll, roll)

    def get_total(self):
        roll = self.d20[0]

        if self.advantage == Advantage.Advantage:
            roll = max(self.d20)

        elif self.advantage == Advantage.Disadvantage:
            roll = min(self.d20)

        return roll + self.modifier


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

    async def set_message(self, itr: Interaction, message: Message) -> None:
        if not itr.guild_id:
            return

        prev_message = self.server_messages.get(itr.guild_id, None)
        if prev_message is None:
            self.server_messages[itr.guild_id] = message
            return

        is_new_message = prev_message != message
        if is_new_message:
            await clean_up_old_message(prev_message)
            self.server_messages[itr.guild_id] = message

    def get(self, itr: Interaction) -> list[Initiative]:
        if not itr.guild_id:
            return []
        return self.server_initiatives.get(itr.guild_id, [])

    def add(self, itr: Interaction, initiative: Initiative) -> Initiative:
        """Adds an initiative to the tracker."""
        if not itr.guild_id:
            raise RuntimeError("Initiatives can only be tracked in a server!")

        guild_id = int(itr.guild_id)
        if guild_id not in self.server_initiatives:
            self.server_initiatives[guild_id] = [initiative]
            return initiative

        existing = [s_initiative for s_initiative in self.server_initiatives[guild_id] if s_initiative.name == initiative.name]
        self.server_initiatives[guild_id] = [  # Enforce unique names
            s_initiative for s_initiative in self.server_initiatives[guild_id] if not (s_initiative.name == initiative.name)
        ]

        # Limit protection (only if initiative is a new creature)
        is_new_entry = not existing
        exceeds_limit = len(self.server_initiatives[guild_id]) >= self.INITIATIVE_LIMIT
        if is_new_entry and exceeds_limit:
            raise RuntimeError("Maximum number of initiatives exceeded!")

        insert_index = -1
        for i, s_initiative in enumerate(self.server_initiatives[guild_id]):
            if initiative.get_total() > s_initiative.get_total():
                insert_index = i
                break  # Insert user in correct place

        if insert_index == -1:
            self.server_initiatives[guild_id].append(initiative)
        else:
            self.server_initiatives[guild_id].insert(insert_index, initiative)

        return initiative

    def clear(self, itr: Interaction) -> None:
        if not itr.guild_id:
            return

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
                choices.append((starts_with_query, score, Choice(name=e.name, value=e.name)))

        choices.sort(key=lambda x: (-x[0], -x[1], x[2].name))  # Sort by query match => fuzzy score => alphabetically
        return [choice for _, _, choice in choices[:limit]]

    def remove(self, itr: Interaction, name: str | None) -> Initiative:
        """Remove an initiative from the list."""
        if not itr.guild or not itr.guild_id:
            raise RuntimeError("Initiatives can only be tracked in a server!")

        guild_id = int(itr.guild_id)
        if guild_id not in self.server_initiatives:
            raise RuntimeError(f"No initiatives to remove in {itr.guild.name.title()}.")

        name = name or itr.user.display_name
        sanitized_name = self._sanitize_name(name)

        removal_index = -1
        for i, e in enumerate(self.get(itr)):
            if self._sanitize_name(e.name) == sanitized_name:
                removal_index = i
                break

        if removal_index == -1:
            raise RuntimeError(f"No initiatives found matching ``{name}``.\n Make sure targets are exact name-matches.")

        initiative = self.server_initiatives[guild_id][removal_index]
        del self.server_initiatives[guild_id][removal_index]

        if len(self.server_initiatives[guild_id]) == 0:
            del self.server_initiatives[guild_id]

        return initiative

    def add_bulk(
        self,
        itr: Interaction,
        modifier: int,
        name: str,
        amount: int,
        advantage: Advantage,
        shared: bool,
    ) -> list[Initiative]:
        """Adds many initiatives to a server."""
        if not itr.guild_id:
            raise RuntimeError("Initiatives can only be tracked in a server!")

        guild_id = itr.guild_id
        server_initiatives = self.server_initiatives.get(guild_id, None) or []
        initiative_count = amount + len(server_initiatives)
        if initiative_count > self.INITIATIVE_LIMIT:
            raise RuntimeError(f"You attempted to add too many initiatives, the max limit is {self.INITIATIVE_LIMIT}!")

        initiatives = []
        for i in range(amount):
            initiative = Initiative(itr, modifier, f"{name}", advantage)
            if shared and i != 0:
                initiative.d20 = initiatives[0].d20
            initiatives.append(initiative)

        initiatives.sort(key=lambda x: x.get_total(), reverse=True)
        for i, initiative in enumerate(initiatives):
            initiative.name += f" {i+1}"
            total = initiative.get_total()
            self.add(itr, initiative)

        return initiatives
