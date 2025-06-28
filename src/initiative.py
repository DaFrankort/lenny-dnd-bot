import random
import discord
from discord import Interaction

from dice import DiceRollMode
from embeds import SimpleEmbed
from rapidfuzz import fuzz
from discord.app_commands import Choice


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

    def __init__(self):
        self.server_initiatives = {}

    def _sanitize_name(self, name: str) -> str:
        """Used to make name-comparisons less strict. (Case insensitive, no spaces)"""
        return name.strip().lower()

    def get(self, itr: Interaction) -> list[Initiative]:
        guild_id = int(itr.guild_id)
        return self.server_initiatives.get(guild_id, [])

    def add(self, itr: Interaction, initiative: Initiative):
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

    def swap(self, itr: Interaction, target_a: str, target_b: str) -> tuple[str, bool]:
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

    def remove(self, itr: Interaction, name: str | None) -> tuple[str, bool]:
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
        itr: Interaction,
        modifier: int,
        name: str,
        amount: int,
        roll_mode: DiceRollMode,
        shared: bool,
    ) -> tuple[str, str]:
        """Adds many initiatives to a server. Returns a title and description for the embed."""
        title = f"{itr.user.display_name} rolled Initiative for {amount} {name.strip().title()}(s)"
        title += " with Advantage" if roll_mode == DiceRollMode.Advantage else ""
        title += " with Disadvantage" if roll_mode == DiceRollMode.Disadvantage else ""
        title += "!"

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


class InitiativeRollModal(discord.ui.Modal, title="Rolling for Initiative"):
    modifier = discord.ui.TextInput(
        label="Your Initiative Modifier", placeholder="0", max_length=2
    )
    mode = discord.ui.TextInput(
        label="Roll Mode (Normal by default)", placeholder="Advantage / Disadvantage", required=False, max_length=12
    )
    name = discord.ui.TextInput(
        label="Name (Username by default)", placeholder="Goblin", required=False, max_length=128
    )

    def __init__(self, itr: Interaction, tracker: InitiativeTracker, owner_id: int):
        super().__init__()
        self.itr = itr
        self.tracker = tracker
        self.owner_id = owner_id

    async def on_submit(self, itr: Interaction):
        name = str(self.name) or None
        try:
            modifier = int(str(self.modifier))
        except ValueError:
            await itr.response.send_message(
                "Initiative modifier must be a number without a decimals.",
                ephemeral=True,
            )
            return

        mode = DiceRollMode.Normal
        mode_input = str(self.mode).lower()
        if mode_input.startswith('a'):  # 'a' for Advantage
            mode = DiceRollMode.Advantage
        elif mode_input.startswith('d'):  # 'd' for Disadvantage
            mode = DiceRollMode.Disadvantage

        self.tracker.add(itr, Initiative(itr, modifier, name, mode))

        embed = InitiativeEmbed(itr, self.tracker, self.owner_id)
        await itr.response.edit_message(embed=embed, view=embed.view)
        await itr.followup.send("Initiative rolled!", ephemeral=True)


class InitiativeBulkModal(discord.ui.Modal, title="Adding Initiatives in Bulk"):
    modifier = discord.ui.TextInput(
        label="Creature's Initiative Modifier", placeholder="0", max_length=3
    )
    name = discord.ui.TextInput(
        label="Creature's Name", placeholder="Goblin", max_length=128
    )
    amount = discord.ui.TextInput(
        label="Amount of creatures to add", placeholder="1", max_length=2
    )
    mode = discord.ui.TextInput(
        label="Roll Mode (Normal by default)", placeholder="Advantage / Disadvantage", required=False, max_length=12
    )
    shared = discord.ui.TextInput(
        label="Share Initiative (False by default)", placeholder="True / False", required=False,  max_length=5
    )

    def __init__(self, itr: Interaction, tracker: InitiativeTracker, owner_id: int):
        super().__init__()
        self.itr = itr
        self.tracker = tracker
        self.owner_id = owner_id

    async def on_submit(self, itr: Interaction):
        name = str(self.name)
        try:
            modifier = int(str(self.modifier))
            amount = int(str(self.amount))
        except ValueError:
            await itr.response.send_message(
                "Modifier and Amount must be a number without a decimals.",
                ephemeral=True,
            )
            return
        mode = DiceRollMode.Normal
        mode_input = str(self.mode).lower()
        if mode_input.startswith('a'):  # 'a' for Advantage
            mode = DiceRollMode.Advantage
        elif mode_input.startswith('d'):  # 'd' for Disadvantage
            mode = DiceRollMode.Disadvantage

        shared = False
        shared_input = str(self.shared).lower()
        if shared_input.startswith("t"):  # 't' for True
            shared = True

        self.tracker.add_bulk(itr, modifier, name, amount, mode, shared)
        embed = InitiativeEmbed(itr, self.tracker, self.owner_id)
        await itr.response.edit_message(embed=embed, view=embed.view)

        additional_text = ""
        additional_text += "" if mode == DiceRollMode.Normal else f"with {mode.value.capitalize()} "
        additional_text += "using the same values " if shared else ""
        await itr.followup.send(f"Rolled Initiative {additional_text}for {amount} {name}(s) using ``1d20+{modifier}``.", ephemeral=True)


