import discord
from discord import Interaction, ui
from components.items import SimpleSeparator
from embeds.embed import SimpleEmbed, UserActionEmbed
from logic.initiative import Initiative, InitiativeTracker
from logic.roll import Advantage
from components.modals import SimpleModal
from logic.voice_chat import VC, SoundType
from logger import log_button_press


class _InitiativeModal(SimpleModal):
    def __init__(self, itr: Interaction, title: str, tracker: InitiativeTracker):
        super().__init__(itr, title)
        self.tracker = tracker


class InitiativeRollModal(_InitiativeModal):
    modifier = ui.TextInput["InitiativeRollModal"](
        label="Your Initiative Modifier", placeholder="0", max_length=2, required=False
    )
    name = ui.TextInput["InitiativeRollModal"](
        label="Name (Username by default)",
        placeholder="Goblin",
        required=False,
        max_length=128,
    )
    advantage = ui.TextInput["InitiativeRollModal"](
        label="Roll Mode (Normal by default)",
        placeholder="Advantage / Disadvantage",
        required=False,
        max_length=12,
    )

    def __init__(self, itr: Interaction, tracker: InitiativeTracker):
        super().__init__(itr, title="Rolling for Initiative", tracker=tracker)

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        modifier = self.get_int(self.modifier)
        if modifier is None:
            await itr.response.send_message("Initiative Modifier must be a number without decimals.", ephemeral=True)
            return

        advantage = self.get_choice(
            self.advantage,
            Advantage.Normal,
            {"a": Advantage.Advantage, "d": Advantage.Disadvantage},
        )
        initiative = Initiative(itr, modifier, name, advantage)
        self.tracker.add(itr, initiative)

        title = f"{itr.user.name} rolled Initiative for {initiative.name}"
        if advantage == Advantage.Advantage:
            title += "with Advantage!"
        elif advantage == Advantage.Disadvantage:
            title += "with Disadvantage!"
        else:
            title += "!"

        descriptions: list[str] = []
        roll_count = 1 if advantage == Advantage.Normal else 2
        for i in range(roll_count):
            d20 = initiative.d20[i]
            mod = initiative.modifier
            total = d20 + mod
            mod_str = f"+ {mod}" if mod > 0 else f"- {-mod}"
            descriptions.append(f"- ``[{d20}] {mod_str}`` -> {total}\n")
        descriptions.append(f"\n**Initiative**: {initiative.get_total()}")
        description = "\n".join(descriptions)

        view = InitiativeContainerView(itr, self.tracker)
        sound_type = SoundType.CREATURE if name else SoundType.PLAYER
        await itr.response.defer()
        await VC.play(itr, sound_type)
        if itr.message:
            await itr.followup.edit_message(message_id=itr.message.id, view=view)
            await itr.followup.send(
                embed=UserActionEmbed(itr=itr, title=title, description=description),
                ephemeral=True,
            )


class InitiativeSetModal(_InitiativeModal):
    value = ui.TextInput["InitiativeSetModal"](label="Initiative value", placeholder="20", max_length=3)
    name = ui.TextInput["InitiativeSetModal"](
        label="Name (Username by default)",
        placeholder="Goblin",
        required=False,
        max_length=128,
    )

    def __init__(self, itr: Interaction, tracker: InitiativeTracker):
        super().__init__(itr, title="Setting your Initiative value", tracker=tracker)

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        value = self.get_int(self.value)
        if not value or value < 0:
            await itr.response.send_message("Value must be a positive number without decimals.", ephemeral=True)
            return

        initiative = Initiative(itr, 0, name, Advantage.Normal, roll=value)
        self.tracker.add(itr, initiative)

        title = f"{itr.user.name} set Initiative for {initiative.name}!"
        description = f"**Initiative**: {initiative.get_total()}"

        view = InitiativeContainerView(itr, self.tracker)
        await VC.play(itr, SoundType.WRITE)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=UserActionEmbed(itr=itr, title=title, description=description),
            ephemeral=True,
        )


