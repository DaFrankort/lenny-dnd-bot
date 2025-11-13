import discord

from embeds.embed import UserActionEmbed
from logic.roll import Advantage, MultiRollResult, RollResult


class RollEmbed(UserActionEmbed):
    def __init__(
        self,
        itr: discord.Interaction,
        result: RollResult,
        reason: str | None,
        reroll: bool = False,
    ):
        title_suffix = ""
        if result.advantage == Advantage.Advantage:
            title_suffix = " with advantage"
        elif result.advantage == Advantage.Disadvantage:
            title_suffix = " with disadvantage"

        if reroll:
            title = f"Re-rolling {result.expression}{title_suffix}!"
        else:
            title = f"Rolling {result.expression}{title_suffix}!"

        if reason is None:
            reason = "Result"

        descriptions: list[str] = []

        if not result.roll.contains_dice:
            descriptions.append("⚠️ Expression contains no dice. ⚠️")

        for roll in result.rolls:
            descriptions.append(f"- `{roll.expression} -> {roll.total}`")

        roll = result.roll
        descriptions.append("")
        descriptions.append(f"🎲 **{reason}: {roll.total}**")

        if roll.is_natural_twenty:
            descriptions.append("🎯 **Critical Hit!**")
        if roll.is_natural_one:
            descriptions.append("💀 **Critical Fail!**")
        if roll.is_dirty_twenty:
            descriptions.append("⚔️  **Dirty 20!**")

        description = "\n".join(descriptions)
        if len(description) > 1024:
            description = "⚠️ Message too long, try sending a shorter expression!"

        super().__init__(itr, title, description)


class MultiRollEmbed(UserActionEmbed):
    def __init__(
        self,
        itr: discord.Interaction,
        result: MultiRollResult,
        reason: str | None,
        reroll: bool = False,
    ):
        if reroll:
            title = f"Re-rolling {result.expression} multiple times!"
        else:
            title = f"Rolling {result.expression} multiple times!"

        if reason is None:
            reason = "Total"

        descriptions: list[str] = []
        if not result.rolls[0].contains_dice:
            descriptions.append("⚠️ Expression contains no dice. ⚠️")

        for roll in result.rolls:
            roll_message = f"- `{roll.expression} -> {roll.total}`"
            if roll.is_natural_twenty:
                roll_message += " 🎯"
            elif roll.is_natural_one:
                roll_message += " 💀"
            elif roll.is_dirty_twenty:
                roll_message += " ⚔️"
            descriptions.append(roll_message)

        descriptions.append("")
        descriptions.append(f"🎲 **{reason}: {result.total}**")

        description = "\n".join(descriptions)
        if len(descriptions) > 1024:
            description = "⚠️ Message too long, try sending a shorter expression!"

        super().__init__(itr, title, description)
