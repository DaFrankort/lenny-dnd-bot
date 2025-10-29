import discord
from embed import UserActionEmbed
from logic.roll import Advantage, RollResult


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