class InitiativeDeleteModal(_InitiativeModal):
    name = ui.TextInput["InitiativeDeleteModal"](
        label="Name (Username by default)",
        placeholder="Goblin",
        required=False,
        max_length=128,
    )

    def __init__(self, itr: Interaction, tracker: InitiativeTracker):
        super().__init__(itr, title="Remove an Initiative", tracker=tracker)

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        initiative = self.tracker.remove(itr, name)
        view = InitiativeContainerView(itr, self.tracker)

        await VC.play(itr, SoundType.DELETE)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=SimpleEmbed(title="Removed initiative", description=f"Initiative removed for {initiative.name}!"),
            ephemeral=True,
        )


class InitiativeBulkModal(_InitiativeModal):
    modifier = ui.TextInput["InitiativeBulkModal"](
        label="Creature's Initiative Modifier",
        placeholder="0",
        max_length=3,
        required=False,
    )
    name = ui.TextInput["InitiativeBulkModal"](label="Creature's Name", placeholder="Goblin", max_length=128)
    amount = ui.TextInput["InitiativeBulkModal"](label="Amount of creatures to add", placeholder="1", max_length=2)
    advantage = ui.TextInput["InitiativeBulkModal"](
        label="Roll Mode (Normal by default)",
        placeholder="Advantage / Disadvantage",
        required=False,
        max_length=12,
    )
    shared = ui.TextInput["InitiativeBulkModal"](
        label="Share Initiative (False by default)",
        placeholder="True / False",
        required=False,
        max_length=5,
    )

    def __init__(self, itr: Interaction, tracker: InitiativeTracker):
        super().__init__(itr, title="Adding Initiatives in bulk!", tracker=tracker)

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        name = str(self.name)
        modifier = self.get_int(self.modifier)
        amount = self.get_int(self.amount)

        if modifier is None or amount is None:
            await itr.response.send_message(
                "Modifier and Amount must be a number without a decimals.",
                ephemeral=True,
            )
            return
        if amount <= 0:
            await itr.response.send_message(
                "Amount must be a numerical value larger than 0.",
                ephemeral=True,
            )
            return

        advantage = self.get_choice(
            self.advantage,
            Advantage.Normal,
            {"a": Advantage.Advantage, "d": Advantage.Disadvantage},
        )
        shared = self.get_choice(self.shared, False, {"t": True})
        initiatives = self.tracker.add_bulk(itr, modifier, name, amount, advantage, shared)

        title = f"{itr.user.display_name} rolled Initiative for {amount} {name.strip().title()}(s)!"
        descriptions: list[str] = []
        for initiative in initiatives:
            descriptions.append(f"``{initiative.get_total():>2}`` - {initiative.name}")
        description = "\n".join(descriptions)

        view = InitiativeContainerView(itr, self.tracker)
        await VC.play(itr, SoundType.CREATURE)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=UserActionEmbed(itr=itr, title=title, description=description),
            ephemeral=True,
        )


class InitiativeClearConfirmModal(_InitiativeModal):
    confirm = ui.TextInput["InitiativeClearConfirmModal"](label="Type 'CLEAR' to confirm", placeholder="CLEAR")

    def __init__(self, itr: Interaction, tracker: InitiativeTracker):
        super().__init__(itr, title="Are you sure you want to clear?", tracker=tracker)

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        confirm = str(self.confirm)
        if confirm != "CLEAR":
            await itr.response.send_message(
                embed=SimpleEmbed("Clearing cancelled!", "Type 'CLEAR' in all caps to confirm."),
                ephemeral=True,
            )
            return

        self.tracker.clear(itr)
        view = InitiativeContainerView(itr, self.tracker)
        await VC.play(itr, SoundType.DELETE)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=SimpleEmbed("Cleared all initiatives!", f"Cleared by {itr.user.display_name}."),
            ephemeral=True,
        )


