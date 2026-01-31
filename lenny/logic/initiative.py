import logging
import random

import discord
from discord import Forbidden, HTTPException, Interaction, Message, NotFound
from discord.app_commands import Choice
from rapidfuzz import fuzz

from logic.roll import Advantage


class Initiative:
    name: str
    raw_d20: tuple[int, int, int]
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
            # Three values, for elven accuracy
            self.raw_d20 = (random.randint(1, 20), random.randint(1, 20), random.randint(1, 20))
        else:
            self.raw_d20 = (roll, roll, roll)

    @property
    def rolls(self) -> list[int]:
        return list(self.raw_d20)[: self.advantage.roll_count]

    def get_total(self):
        roll = self.raw_d20[0]

        if self.advantage == Advantage.ADVANTAGE:
            roll = max(self.rolls)

        elif self.advantage == Advantage.DISADVANTAGE:
            roll = min(self.rolls)

        if self.advantage == Advantage.ELVEN_ACCURACY:
            roll = max(self.rolls)

        return roll + self.modifier

    def is_owner(self, user: discord.User | discord.Member) -> bool:
        return self.owner.id == user.id


class GlobalInitiativeTracker:
    channel_initiatives: dict[int, list[Initiative]]
    channel_messages: dict[int, int]
    INITIATIVE_LIMIT = 25  # Max options for a discord dropdown

    def __init__(self):
        self.channel_initiatives = {}
        self.channel_messages = {}

    def _sanitize_name(self, name: str) -> str:
        """Used to make name-comparisons less strict. (Case insensitive, no spaces)"""
        return name.strip().lower()

    async def set_message(self, itr: Interaction, message: Message) -> None:
        if not itr.channel or not itr.channel_id:
            return
        if not isinstance(itr.channel, discord.abc.Messageable):
            return  # Not a channel that can contain messages

        prev_message_id = self.channel_messages.get(itr.channel_id, None)
        if prev_message_id == message.id:
            return

        self.channel_messages[itr.channel_id] = message.id
        if prev_message_id is None:
            return

        try:
            prev_message: Message = await itr.channel.fetch_message(prev_message_id)
            if isinstance(prev_message, Message):
                await prev_message.delete()
        except NotFound:
            logging.error("Previous message was already been deleted!")
        except Forbidden:
            logging.error("Missing permissions to delete message!")
        except HTTPException as e:
            logging.error(f"Failed to delete message: {e}")

    def get(self, itr: Interaction) -> list[Initiative]:
        if not itr.channel_id:
            return []
        return self.channel_initiatives.get(itr.channel_id, [])

    def add(self, itr: Interaction, initiative: Initiative) -> Initiative:
        """Adds an initiative to the tracker."""
        if not itr.channel_id:
            raise RuntimeError("Initiatives can only be tracked in a server!")

        channel_id = int(itr.channel_id)
        if channel_id not in self.channel_initiatives:
            self.channel_initiatives[channel_id] = [initiative]
            return initiative

        existing = [
            s_initiative for s_initiative in self.channel_initiatives[channel_id] if s_initiative.name == initiative.name
        ]
        self.channel_initiatives[channel_id] = [  # Enforce unique names
            s_initiative for s_initiative in self.channel_initiatives[channel_id] if not (s_initiative.name == initiative.name)
        ]

        # Limit protection (only if initiative is a new creature)
        is_new_entry = not existing
        exceeds_limit = len(self.channel_initiatives[channel_id]) >= self.INITIATIVE_LIMIT
        if is_new_entry and exceeds_limit:
            raise RuntimeError("Maximum number of initiatives exceeded!")

        insert_index = -1
        for i, s_initiative in enumerate(self.channel_initiatives[channel_id]):
            if initiative.get_total() > s_initiative.get_total():
                insert_index = i
                break  # Insert user in correct place

        if insert_index == -1:
            self.channel_initiatives[channel_id].append(initiative)
        else:
            self.channel_initiatives[channel_id].insert(insert_index, initiative)

        return initiative

    def clear(self, itr: Interaction) -> None:
        if not itr.channel_id:
            return

        channel_id = int(itr.channel_id)
        if channel_id in self.channel_initiatives:
            del self.channel_initiatives[channel_id]

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

        choices: list[tuple[bool, float, Choice[str]]] = []
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
        if not itr.channel or not itr.channel_id:
            raise RuntimeError("Initiatives can only be tracked in a server!")

        channel_id = int(itr.channel_id)
        if channel_id not in self.channel_initiatives:
            raise RuntimeError("No initiatives to remove in this server.")

        name = name or itr.user.display_name
        sanitized_name = self._sanitize_name(name)

        removal_index = -1
        for i, e in enumerate(self.get(itr)):
            if self._sanitize_name(e.name) == sanitized_name:
                removal_index = i
                break

        if removal_index == -1:
            raise RuntimeError(f"No initiatives found matching ``{name}``.\n Make sure targets are exact name-matches.")

        initiative = self.channel_initiatives[channel_id][removal_index]
        del self.channel_initiatives[channel_id][removal_index]

        if len(self.channel_initiatives[channel_id]) == 0:
            del self.channel_initiatives[channel_id]

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
        """Adds many initiatives to a channel."""
        if not itr.channel_id:
            raise RuntimeError("Initiatives can only be tracked in a server!")

        channel_id = itr.channel_id
        channel_initiatives = self.channel_initiatives.get(channel_id, None) or []
        initiative_count = amount + len(channel_initiatives)
        if initiative_count > self.INITIATIVE_LIMIT:
            raise RuntimeError(f"You attempted to add too many initiatives, the max limit is {self.INITIATIVE_LIMIT}!")

        initiatives: list[Initiative] = []
        for i in range(amount):
            initiative = Initiative(itr, modifier, f"{name}", advantage)
            if shared and i != 0:
                initiative.raw_d20 = initiatives[0].raw_d20
            initiatives.append(initiative)

        initiatives.sort(key=lambda x: x.get_total(), reverse=True)
        for i, initiative in enumerate(initiatives):
            initiative.name += f" {i + 1}"
            self.add(itr, initiative)

        return initiatives


Initiatives = GlobalInitiativeTracker()
