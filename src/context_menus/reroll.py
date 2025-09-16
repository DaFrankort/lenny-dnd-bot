import discord

from dice import DiceCache
from embeds.roll import RollEmbed
from logic.app_commands import SimpleContextMenu
from logic.roll import DiceRollMode, roll
from voice_chat import VC


class RerollContextMenu(SimpleContextMenu):
    name = "Re-roll"

    def __init__(self):
        super().__init__()

    async def callback(self, itr: discord.Interaction, message: discord.Message):
        self.log(itr)
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

        result = roll(dice_notation, mode)
        embed = RollEmbed(itr, result, reason, reroll=True)
        DiceCache.store_expression(itr, dice_notation)

        await itr.response.send_message(embed=embed)
        await VC.play_dice_roll(itr, result, reason)
