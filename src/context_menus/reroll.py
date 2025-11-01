import discord

from dice import DiceCache
from embeds.roll import RollEmbed
from command import SimpleContextMenu
from logic.roll import Advantage, roll
from logic.voice_chat import VC


class RerollContextMenu(SimpleContextMenu):
    name = "Re-roll"

    def __init__(self):
        super().__init__()

    async def callback(self, itr: discord.Interaction, message: discord.Message):  # pyright: ignore
        self.log(itr)

        if itr.client.user is None:
            error = "The bot is not associated with a user account!"
            await itr.response.send_message(f"❌ {error} ❌", ephemeral=True)
            return

        if message.author.id != itr.client.user.id:
            error = f"Only works on dice-roll messages sent by {itr.client.user.name}"
            await itr.response.send_message(f"❌ {error} ❌", ephemeral=True)
            return

        if not message.embeds or len(message.embeds) == 0:
            await itr.response.send_message("❌ Reroll doesn't work on this message type!", ephemeral=True)
            return

        embed = message.embeds[0]
        title = embed.author.name or ""
        if not ("Rolling" in title or "Re-rolling" in title):
            await itr.response.send_message("❌ Message does not contain a dice-roll!", ephemeral=True)
            return

        dice_notation = title.replace("Rolling ", "").replace("Re-rolling", "").replace("!", "")
        if "disadvantage" in dice_notation:
            # Check 'disadvantage' before 'advantage', may give a false positive otherwise.
            advantage = Advantage.Disadvantage
            dice_notation = dice_notation.replace("with disadvantage", "")
        elif "advantage" in dice_notation:
            advantage = Advantage.Advantage
            dice_notation = dice_notation.replace("with advantage", "")
        else:
            advantage = Advantage.Normal
        dice_notation = dice_notation.strip()

        reason = None
        field = embed.fields[0].value or ""
        if "Result" not in field:
            lines = field.strip().splitlines()
            for line in lines:
                if line.startswith("🎲") and ":" in line:
                    label = line[1:].split(":", 1)[0].strip()  # Remove 🎲 and split before colon
                    reason = label.replace("*", "")
                    break

        result = roll(dice_notation, advantage)
        embed = RollEmbed(itr, result, reason, reroll=True)
        DiceCache.store_expression(itr, dice_notation)

        await itr.response.send_message(embed=embed)
        await VC.play_dice_roll(itr, result, reason)
