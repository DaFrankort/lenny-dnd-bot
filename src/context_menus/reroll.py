import discord

from logic.dicecache import DiceCache
from embeds.roll import MultiRollEmbed, RollEmbed
from commands.command import SimpleContextMenu
from logic.roll import Advantage, multi_roll, roll
from logic.voice_chat import VC, SoundType


class RerollContextMenu(SimpleContextMenu):
    name = "Re-roll"
    help = "Will repeat a roll done with the __/roll__, __/advantage__, or __/disadvantage__ commands."

    def __init__(self):
        super().__init__()

    def _get_reason(self, embed: discord.Embed):
        reason = None
        field = embed.fields[0].value or ""
        if "Result" not in field:
            lines = field.strip().splitlines()
            for line in lines:
                if line.startswith("🎲") and ":" in line:
                    label = line[1:].split(":", 1)[0].strip()  # Remove 🎲 and split before colon
                    reason = label.replace("*", "")
                    break
        return reason

    async def _handle_multiroll(self, interaction: discord.Interaction, dice_notation: str, embed: discord.Embed):
        dice_notation = dice_notation.replace("multiple times", "").strip()
        reason = self._get_reason(embed)

        if not embed.fields[0].value:
            raise ValueError("Could not find any roll-related info in this message!")

        amount = 0
        for line in embed.fields[0].value.split("\n"):
            if "- `" in line:
                amount += 1

        result = multi_roll(dice_notation, amount)
        embed = MultiRollEmbed(interaction, result, reason, reroll=True)
        DiceCache.store_expression(interaction, dice_notation)

        await interaction.response.send_message(embed=embed)
        await VC.play(interaction, SoundType.ROLL)

    async def _handle_single_roll(self, interaction: discord.Interaction, dice_notation: str, embed: discord.Embed):
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

        reason = self._get_reason(embed)
        result = roll(dice_notation, advantage)
        embed = RollEmbed(interaction, result, reason, reroll=True)
        DiceCache.store_expression(interaction, dice_notation)

        await interaction.response.send_message(embed=embed)
        await VC.play_dice_roll(interaction, result, reason)

    async def callback(self, interaction: discord.Interaction, message: discord.Message):
        self.log(interaction)

        if interaction.client.user is None:
            error = "The bot is not associated with a user account!"
            await interaction.response.send_message(f"❌ {error} ❌", ephemeral=True)
            return

        if message.author.id != interaction.client.user.id:
            error = f"Only works on dice-roll messages sent by {interaction.client.user.name}"
            await interaction.response.send_message(f"❌ {error} ❌", ephemeral=True)
            return

        if not message.embeds or len(message.embeds) == 0:
            await interaction.response.send_message("❌ Reroll doesn't work on this message type!", ephemeral=True)
            return

        embed = message.embeds[0]
        title = embed.author.name or ""
        if not ("Rolling" in title or "Re-rolling" in title):
            await interaction.response.send_message("❌ Message does not contain a dice-roll!", ephemeral=True)
            return

        dice_notation = title.replace("Rolling ", "").replace("Re-rolling", "").replace("!", "")
        if "multiple times" in dice_notation:
            await self._handle_multiroll(interaction, dice_notation, embed)
            return
        await self._handle_single_roll(interaction, dice_notation, embed)
