import abc
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


class DetailedRollCommand(discord.app_commands.Command, abc.ABC):
    """Utility class for specific dice commands that accept an expression and a reason."""

    @discord.app_commands.autocomplete("diceroll")
    async def autocomplete_diceroll(
        itr: discord.Interaction, current: str
    ) -> list[discord.app_commands.Choice[str]]:
        return DiceExpressionCache.get_autocomplete_suggestions(itr, current)

    async def autocomplete_roll_reason(
        itr: discord.Interaction, current: str
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


class RollCommand(DetailedRollCommand):
    name = t("commands.roll.name")
    description = t("commands.roll.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def callback(
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


class AdvantageRollCommand(DetailedRollCommand):
    name = t("commands.advantage.name")
    description = t("commands.advantage.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def callback(itr: discord.Interaction, diceroll: str, reason: str = None):
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


class DisadvantageRollCommand(DetailedRollCommand):
    name = t("commands.disadvantage.name")
    description = t("commands.disadvantage.desc")

    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            callback=self.callback,
        )

    async def callback(itr: discord.Interaction, diceroll: str, reason: str = None):
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

    async def callback(itr: discord.Interaction):
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