class InitiativeSetModal(discord.ui.Modal, title="Setting your Initiative value"):
    value = discord.ui.TextInput(
        label="Your Initiative value", placeholder="0",  max_length=3
    )
    name = discord.ui.TextInput(
        label="Name (Username by default)", placeholder="Goblin", required=False, max_length=128
    )

    def __init__(self, itr: Interaction, tracker: InitiativeTracker, owner_id: int):
        super().__init__()
        self.itr = itr
        self.tracker = tracker
        self.owner_id = owner_id

    async def on_submit(self, itr: Interaction):
        name = str(self.name) or None

        try:
            value = int(str(self.value))
        except ValueError:
            await itr.response.send_message(
                "Initiative value must be a number without a decimals.", ephemeral=True
            )
            return

        initiative = Initiative(itr, value, name, DiceRollMode.Normal)
        initiative.set_value(value)
        self.tracker.add(itr, initiative)

        embed = InitiativeEmbed(itr, self.tracker, self.owner_id)
        await itr.response.edit_message(embed=embed, view=embed.view)
        await itr.followup.send(f"Initiative set to {value}!", ephemeral=True)


class InitiativeClearConfirmModal(discord.ui.Modal, title="Are you sure you want to clear?"):
    confirm = discord.ui.TextInput(
        label="Type 'CLEAR' to confirm", placeholder="CLEAR"
    )

    def __init__(self, itr: Interaction, tracker: InitiativeTracker, owner_id: int):
        super().__init__()
        self.itr = itr
        self.tracker = tracker
        self.owner_id = owner_id

    async def on_submit(self, itr: Interaction):
        confirm = str(self.confirm)

        if confirm != 'CLEAR':
            await itr.response.send_message("Clearing cancelled, input 'CLEAR' in all caps to confirm.", ephemeral=True)
            return

        self.tracker.clear(itr)
        embed = InitiativeEmbed(itr, self.tracker, self.owner_id)
        await itr.response.edit_message(embed=embed, view=embed.view)
        await itr.followup.send("Initiatives cleared!", ephemeral=True)


class InitiativeView(discord.ui.View):
    def __init__(self, itr: Interaction, tracker: InitiativeTracker, owner_id: int):
        super().__init__(timeout=3600)  # Stop being responsive after 1 hour
        self.tracker = tracker
        self.owner_id = owner_id
        self.locked = False

    @discord.ui.button(
        label="Roll", style=discord.ButtonStyle.success, custom_id="roll_btn", row=0
    )
    async def roll_initiative(self, itr: Interaction, button: discord.ui.Button):
        await itr.response.send_modal(
            InitiativeRollModal(itr, self.tracker, self.owner_id)
        )

    @discord.ui.button(
        label="Set", style=discord.ButtonStyle.success, custom_id="set_btn", row=0
    )
    async def set_initiative(self, itr: Interaction, button: discord.ui.Button):
        await itr.response.send_modal(
            InitiativeSetModal(itr, self.tracker, self.owner_id)
        )

    @discord.ui.button(
        label="Delete Roll",
        style=discord.ButtonStyle.danger,
        custom_id="retract_btn",
        row=0,
    )
    async def remove_initiative(self, itr: Interaction, button: discord.ui.Button):
        self.tracker.remove(itr, None)
        embed = InitiativeEmbed(itr, self.tracker, self.owner_id)
        await itr.response.edit_message(embed=embed, view=embed.view)
        await itr.followup.send("Initiative removed!", ephemeral=True)

    @discord.ui.button(
        label="Bulk", style=discord.ButtonStyle.primary, custom_id="bulk_btn", row=1
    )
    async def bulk_roll_initiative(self, itr: Interaction, button: discord.ui.Button):
        await itr.response.send_modal(
            InitiativeBulkModal(itr, self.tracker, self.owner_id)
        )

    @discord.ui.button(
        label="Lock", style=discord.ButtonStyle.primary, custom_id="lock_btn", row=1
    )
    async def lock(self, itr: Interaction, button: discord.ui.Button):
        self.locked = not self.locked
        for child in self.children:
            if child.custom_id == "lock_btn":
                continue

            child.disabled = self.locked
            child.style = (
                discord.ButtonStyle.secondary
                if self.locked
                else {
                    "retract_btn": discord.ButtonStyle.danger,
                    "clear_btn": discord.ButtonStyle.danger,
                    "bulk_btn": discord.ButtonStyle.primary,
                }.get(child.custom_id, discord.ButtonStyle.success)
            )
        await itr.response.edit_message(view=self)

    @discord.ui.button(
        label="Clear Rolls",
        style=discord.ButtonStyle.danger,
        custom_id="clear_btn",
        row=1,
    )
    async def clear_initiative(self, itr: Interaction, button: discord.ui.Button):
        await itr.response.send_modal(InitiativeClearConfirmModal(itr, self.tracker, self.owner_id))


class InitiativeEmbed(SimpleEmbed):
    view: discord.ui.View

    def __init__(self, itr: Interaction, tracker: InitiativeTracker, owner_id: int):
        description = ""
        for initiative in tracker.get(itr):
            total = initiative.get_total()
            description += f"- ``{total:>2}`` - {initiative.name}\n"

        description = description or "*No initiatives rolled yet!*"

        super().__init__(
            title="Initiative - Get ready for Combat!", description=description
        )

        self.view = InitiativeView(itr, tracker, owner_id)
