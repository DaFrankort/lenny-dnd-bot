import discord
from discord import Interaction, ui
from components.items import SimpleSeparator
from embed import SimpleEmbed, SuccessEmbed, UserActionEmbed
from initiative import Initiative, InitiativeTracker
from logic.roll import DiceRollMode
from modals import SimpleModal
from logic.voice_chat import VC, SoundType
from logger import log_button_press


class _InitiativeModal(SimpleModal):
    def __init__(self, itr: Interaction, title: str, tracker: InitiativeTracker):
        super().__init__(itr, title)
        self.tracker = tracker


class InitiativeRollModal(_InitiativeModal):
    modifier = ui.TextInput(
        label="Your Initiative Modifier", placeholder="0", max_length=2, required=False
    )
    name = ui.TextInput(
        label="Name (Username by default)",
        placeholder="Goblin",
        required=False,
        max_length=128,
    )
    mode = ui.TextInput(
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
            await itr.response.send_message(
                "Initiative Modifier must be a number without decimals.", ephemeral=True
            )
            return

        mode = self.get_choice(
            self.mode,
            DiceRollMode.Normal,
            {"a": DiceRollMode.Advantage, "d": DiceRollMode.Disadvantage},
        )
        initiative = Initiative(itr, modifier, name, mode)
        success = self.tracker.add(itr, initiative)

        if not success:
            await itr.response.send_message(
                embed=SuccessEmbed(
                    title_success="",
                    title_fail="Failed to add initiative!",
                    description=f"Can't add more initiatives to the tracker, max limit of {self.tracker.INITIATIVE_LIMIT} reached.",
                    success=False,
                ),
                ephemeral=True,
            )
            return

        view = InitiativeContainerView(itr, self.tracker)
        sound_type = SoundType.CREATURE if name else SoundType.PLAYER
        await VC.play(itr, sound_type)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=UserActionEmbed(
                itr=itr, title=initiative.title, description=initiative.description
            ),
            ephemeral=True,
        )


class InitiativeSetModal(_InitiativeModal):
    value = ui.TextInput(label="Initiative value", placeholder="20", max_length=3)
    name = ui.TextInput(
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
            await itr.response.send_message(
                "Value must be a positive number without decimals.", ephemeral=True
            )
            return

        initiative = Initiative(itr, value, name, DiceRollMode.Normal)
        initiative.set_value(value)
        self.tracker.add(itr, initiative)

        view = InitiativeContainerView(itr, self.tracker)
        await VC.play(itr, SoundType.WRITE)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=UserActionEmbed(
                itr=itr, title=initiative.title, description=initiative.description
            ),
            ephemeral=True,
        )


class InitiativeDeleteModal(_InitiativeModal):
    name = ui.TextInput(
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
        success, text = self.tracker.remove(itr, name)
        view = InitiativeContainerView(itr, self.tracker)

        if success:
            await VC.play(itr, SoundType.DELETE)

        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=SuccessEmbed(
                title_success="Removed initiative",
                title_fail="Failed to remove initiative",
                description=text,
                success=success,
            ),
            ephemeral=True,
        )


class InitiativeBulkModal(_InitiativeModal):
    modifier = ui.TextInput(
        label="Creature's Initiative Modifier",
        placeholder="0",
        max_length=3,
        required=False,
    )
    name = ui.TextInput(label="Creature's Name", placeholder="Goblin", max_length=128)
    amount = ui.TextInput(
        label="Amount of creatures to add", placeholder="1", max_length=2
    )
    mode = ui.TextInput(
        label="Roll Mode (Normal by default)",
        placeholder="Advantage / Disadvantage",
        required=False,
        max_length=12,
    )
    shared = ui.TextInput(
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

        mode = self.get_choice(
            self.mode,
            DiceRollMode.Normal,
            {"a": DiceRollMode.Advantage, "d": DiceRollMode.Disadvantage},
        )
        shared = self.get_choice(self.shared, False, {"t": True})

        title, description, success = self.tracker.add_bulk(
            itr, modifier, name, amount, mode, shared
        )

        if not success:
            await itr.response.send_message(
                embed=SuccessEmbed(
                    title_success="",
                    title_fail=title,
                    description=description,
                    success=False,
                ),
                ephemeral=True,
            )
            return

        view = InitiativeContainerView(itr, self.tracker)
        await VC.play(itr, SoundType.CREATURE)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=UserActionEmbed(itr=itr, title=title, description=description),
            ephemeral=True,
        )


