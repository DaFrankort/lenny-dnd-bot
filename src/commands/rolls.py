import re
import discord

from dice import DiceExpression, DiceExpressionCache, DiceRollMode
from embeds import UserActionEmbed
from i18n import t
from logger import log_cmd
from voice_chat import VC


def _get_diceroll_shortcut(
    itr: discord.Interaction, diceroll: str, reason: str | None
) -> tuple[str, str | None]:
    shortcuts = DiceExpressionCache.get_user_shortcuts(itr)
    if not shortcuts:
        return diceroll, reason

    parts = re.split(r"([+\-*/()])", diceroll)
    shortcut_reason = None
    for part in parts:
        part = part.strip()

        if part in shortcuts:
            shortcut = shortcuts[part]
            expression = shortcut["expression"]
            reason = shortcut["reason"]
            diceroll = diceroll.replace(part, expression)
            shortcut_reason = reason

    return diceroll, reason or shortcut_reason


async def func_diceroll_autocomplete(
    itr: discord.Interaction, current: str
) -> list[discord.app_commands.Choice[str]]:
    return DiceExpressionCache.get_autocomplete_suggestions(itr, current)


async def func_reason_autocomplete(
    _: discord.Interaction, current: str
) -> list[discord.app_commands.Choice[str]]:
    reasons = [
        "Attack",
        "Damage",
        "Saving Throw",
        "Athletics",
        "Acrobatics",
        "Sleight of Hand",
        "Stealth",
        "Arcana",
        "History",
        "Investigation",
        "Nature",
        "Religion",
        "Animal Handling",
        "Insight",
        "Medicine",
        "Perception",
        "Survival",
        "Deception",
        "Intimidation",
        "Performance",
        "Persuasion",
        "Fire",
    ]
    filtered_reasons = [
        reason for reason in reasons if current.lower() in reason.lower()
    ]
    return [
        discord.app_commands.Choice(name=reason, value=reason)
        for reason in filtered_reasons[:25]
    ]


class RollCommand(discord.app_commands.Command):
    name = t("commands.roll.name")
    description = t("commands.roll.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def diceroll_autocomplete(self, itr: discord.Interaction, current: str):
        return func_diceroll_autocomplete(itr, current)

    async def reason_autocomplete(self, itr: discord.Interaction, current: str):
        return func_reason_autocomplete(itr, current)

    @discord.app_commands.autocomplete(
        diceroll=diceroll_autocomplete,
        reason=reason_autocomplete,
    )
    async def callback(
        self,
        itr: discord.Interaction,
        diceroll: str,
        reason: str = None,
    ):
        log_cmd(itr)
        dice_notation, reason = _get_diceroll_shortcut(itr, diceroll, reason)
        expression = DiceExpression(
            dice_notation, mode=DiceRollMode.Normal, reason=reason
        )
        DiceExpressionCache.store_expression(itr, expression, diceroll)

        await itr.response.send_message(
            embed=UserActionEmbed(
                itr=itr,
                title=expression.title,
                description=expression.description,
            ),
            ephemeral=expression.ephemeral,
        )
        await VC.play_dice_roll(itr, expression, reason)


class AdvantageRollCommand(discord.app_commands.Command):
    name = t("commands.advantage.name")
    description = t("commands.advantage.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def diceroll_autocomplete(self, itr: discord.Interaction, current: str):
        return func_diceroll_autocomplete(itr, current)

    async def reason_autocomplete(self, itr: discord.Interaction, current: str):
        return func_reason_autocomplete(itr, current)

    @discord.app_commands.autocomplete(
        diceroll=diceroll_autocomplete,
        reason=reason_autocomplete,
    )
    async def callback(
        self,
        itr: discord.Interaction,
        diceroll: str,
        reason: str = None,
    ):
        log_cmd(itr)
        dice_notation, reason = _get_diceroll_shortcut(itr, diceroll, reason)
        expression = DiceExpression(
            dice_notation, DiceRollMode.Advantage, reason=reason
        )
        DiceExpressionCache.store_expression(itr, expression, diceroll)

        await itr.response.send_message(
            embed=UserActionEmbed(
                itr=itr,
                title=expression.title,
                description=expression.description,
            ),
            ephemeral=expression.ephemeral,
        )
        await VC.play_dice_roll(itr, expression, reason)


class DisadvantageRollCommand(discord.app_commands.Command):
    name = t("commands.disadvantage.name")
    description = t("commands.disadvantage.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def diceroll_autocomplete(self, itr: discord.Interaction, current: str):
        return func_diceroll_autocomplete(itr, current)

    async def reason_autocomplete(self, itr: discord.Interaction, current: str):
        return func_reason_autocomplete(itr, current)

    @discord.app_commands.autocomplete(
        diceroll=diceroll_autocomplete,
        reason=reason_autocomplete,
    )
    async def callback(
        self,
        itr: discord.Interaction,
        diceroll: str,
        reason: str = None,
    ):
        log_cmd(itr)
        dice_notation, reason = _get_diceroll_shortcut(itr, diceroll, reason)
        expression = DiceExpression(
            dice_notation, DiceRollMode.Disadvantage, reason=reason
        )
        DiceExpressionCache.store_expression(itr, expression, diceroll)

        await itr.response.send_message(
            embed=UserActionEmbed(
                itr=itr,
                title=expression.title,
                description=expression.description,
            ),
            ephemeral=expression.ephemeral,
        )
        await VC.play_dice_roll(itr, expression, reason)


class D20Command(discord.app_commands.Command):
    name = t("commands.d20.name")
    description = t("commands.d20.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction):
        log_cmd(itr)
        expression = DiceExpression("1d20", DiceRollMode.Normal)
        await itr.response.send_message(
            embed=UserActionEmbed(
                itr=itr,
                title=expression.title,
                description=expression.description,
            ),
            ephemeral=expression.ephemeral,
        )
        await VC.play_dice_roll(itr, expression)
