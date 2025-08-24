import re
import discord

from logic.app_commands import SimpleCommand
from dice import DiceExpression, DiceExpressionCache, DiceRollMode
from embeds import UserActionEmbed
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
    itr: discord.Interaction, current: str
) -> list[discord.app_commands.Choice[str]]:
    return DiceExpressionCache.get_autocomplete_reason_suggestions(itr, current)


class RollCommand(SimpleCommand):
    name = "roll"
    desc = "Roll your d20s!"
    help = "Roll a single dice expression."

    async def diceroll_autocomplete(self, itr: discord.Interaction, current: str):
        return await func_diceroll_autocomplete(itr, current)

    async def reason_autocomplete(self, itr: discord.Interaction, current: str):
        return await func_reason_autocomplete(itr, current)

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
        self.log(itr)
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


class AdvantageRollCommand(SimpleCommand):
    name = "advantage"
    desc = "Lucky you! Roll and take the best of two!"
    help = "Roll the expression twice, use the highest result."

    async def diceroll_autocomplete(self, itr: discord.Interaction, current: str):
        return await func_diceroll_autocomplete(itr, current)

    async def reason_autocomplete(self, itr: discord.Interaction, current: str):
        return await func_reason_autocomplete(itr, current)

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
        self.log(itr)
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


class DisadvantageRollCommand(SimpleCommand):
    name = "disadvantage"
    desc = "Tough luck chump... Roll twice and suck it."
    help = "Roll the expression twice, use the lowest result."

    async def diceroll_autocomplete(self, itr: discord.Interaction, current: str):
        return await func_diceroll_autocomplete(itr, current)

    async def reason_autocomplete(self, itr: discord.Interaction, current: str):
        return await func_reason_autocomplete(itr, current)

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
        self.log(itr)
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


class D20Command(SimpleCommand):
    name = "d20"
    desc = "Just roll a clean d20!"
    help = "Rolls a basic 1d20 with no modifiers."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
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
