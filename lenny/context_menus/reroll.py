import discord

from commands.command import BaseContextMenu
from embeds.roll import MultiRollEmbed, RollEmbed
from logic.dicecache import DiceCache
from logic.roll import Advantage, multi_roll, roll
from logic.voice_chat import VC, SoundType


class RerollContextMenu(BaseContextMenu):
    name = "Re-roll"
    help = "Will repeat a roll done with the __/roll__ or __/multiroll__ commands."

    @staticmethod
    def _get_reason(embed: discord.Embed):
        reason = None
        field = embed.fields[-1].value or ""
        if "Result" not in field:
            lines = field.strip().splitlines()
            for line in lines:
                if line.startswith("🎲") and ":" in line:
                    label = line[1:].split(":", 1)[0].strip()  # Remove 🎲 and split before colon
                    reason = label.replace("*", "")
                    break
        return reason

    @staticmethod
    def _parse_advantage(dice_notation: str) -> Advantage:
        if "disadvantage" in dice_notation:
            # Check 'disadvantage' before 'advantage', may give a false positive otherwise.
            return Advantage.DISADVANTAGE
        if "advantage" in dice_notation:
            return Advantage.ADVANTAGE
        if "elven accuracy" in dice_notation:
            return Advantage.ELVEN_ACCURACY
        return Advantage.NORMAL

    async def _handle_multiroll(self, interaction: discord.Interaction, dice_notation: str, embed: discord.Embed):
        advantage = self._parse_advantage(dice_notation)
        dice_notation = dice_notation.replace(advantage.title_suffix.strip(), "")
        dice_notation = dice_notation.replace("multiple times", "").strip()
        reason = self._get_reason(embed)

        if not embed.fields[0].value:
            raise ValueError("Could not find any roll-related info in this message!")

        amount = 0
        for line in embed.fields[0].value.split("\n"):
            if "`" in line:
                amount += 1

        result = multi_roll(dice_notation, amount, advantage)
        embed = MultiRollEmbed(interaction, result, reason, reroll=True)
        DiceCache.get(interaction).store_expression(dice_notation)

        await interaction.response.send_message(embed=embed)
        await VC.play(interaction, SoundType.ROLL)

    async def _handle_single_roll(self, interaction: discord.Interaction, dice_notation: str, embed: discord.Embed):
        advantage = self._parse_advantage(dice_notation)
        dice_notation = dice_notation.replace(advantage.title_suffix.strip(), "")
        dice_notation = dice_notation.strip()

        reason = self._get_reason(embed)
        result = roll(dice_notation, advantage)
        embed = RollEmbed(interaction, result, reason, reroll=True)
        DiceCache.get(interaction).store_expression(dice_notation)

        await interaction.response.send_message(embed=embed)
        await VC.play_dice_roll(interaction, result, reason)

    async def handle(self, interaction: discord.Interaction, message: discord.Message):
        self.log(interaction)

        if interaction.client.user is None:
            raise ValueError("The bot is not associated with a user account!")

        if message.author.id != interaction.client.user.id:
            raise PermissionError(f"Only works on dice-roll messages sent by {interaction.client.user.name}")

        if not message.embeds or len(message.embeds) == 0:
            raise ValueError("Reroll doesn't work on this message type!")

        embed = message.embeds[0]
        title = embed.author.name or ""
        if not ("Rolling" in title or "Re-rolling" in title):
            raise ValueError("Message does not contain a dice-roll!")

        dice_notation = title.replace("Rolling ", "").replace("Re-rolling", "").replace("!", "")
        if "multiple times" in dice_notation:
            await self._handle_multiroll(interaction, dice_notation, embed)
            return
        await self._handle_single_roll(interaction, dice_notation, embed)