class InitiativePlayerRow(ui.ActionRow["InitiativeContainerView"]):
    def __init__(self, tracker: InitiativeTracker):
        super().__init__()
        self.tracker = tracker

    @ui.button(label="Roll", style=discord.ButtonStyle.success, custom_id="roll_btn", row=0)
    async def roll_initiative(self, itr: Interaction, button: ui.Button["InitiativeContainerView"]):
        await itr.response.send_modal(InitiativeRollModal(itr, self.tracker))

    @ui.button(label="Set", style=discord.ButtonStyle.success, custom_id="set_btn", row=0)
    async def set_initiative(self, itr: Interaction, button: ui.Button["InitiativeContainerView"]):
        await itr.response.send_modal(InitiativeSetModal(itr, self.tracker))

    @ui.button(
        label="Delete Roll",
        style=discord.ButtonStyle.danger,
        custom_id="delete_btn",
        row=0,
    )
    async def remove_initiative(self, itr: Interaction, button: ui.Button["InitiativeContainerView"]):
        await itr.response.send_modal(InitiativeDeleteModal(itr, self.tracker))


class InitiativeDMRow(ui.ActionRow["InitiativeContainerView"]):
    def __init__(self, tracker: InitiativeTracker):
        super().__init__()
        self.tracker = tracker

    @ui.button(label="Bulk", style=discord.ButtonStyle.primary, custom_id="bulk_btn", row=1)
    async def bulk_roll_initiative(self, itr: Interaction, button: ui.Button["InitiativeContainerView"]):
        await itr.response.send_modal(InitiativeBulkModal(itr, self.tracker))

    @ui.button(label="Lock", style=discord.ButtonStyle.primary, custom_id="lock_btn", row=1)
    async def lock(self, itr: Interaction, button: ui.Button["InitiativeContainerView"]):
        log_button_press(itr, button, "InitiativeContainerView")
        await VC.play(itr, SoundType.LOCK)
        await itr.response.edit_message(view=InitiativeContainerView(itr, self.tracker, True))

    @ui.button(
        label="Clear Rolls",
        style=discord.ButtonStyle.danger,
        custom_id="clear_btn",
        row=1,
    )
    async def clear_initiative(self, itr: Interaction, button: ui.Button["InitiativeContainerView"]):
        await itr.response.send_modal(InitiativeClearConfirmModal(itr, self.tracker))


class InitiativeUnlockButton(ui.Button["InitiativeContainerView"]):
    def __init__(self, tracker: InitiativeTracker):
        super().__init__(style=discord.ButtonStyle.primary, label="Unlock", custom_id="unlock_btn")
        self.tracker = tracker

    async def callback(self, itr: Interaction):  # pyright: ignore[reportIncompatibleMethodOverride]
        log_button_press(itr, self, "InitiativeContainerView")
        await VC.play(itr, SoundType.LOCK)
        await itr.response.edit_message(view=InitiativeContainerView(itr, self.tracker, False))


class InitiativeContainerView(ui.LayoutView):
    def __init__(self, itr: Interaction, tracker: InitiativeTracker, locked: bool = False):
        super().__init__(timeout=None)

        container = ui.Container["InitiativeContainerView"](accent_color=discord.Color.dark_green())
        container.add_item(ui.TextDisplay("# Initiatives"))
        container.add_item(SimpleSeparator())

        initiatives = tracker.get(itr)
        descriptions = [f"- ``{i.get_total():>2}`` - {i.name}" for i in initiatives]
        description = "\n".join(descriptions) or "*No initiatives rolled yet!*"

        container.add_item(ui.TextDisplay(description))
        container.add_item(SimpleSeparator())

        if locked:
            unlock_section = ui.Section["InitiativeContainerView"]("‎", accessory=InitiativeUnlockButton(tracker))
            container.add_item(unlock_section)
        else:
            container.add_item(InitiativePlayerRow(tracker))
            container.add_item(InitiativeDMRow(tracker))

        self.add_item(container)
