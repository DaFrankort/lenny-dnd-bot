import discord

from embeds.roll import RollEmbed
from logic.app_commands import SimpleCommand
from dice import DiceExpressionCache
from logic.roll import Advantage, roll
from voice_chat import VC


class _AbstractRollCommand(SimpleCommand):
    advantage: Advantage

    async def diceroll_autocomplete(self, itr: discord.Interaction, current: str):
        return await DiceExpressionCache.get_autocomplete_suggestions(itr, current)

    async def reason_autocomplete(self, itr: discord.Interaction, current: str):
        return await DiceExpressionCache.get_autocomplete_reason_suggestions(
            itr, current
        )

    @discord.app_commands.autocomplete(
        diceroll=diceroll_autocomplete,
        reason=reason_autocomplete,
    )
    async def callback(
        self,
        itr: discord.Interaction,
        diceroll: str,
        reason: str | None = None,
    ):
        self.log(itr)
        result = roll(diceroll, self.advantage)
        if result.error is not None:
            DiceExpressionCache.store_expression(itr, result.expression, reason)

        embed = RollEmbed(itr, result, reason)
        await itr.response.send_message(embed=embed, ephemeral=embed.ephemeral)
        await VC.play_dice_roll(itr, result, reason)


class RollCommand(_AbstractRollCommand):
    name = "roll"
    desc = "Roll your d20s!"
    help = "Roll a single dice expression."
    advantage = Advantage.Normal


class AdvantageRollCommand(_AbstractRollCommand):
    name = "advantage"
    desc = "Lucky you! Roll and take the best of two!"
    help = "Roll the expression twice, use the highest result."
    advantage = Advantage.Advantage


class DisadvantageRollCommand(_AbstractRollCommand):
    name = "disadvantage"
    desc = "Tough luck chump... Roll twice and suck it."
    help = "Roll the expression twice, use the lowest result."
    advantage = Advantage.Disadvantage


class D20Command(SimpleCommand):
    name = "d20"
    desc = "Just roll a clean d20!"
    help = "Rolls a basic 1d20 with no modifiers."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        result = roll("1d20", Advantage.Normal)
        embed = RollEmbed(itr, result)
        await itr.response.send_message(embed=embed, ephemeral=embed.ephemeral)
        await VC.play_dice_roll(itr, result)
