import discord
from embed import UserActionEmbed
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

        description = []

        if not result.roll.contains_dice:
            description.append("⚠️ Expression contains no dice. ⚠️")

        for roll in result.rolls:
            description.append(f"- `{roll.expression} -> {roll.total}`")

        roll = result.roll
        description.append("")
        description.append(f"🎲 **{reason}: {roll.total}**")

        if roll.is_natural_twenty:
            description.append("🎯 **Critical Hit!**")
        if roll.is_natural_one:
            description.append("💀 **Critical Fail!**")
        if roll.is_dirty_twenty:
            description.append("⚔️  **Dirty 20!**")

        description = "\n".join(description)
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

        description = []
        if not result.rolls[0].contains_dice:
            description.append("⚠️ Expression contains no dice. ⚠️")

        for roll in result.rolls:
            roll_message = f"- `{roll.expression} -> {roll.total}`"
            if roll.is_natural_twenty:
                roll_message += " 🎯"
            elif roll.is_natural_one:
                roll_message += " 💀"
            elif roll.is_dirty_twenty:
                roll_message += " ⚔️"
            description.append(roll_message)

        description.append("")
        description.append(f"🎲 **{reason}: {result.total}**")

        description = "\n".join(description)
        if len(description) > 1024:
            description = "⚠️ Message too long, try sending a shorter expression!"

        super().__init__(itr, title, description)
