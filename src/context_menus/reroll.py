import discord

from dice import DiceExpression, DiceExpressionCache, DiceRollMode
from embeds import UserActionEmbed
from i18n import t
from logger import log_cmd
from voice_chat import VC


class RerollContextMenu(discord.app_commands.ContextMenu):
    name = "Re-roll"

    def __init__(self):
        super().__init__(
            name=self.name,
            callback=self.callback,
        )

    async def callback(self, itr: discord.Interaction, message: discord.Message):
        log_cmd(itr)
        if message.author.id != itr.client.user.id:
            await itr.response.send_message(
                f"❌ Only works on dice-roll messages sent by {itr.client.user.name} ❌",
                ephemeral=True,
            )
            return

        if not message.embeds or len(message.embeds) == 0:
            await itr.response.send_message(
                "❌ Reroll doesn't work on this message type!", ephemeral=True
            )
            return

        embed = message.embeds[0]
        title = embed.author.name or ""
        if not ("Rolling" in title or "Re-rolling" in title):
            await itr.response.send_message(
                "❌ Message does not contain a dice-roll!", ephemeral=True
            )
            return

        dice_notation = (
            title.replace("Rolling ", "").replace("Re-rolling", "").replace("!", "")
        )
        if "disadvantage" in dice_notation:
            # Check 'disadvantage' before 'advantage', may give a false positive otherwise.
            mode = DiceRollMode.Disadvantage
            dice_notation = dice_notation.replace("with disadvantage", "")
        elif "advantage" in dice_notation:
            mode = DiceRollMode.Advantage
            dice_notation = dice_notation.replace("with advantage", "")
        else:
            mode = DiceRollMode.Normal
        dice_notation = dice_notation.strip()

        reason = None
        if "Result" not in embed.fields[0].value:
            lines = embed.fields[0].value.strip().splitlines()
            for line in lines:
                if line.startswith("🎲") and ":" in line:
                    label = (
                        line[1:].split(":", 1)[0].strip()
                    )  # Remove 🎲 and split before colon
                    reason = label.replace("*", "")
                    break

        expression = DiceExpression(expression=dice_notation, mode=mode, reason=reason)
        expression.title = expression.title.replace("Rolling", "Re-rolling")
        DiceExpressionCache.store_expression(itr, expression, dice_notation)

        await itr.response.send_message(
            embed=UserActionEmbed(
                itr=itr,
                title=expression.title,
                description=expression.description,
            ),
            ephemeral=expression.ephemeral,
        )
        await VC.play_dice_roll(itr, expression, reason)
