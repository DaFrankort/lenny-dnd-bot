from dice import DiceExpressionCache
from discord import Button, ButtonStyle, Interaction, SelectOption, ui
from embeds import SuccessEmbed, UserActionEmbed
from modals import SimpleModal


async def update_shortcut_embed(itr: Interaction, view: ui.View | None = None):
    """Updates the ShortcutEmbed, if no view is specified defaults to ShortcutBaseView"""
    embed = ShortcutEmbed(itr)
    if view is None:
        view = embed.view

    await itr.response.edit_message(content=None, embed=embed, view=view)


def get_shortcut_options(shortcuts: object) -> list[SelectOption]:
    options = []
    for key in shortcuts:
        shortcut = shortcuts[key]
        expr = shortcut["expression"]
        reason = shortcut["reason"]
        desc = expr if not reason else f"{expr} ({reason})"
        options.append(SelectOption(label=key, description=desc, value=key))

    return options


class DiceShortcutAddModal(SimpleModal):
    name = ui.TextInput(
        label="Shortcut Name",
        placeholder="ATK",
    )
    notation = ui.TextInput(
        label="Dice expression",
        placeholder="1d20+6",
    )
    reason = ui.TextInput(
        label="Roll Reason (Optional)",
        placeholder="Attack / Damage / Fire / ...",
        required=False,
    )

    def __init__(self, itr: Interaction):
        super().__init__(itr, title="Adding shortcut...")

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        name = self.get_str(self.name)
        notation = self.get_str(self.notation)
        reason = self.get_str(self.reason)

        description, success = DiceExpressionCache.store_shortcut(
            itr, name, notation, reason
        )
        await update_shortcut_embed(itr)

        if success:
            return

        await itr.followup.send(
            embed=SuccessEmbed(
                title_success="",
                title_fail=f"Failed to add {name}...",
                description=description,
                success=success,
            ),
            ephemeral=True,
        )


class DiceShortcutEditModal(SimpleModal):
    name: str
    notation = ui.TextInput(
        label="Dice expression",
    )
    reason = ui.TextInput(
        label="Roll Reason (Optional)",
        required=False,
    )

    def __init__(self, itr: Interaction, name: str, shortcut: object):
        super().__init__(itr, title=f"Editing shortcut: '{name}'")
        self.name = name
        expression = shortcut["expression"]
        reason = shortcut["reason"]

        self.notation.default = expression
        self.notation.placeholder = expression
        self.reason.default = reason
        self.reason.placeholder = reason or "Attack / Damage / Fire / ..."

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        notation = self.get_str(self.notation)
        reason = self.get_str(self.reason)

        description, success = DiceExpressionCache.store_shortcut(
            itr, self.name, notation, reason
        )

        await update_shortcut_embed(itr)

        if success:
            return

        await itr.followup.send(
            embed=SuccessEmbed(
                title_success="",
                title_fail=f"Failed to edit {self.name}...",
                description=description,
                success=success,
            ),
            ephemeral=True,
        )


class ShortcutBaseView(ui.View):
    def __init__(self, shortcuts: object):
        super().__init__()
        self.shortcuts = shortcuts

    @ui.button(label="Add", style=ButtonStyle.success, custom_id='add_btn')
    async def add(self, itr: Interaction, _: Button):
        await itr.response.send_modal(DiceShortcutAddModal(itr))

    @ui.button(label="Edit", style=ButtonStyle.primary, custom_id='edit_btn')
    async def edit(self, itr: Interaction, _: Button):
        await update_shortcut_embed(itr, ShortcutEditView(self.shortcuts))

    @ui.button(label="Remove", style=ButtonStyle.danger, custom_id='remove_btn')
    async def remove(self, itr: Interaction, _: Button):
        await update_shortcut_embed(itr, ShortcutRemoveView(self.shortcuts))


class ShortcutEditSelect(ui.Select):
    def __init__(self, shortcuts: object):
        super().__init__(
            placeholder="Shortcut to edit",
            options=get_shortcut_options(shortcuts),
            min_values=1,
            max_values=1,
        )
        self.shortcuts = shortcuts

    async def callback(self, itr: Interaction):
        name = str(self.values[0])
        shortcut = DiceExpressionCache.get_shortcut(itr, name)

        await itr.response.send_modal(DiceShortcutEditModal(itr, name, shortcut))


class ShortcutEditView(ui.View):
    def __init__(self, shortcuts: object):
        super().__init__()
        self.shortcuts = shortcuts
        self.add_item(ShortcutEditSelect(shortcuts))

    @ui.button(label="Cancel", style=ButtonStyle.secondary, row=1)
    async def cancel(self, itr: Interaction, _: ui.Button):
        await update_shortcut_embed(itr)


class ShortcutRemoveSelect(ui.Select):
    def __init__(self, shortcuts: object):
        super().__init__(
            placeholder="Shortcuts to remove",
            options=get_shortcut_options(shortcuts),
            min_values=1,
            max_values=1,
        )

    async def callback(self, itr: Interaction):
        name = str(self.values[0])
        description, success = DiceExpressionCache.remove_shortcut(itr, name)

        await update_shortcut_embed(itr)

        if success:
            return

        await itr.followup.send(
            embed=SuccessEmbed(
                title_success="",
                title_fail="Failed to remove shortcut...",
                description=description,
                success=success,
            ),
            ephemeral=True,
        )


class ShortcutRemoveView(ui.View):
    def __init__(self, shortcuts: object):
        super().__init__()
        self.add_item(ShortcutRemoveSelect(shortcuts))

    @ui.button(label="Cancel", style=ButtonStyle.secondary, row=1)
    async def cancel(self, itr: Interaction, _: ui.Button):
        await update_shortcut_embed(itr)


class ShortcutEmbed(UserActionEmbed):
    view = ShortcutBaseView | ShortcutEditView | ShortcutRemoveView

    def __init__(self, itr: Interaction):
        shortcuts = DiceExpressionCache.get_user_shortcuts(itr)
        title = f"{itr.user.display_name}'s Shortcuts"
        description = "*You don't have any shortcuts*"

        if shortcuts:
            descriptions = []
            for key in shortcuts:
                shortcut = shortcuts[key]
                expression = shortcut["expression"]
                reason = shortcut["reason"]
                text = f"- **{key}:** {expression}"
                if reason:
                    text += f" ({reason})"
                descriptions.append(text)

            description = "\n".join(descriptions)

        super().__init__(itr, title=title, description=description)

        self.view = ShortcutBaseView(shortcuts)