class InitiativeClearConfirmModal(_InitiativeModal):
    confirm = ui.TextInput(label="Type 'CLEAR' to confirm", placeholder="CLEAR")

    def __init__(self, itr: Interaction, tracker: InitiativeTracker):
        super().__init__(itr, title="Are you sure you want to clear?", tracker=tracker)

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        confirm = str(self.confirm)
        if confirm != "CLEAR":
            await itr.response.send_message(
                embed=SimpleEmbed(
                    "Clearing cancelled!", "Type 'CLEAR' in all caps to confirm."
                ),
                ephemeral=True,
            )
            return

        self.tracker.clear(itr)
        view = InitiativeContainerView(itr, self.tracker)
        await VC.play(itr, SoundType.DELETE)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=SimpleEmbed(
                "Cleared all initiatives!", f"Cleared by {itr.user.display_name}."
            ),
            ephemeral=True,
        )


class InitiativePlayerRow(ui.ActionRow):
    def __init__(self, tracker: InitiativeTracker):
        super().__init__()
        self.tracker = tracker

    @ui.button(
        label="Roll", style=discord.ButtonStyle.success, custom_id="roll_btn", row=0
    )
    async def roll_initiative(self, itr: Interaction, button: ui.Button):
        await itr.response.send_modal(InitiativeRollModal(itr, self.tracker))

    @ui.button(
        label="Set", style=discord.ButtonStyle.success, custom_id="set_btn", row=0
    )
    async def set_initiative(self, itr: Interaction, button: ui.Button):
        await itr.response.send_modal(InitiativeSetModal(itr, self.tracker))

    @ui.button(
        label="Delete Roll",
        style=discord.ButtonStyle.danger,
        custom_id="delete_btn",
        row=0,
    )
    async def remove_initiative(self, itr: Interaction, button: ui.Button):
        await itr.response.send_modal(InitiativeDeleteModal(itr, self.tracker))


class InitiativeDMRow(ui.ActionRow):
    def __init__(self, tracker: InitiativeTracker):
        super().__init__()
        self.tracker = tracker

    @ui.button(
        label="Bulk", style=discord.ButtonStyle.primary, custom_id="bulk_btn", row=1
    )
    async def bulk_roll_initiative(self, itr: Interaction, button: ui.Button):
        await itr.response.send_modal(InitiativeBulkModal(itr, self.tracker))

    @ui.button(
        label="Lock", style=discord.ButtonStyle.primary, custom_id="lock_btn", row=1
    )
    async def lock(self, itr: Interaction, button: ui.Button):
        log_button_press(itr, button, "InitiativeContainerView")
        await VC.play(itr, SoundType.LOCK)
        await itr.response.edit_message(
            view=InitiativeContainerView(itr, self.tracker, True)
        )

    @ui.button(
        label="Clear Rolls",
        style=discord.ButtonStyle.danger,
        custom_id="clear_btn",
        row=1,
    )
    async def clear_initiative(self, itr: Interaction, button: ui.Button):
        await itr.response.send_modal(InitiativeClearConfirmModal(itr, self.tracker))


class InitiativeUnlockButton(ui.Button):
    def __init__(self, tracker: InitiativeTracker):
        super().__init__(
            style=discord.ButtonStyle.primary, label="Unlock", custom_id="unlock_btn"
        )
        self.tracker = tracker

    async def callback(self, itr: Interaction):
        log_button_press(itr, self, "InitiativeContainerView")
        await VC.play(itr, SoundType.LOCK)
        await itr.response.edit_message(
            view=InitiativeContainerView(itr, self.tracker, False)
        )


class InitiativeContainerView(ui.LayoutView):
    def __init__(
        self, itr: Interaction, tracker: InitiativeTracker, locked: bool = False
    ):
        super().__init__(timeout=None)

        container = ui.Container(accent_color=discord.Color.dark_green())
        container.add_item(ui.TextDisplay("# Initiatives"))
        container.add_item(SimpleSeparator())

        initiatives = tracker.get(itr)
        descriptions = [f"- ``{i.get_total():>2}`` - {i.name}" for i in initiatives]
        description = "\n".join(descriptions) or "*No initiatives rolled yet!*"

        container.add_item(ui.TextDisplay(description))
        container.add_item(SimpleSeparator())

        if locked:
            unlock_section = ui.Section("‎", accessory=InitiativeUnlockButton(tracker))
            container.add_item(unlock_section)
        else:
            container.add_item(InitiativePlayerRow(tracker))
            container.add_item(InitiativeDMRow(tracker))

        self.add_item(container)
