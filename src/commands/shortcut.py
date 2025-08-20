import discord

from dice import DiceExpressionCache
from embeds import SuccessEmbed, UserActionEmbed
from logger import log_cmd
from modals import SimpleModal


async def update_shortcut_embed(
    itr: discord.Interaction,
    view: discord.ui.View | None = None,
):
    """Updates the ShortcutEmbed, if no view is specified defaults to ShortcutBaseView"""
    embed = ShortcutEmbed(itr)
    if view is None:
        view = embed.view

    await itr.response.edit_message(content=None, embed=embed, view=view)


def get_shortcut_options(shortcuts: object) -> list[discord.SelectOption]:
    options = []
    for key in shortcuts:
        shortcut = shortcuts[key]
        expr = shortcut["expression"]
        reason = shortcut["reason"]
        desc = expr if not reason else f"{expr} ({reason})"
        options.append(discord.SelectOption(label=key, description=desc, value=key))

    return options


class DiceShortcutAddModal(SimpleModal):
    name = discord.ui.TextInput(
        label="Shortcut Name",
        placeholder="ATK",
    )
    notation = discord.ui.TextInput(
        label="Dice expression",
        placeholder="1d20+6",
    )
    reason = discord.ui.TextInput(
        label="Roll Reason (Optional)",
        placeholder="Attack / Damage / Fire / ...",
        required=False,
    )

    def __init__(self, itr: discord.Interaction):
        super().__init__(itr, title="Adding shortcut...")

    async def on_submit(self, itr: discord.Interaction):
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
    notation = discord.ui.TextInput(
        label="Dice expression",
    )
    reason = discord.ui.TextInput(
        label="Roll Reason (Optional)",
        required=False,
    )

    def __init__(self, itr: discord.Interaction, name: str, shortcut: object):
        super().__init__(itr, title=f"Editing shortcut: '{name}'")
        self.name = name
        expression = shortcut["expression"]
        reason = shortcut["reason"]

        self.notation.default = expression
        self.notation.placeholder = expression
        self.reason.default = reason
        self.reason.placeholder = reason or "Attack / Damage / Fire / ..."

    async def on_submit(self, itr: discord.Interaction):
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


class ShortcutBaseView(discord.ui.View):
    def __init__(self, shortcuts: object):
        super().__init__()
        self.shortcuts = shortcuts

        has_shortcuts = bool(shortcuts)
        if has_shortcuts:
            return

        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id in ("edit_btn", "remove_btn"):
                    child.disabled = True
                    child.style = discord.ButtonStyle.secondary

    @discord.ui.button(
        label="Add", style=discord.ButtonStyle.success, custom_id="add_btn"
    )
    async def add(self, itr: discord.Interaction, _: discord.Button):
        await itr.response.send_modal(DiceShortcutAddModal(itr))

    @discord.ui.button(
        label="Edit", style=discord.ButtonStyle.primary, custom_id="edit_btn"
    )
    async def edit(self, itr: discord.Interaction, _: discord.Button):
        await update_shortcut_embed(itr, ShortcutEditView(self.shortcuts))

    @discord.ui.button(
        label="Remove", style=discord.ButtonStyle.danger, custom_id="remove_btn"
    )
    async def remove(self, itr: discord.Interaction, _: discord.Button):
        await update_shortcut_embed(itr, ShortcutRemoveView(self.shortcuts))


class ShortcutEditSelect(discord.ui.Select):
    def __init__(self, shortcuts: object):
        super().__init__(
            placeholder="Shortcut to edit",
            options=get_shortcut_options(shortcuts),
            min_values=1,
            max_values=1,
        )
        self.shortcuts = shortcuts

    async def callback(self, itr: discord.Interaction):
        name = str(self.values[0])
        shortcut = DiceExpressionCache.get_shortcut(itr, name)

        await itr.response.send_modal(DiceShortcutEditModal(itr, name, shortcut))


class ShortcutEditView(discord.ui.View):
    def __init__(self, shortcuts: object):
        super().__init__()
        self.shortcuts = shortcuts
        self.add_item(ShortcutEditSelect(shortcuts))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=1)
    async def cancel(self, itr: discord.Interaction, _: discord.ui.Button):
        await update_shortcut_embed(itr)


class ShortcutRemoveSelect(discord.ui.Select):
    def __init__(self, shortcuts: object):
        super().__init__(
            placeholder="Shortcuts to remove",
            options=get_shortcut_options(shortcuts),
            min_values=1,
            max_values=1,
        )

    async def callback(self, itr: discord.Interaction):
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


class ShortcutRemoveView(discord.ui.View):
    def __init__(self, shortcuts: object):
        super().__init__()
        self.add_item(ShortcutRemoveSelect(shortcuts))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=1)
    async def cancel(self, itr: discord.Interaction, _: discord.ui.Button):
        await update_shortcut_embed(itr)


class ShortcutEmbed(UserActionEmbed):
    view = ShortcutBaseView | ShortcutEditView | ShortcutRemoveView

    def __init__(self, itr: discord.Interaction):
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


class ShortcutCommand(discord.app_commands.Command):
    name = "shortcut"
    desc = "Create & edit roll shortcuts, ideal for people who can't read character sheets!"
    help = "Create, edit and remove roll-shortcuts, which can be referred to in dice-roll commands."
    command = "/shortcut"

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.desc,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction):
        log_cmd(itr)
        embed = ShortcutEmbed(itr)
        await itr.response.send_message(embed=embed, view=embed.view, ephemeral=True)
